"""Создаёт демо-пользователей для проверки задания.

Запуск: python -m scripts.seed
Повторный запуск безопасен: существующие пользователи не изменяются.
"""

import asyncio
import sys

from app.core.config import get_settings
from app.core.db import SessionFactory, engine
from app.core.security import hash_password
from app.domain.enums import UserRole
from app.models import User
from app.repositories.user_repository import UserRepository


def demo_users() -> list[tuple[str, str, UserRole, str]]:
    settings = get_settings()
    if not settings.seed_applicant_password or not settings.seed_operator_password:
        sys.exit("Задайте SEED_APPLICANT_PASSWORD и SEED_OPERATOR_PASSWORD в .env")

    return [
        (
            "applicant1",
            "Каримов Фаррух Шарифович",
            UserRole.APPLICANT,
            settings.seed_applicant_password,
        ),
        (
            "applicant2",
            "Назарова Мадина Рустамовна",
            UserRole.APPLICANT,
            settings.seed_applicant_password,
        ),
        ("operator1", "Сафаров Далер Олимович", UserRole.OPERATOR, settings.seed_operator_password),
    ]


async def seed() -> None:
    users = demo_users()
    async with SessionFactory() as session:
        repository = UserRepository(session)
        for username, full_name, role, password in users:
            if await repository.get_by_username(username):
                print(f"Пользователь {username} уже существует, пропускаю")
                continue
            repository.add(
                User(
                    username=username,
                    full_name=full_name,
                    role=role,
                    password_hash=hash_password(password),
                )
            )
            print(f"Создан пользователь {username} ({role.value})")
        await session.commit()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
