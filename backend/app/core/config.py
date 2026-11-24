from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL

# Корень репозитория: backend/app/core/config.py -> ../../../
ROOT_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Настройки приложения.

    В Docker значения приходят из переменных окружения (compose читает
    .env.example, затем .env). При запуске без Docker те же файлы читаются
    напрямую из корня репозитория. Переменные окружения всегда приоритетнее.
    """

    model_config = SettingsConfigDict(
        env_file=(ROOT_DIR / ".env.example", ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Сервис подачи заявок"
    app_env: str = "local"
    api_prefix: str = "/api"

    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 7
    refresh_cookie_name: str = "refresh_token"
    # true в продакшене за HTTPS; локально по http cookie с Secure браузер не сохранит
    refresh_cookie_secure: bool = False

    # Регион для номеров без кода страны: "93 123 4567" -> +992931234567
    phone_default_region: str = "TJ"

    # Каталог для загруженных документов. В Docker это именованный том.
    upload_dir: str = "uploads"

    # Заглушка платёжного шлюза: flaky — с задержками и ошибками (по умолчанию),
    # stable — без сбоев, включается только в сквозном тесте (docker-compose.e2e.yml)
    payment_gateway: Literal["flaky", "stable"] = "flaky"
    # доли исходов: 30% отказов, 30% ответов с задержкой, остальные 40% — быстрый успех
    payment_failure_rate: float = Field(0.3, ge=0, le=1)
    payment_delay_rate: float = Field(0.3, ge=0, le=1)
    # длительность задержки, секунды (случайно в этом диапазоне)
    payment_delay_min_seconds: float = 5.0
    payment_delay_max_seconds: float = 12.0
    # дольше этого backend шлюз не ждёт и считает попытку неудачной
    payment_gateway_timeout_seconds: float = 15.0

    # Адреса фронтенда через запятую, которым разрешено обращаться к API из браузера
    cors_origins: str

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def database_url(self) -> str:
        # URL.create сам экранирует спецсимволы в пароле
        return URL.create(
            drivername="postgresql+asyncpg",
            username=self.postgres_user,
            password=self.postgres_password,
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        ).render_as_string(hide_password=False)


@lru_cache
def get_settings() -> Settings:
    return Settings()
