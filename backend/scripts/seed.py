"""Создаёт демо-пользователей для проверки задания.

Запуск: python -m scripts.seed
Повторный запуск безопасен: существующие пользователи не изменяются.
Пользователей любой роли может быть сколько угодно — достаточно добавить строку в DEMO_USERS.
Логины и пароли перечислены в README.
"""

import asyncio
from dataclasses import dataclass

from app.core.db import SessionFactory, engine
from app.core.security import hash_password
from app.domain.enums import UserRole
from app.models import User
from app.repositories.user_repository import UserRepository


@dataclass(frozen=True)
class DemoUser:
    username: str
    password: str
    full_name: str
    role: UserRole


DEMO_USERS = [
    DemoUser("applicant1", "applicant1pass", "Каримов Фаррух Шарифович", UserRole.APPLICANT),
    DemoUser("applicant2", "applicant2pass", "Назарова Мадина Рустамовна", UserRole.APPLICANT),
    DemoUser("applicant3", "applicant3pass", "Рахимов Шахзод Бахтиёрович", UserRole.APPLICANT),
    DemoUser("operator1", "operator1pass", "Сафаров Далер Олимович", UserRole.OPERATOR),
    DemoUser("operator2", "operator2pass", "Юсупова Нилуфар Камоловна", UserRole.OPERATOR),
]


async def seed() -> None:
    async with SessionFactory() as session:
        repository = UserRepository(session)
        for demo in DEMO_USERS:
            if await repository.get_by_username(demo.username):
                print(f"Пользователь {demo.username} уже существует, пропускаю")
                continue
            repository.add(
                User(
                    username=demo.username,
                    full_name=demo.full_name,
                    role=demo.role,
                    password_hash=hash_password(demo.password),
                )
            )
            print(f"Создан пользователь {demo.username} ({demo.role.value})")
        await session.commit()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
