from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import ForbiddenError, UnauthorizedError
from app.core.security import (
    AccessToken,
    create_access_token,
    decode_access_token,
    dummy_password_hash,
    generate_refresh_token,
    hash_refresh_token,
    verify_password,
)
from app.domain.enums import UserRole
from app.models import RefreshToken, User
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository

# Если старый refresh-токен пришёл в течение этого окна после ротации, это почти
# наверняка параллельный запрос из соседней вкладки, а не кража — сессию не рвём.
ROTATION_GRACE_PERIOD = timedelta(seconds=30)

_PORTAL_NAMES = {UserRole.APPLICANT: "заявителя", UserRole.OPERATOR: "оператора"}


@dataclass(frozen=True)
class AuthSession:
    user: User
    access_token: AccessToken
    refresh_token: str
    refresh_expires_at: datetime


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._users = UserRepository(session)
        self._tokens = RefreshTokenRepository(session)

    async def login(self, username: str, password: str, portal: UserRole) -> AuthSession:
        user = await self._users.get_by_username(username)
        password_ok = verify_password(
            password, user.password_hash if user else dummy_password_hash()
        )
        if user is None or not password_ok or not user.is_active:
            raise UnauthorizedError("Неверный логин или пароль", code="INVALID_CREDENTIALS")

        # Роль берётся из БД; выбор кабинета на странице входа её не меняет
        if user.role != portal:
            raise ForbiddenError(
                f"У этой учётной записи нет доступа к кабинету {_PORTAL_NAMES[portal]}",
                code="WRONG_PORTAL",
            )

        auth, _ = await self._start_session(user)
        await self._session.commit()
        return auth

    async def refresh(self, raw_token: str | None) -> AuthSession:
        if not raw_token:
            raise UnauthorizedError("Сессия не найдена, войдите снова", code="NO_REFRESH_TOKEN")

        now = datetime.now(UTC)
        token = await self._tokens.get_by_hash_for_update(hash_refresh_token(raw_token))
        if token is None or token.expires_at <= now:
            raise UnauthorizedError("Сессия истекла, войдите снова", code="INVALID_REFRESH_TOKEN")

        if token.revoked_at is not None:
            if token.replaced_by_id is not None and now - token.revoked_at < ROTATION_GRACE_PERIOD:
                raise UnauthorizedError("Сессия уже обновлена", code="REFRESH_TOKEN_ROTATED")
            # Повторное использование отозванного токена — признак утечки:
            # закрываем все сессии пользователя.
            await self._tokens.revoke_all_for_user(token.user_id, now)
            await self._session.commit()
            raise UnauthorizedError(
                "Сессия недействительна, войдите снова", code="REFRESH_TOKEN_REUSED"
            )

        user = await self._users.get_by_id(token.user_id)
        if user is None or not user.is_active:
            raise UnauthorizedError("Сессия недействительна, войдите снова")

        auth, new_token = await self._start_session(user)
        token.revoked_at = now
        token.replaced_by_id = new_token.id
        await self._session.commit()
        return auth

    async def authenticate(self, access_token: str) -> User:
        """Пользователь по access-токену.

        Пользователь каждый раз читается из БД: заблокированный пользователь
        теряет доступ сразу, не дожидаясь истечения токена.
        """
        payload = decode_access_token(access_token)
        user = await self._users.get_by_id(payload.user_id)
        if user is None or not user.is_active:
            raise UnauthorizedError("Пользователь не найден или заблокирован", code="INVALID_TOKEN")
        return user

    async def logout(self, raw_token: str | None) -> None:
        if not raw_token:
            return
        token = await self._tokens.get_by_hash_for_update(hash_refresh_token(raw_token))
        if token is not None and token.revoked_at is None:
            token.revoked_at = datetime.now(UTC)
            await self._session.commit()

    async def _start_session(self, user: User) -> tuple[AuthSession, RefreshToken]:
        raw_token = generate_refresh_token()
        expires_at = datetime.now(UTC) + timedelta(days=get_settings().refresh_token_ttl_days)
        token = RefreshToken(
            user_id=user.id, token_hash=hash_refresh_token(raw_token), expires_at=expires_at
        )
        self._tokens.add(token)
        await self._session.flush()  # нужен id нового токена для связи при ротации

        auth = AuthSession(
            user=user,
            access_token=create_access_token(user.id, user.role),
            refresh_token=raw_token,
            refresh_expires_at=expires_at,
        )
        return auth, token
