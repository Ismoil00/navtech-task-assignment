from functools import lru_cache
from pathlib import Path

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
