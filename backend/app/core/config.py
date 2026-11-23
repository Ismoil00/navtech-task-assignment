from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

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


@lru_cache
def get_settings() -> Settings:
    return Settings()
