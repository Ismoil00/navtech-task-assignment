import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from app.core.config import get_settings
from app.core.errors import UnauthorizedError
from app.domain.enums import UserRole


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


@dataclass(frozen=True)
class AccessToken:
    token: str
    expires_in: int  # секунды


@dataclass(frozen=True)
class AccessTokenPayload:
    user_id: uuid.UUID
    role: UserRole


def create_access_token(user_id: uuid.UUID, role: UserRole) -> AccessToken:
    settings = get_settings()
    now = datetime.now(UTC)
    ttl = timedelta(minutes=settings.access_token_ttl_minutes)
    payload = {
        "sub": str(user_id),
        "role": role.value,
        "type": "access",
        "iat": now,
        "exp": now + ttl,
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return AccessToken(token=token, expires_in=int(ttl.total_seconds()))


def decode_access_token(token: str) -> AccessTokenPayload:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp", "sub", "type"]},
        )
    except jwt.ExpiredSignatureError as exc:
        # отдельный код: фронтенд по нему понимает, что пора обновить токен
        raise UnauthorizedError("Срок действия сессии истёк", code="TOKEN_EXPIRED") from exc
    except jwt.InvalidTokenError as exc:
        raise UnauthorizedError("Недействительный токен", code="INVALID_TOKEN") from exc

    if payload.get("type") != "access":
        raise UnauthorizedError("Недействительный токен", code="INVALID_TOKEN")
    try:
        return AccessTokenPayload(user_id=uuid.UUID(payload["sub"]), role=UserRole(payload["role"]))
    except (KeyError, ValueError) as exc:
        raise UnauthorizedError("Недействительный токен", code="INVALID_TOKEN") from exc
