"""Фикстуры интеграционных тестов: база, пользователи, управляемый шлюз, HTTP-клиент."""

import asyncio
import inspect
import subprocess
import sys
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from pathlib import Path

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.core.db import SessionFactory, engine
from app.core.security import create_access_token
from app.domain.enums import UserRole
from app.integrations.payment_gateway import ChargeResult, PaymentGatewayError, get_payment_gateway
from app.main import create_app
from app.models import User
from app.storage import LocalFileStorage, get_file_storage
from tests.integration.api import Actor, Api

BACKEND_DIR = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session", autouse=True)
async def database() -> AsyncIterator[None]:
    """Чистая тестовая база на каждый прогон, схема — теми же миграциями Alembic."""
    settings = get_settings()
    name = settings.postgres_db
    assert name.endswith("_test"), f"Тесты пересоздают базу {name!r} — нужна отдельная *_test"

    admin_url = settings.database_url.rsplit("/", 1)[0] + "/postgres"
    admin = create_async_engine(admin_url, isolation_level="AUTOCOMMIT", poolclass=NullPool)
    async with admin.connect() as connection:
        await connection.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
        await connection.execute(text(f'CREATE DATABASE "{name}"'))
    await admin.dispose()

    # Alembic сам запускает цикл событий, поэтому — отдельным процессом
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=BACKEND_DIR,
        check=True,
        capture_output=True,
    )
    yield
    await engine.dispose()


@pytest.fixture(autouse=True)
async def clean_tables() -> None:
    # справочник услуг (из миграции) остаётся, всё остальное очищается перед тестом
    async with engine.begin() as connection:
        await connection.execute(
            text(
                "TRUNCATE users, applications, attachments, payments, "
                "application_status_history, refresh_tokens RESTART IDENTITY CASCADE"
            )
        )


class FakeGateway:
    """Управляемый шлюз: считает списания, умеет отказывать и «зависать»."""

    def __init__(self) -> None:
        self.charges: list[uuid.UUID] = []
        self.refunds: list[uuid.UUID] = []
        self.fail_with: str | None = None
        self._release: asyncio.Event | None = None

    def hold(self) -> asyncio.Event:
        """Следующие списания будут ждать, пока тест не вызовет .set()."""
        self._release = asyncio.Event()
        return self._release

    async def charge(self, payment_id: uuid.UUID, amount: int, currency: str) -> ChargeResult:
        self.charges.append(payment_id)
        if self._release is not None:
            await self._release.wait()
        if self.fail_with:
            raise PaymentGatewayError(self.fail_with)
        return ChargeResult(provider_ref=f"test-{payment_id.hex[:8]}")

    async def refund(self, payment_id: uuid.UUID, provider_ref: str) -> None:
        self.refunds.append(payment_id)


@pytest.fixture
def gateway() -> FakeGateway:
    return FakeGateway()


@pytest.fixture
async def client(gateway: FakeGateway, tmp_path: Path) -> AsyncIterator[httpx.AsyncClient]:
    app = create_app()
    app.dependency_overrides[get_payment_gateway] = lambda: gateway
    app.dependency_overrides[get_file_storage] = lambda: LocalFileStorage(str(tmp_path))
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client


@pytest.fixture
def api(client: httpx.AsyncClient) -> Api:
    return Api(client)


async def _create_user(username: str, role: UserRole, full_name: str) -> Actor:
    async with SessionFactory() as session:
        user = User(username=username, full_name=full_name, role=role, password_hash="not-used")
        session.add(user)
        await session.commit()
    token = create_access_token(user.id, user.role).token
    return Actor(user=user, headers={"Authorization": f"Bearer {token}"})


@pytest.fixture
async def applicant() -> Actor:
    return await _create_user("applicant1", UserRole.APPLICANT, "Каримов Фаррух Шарифович")


@pytest.fixture
async def other_applicant() -> Actor:
    return await _create_user("applicant2", UserRole.APPLICANT, "Назарова Мадина Рустамовна")


@pytest.fixture
async def operator() -> Actor:
    return await _create_user("operator1", UserRole.OPERATOR, "Сафаров Далер Олимович")


async def wait_until(condition: Callable[[], bool | Awaitable[bool]], timeout: float = 5.0) -> None:
    """Ждёт, пока условие станет истинным (условие может быть обычным или async)."""
    async with asyncio.timeout(timeout):
        while True:
            result = condition()
            if inspect.isawaitable(result):
                result = await result
            if result:
                return
            await asyncio.sleep(0.02)
