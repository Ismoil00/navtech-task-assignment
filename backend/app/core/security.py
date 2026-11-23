import hashlib
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from functools import cache

import bcrypt
import jwt

from app.core.config import get_settings
from app.core.errors import UnauthorizedError
from app.domain.enums import UserRole

# bcrypt учитывает только первые 72 байта пароля, а bcrypt>=5 на более длинном падает
_BCRYPT_MAX_BYTES = 72


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    encoded = password.encode()
    if len(encoded) > _BCRYPT_MAX_BYTES:
        return False
    return bcrypt.checkpw(encoded, password_hash.encode())


@cache
def dummy_password_hash() -> str:
    """Хеш-заглушка для входа под несуществующим логином.

    Пароль проверяется всегда, поэтому по времени ответа нельзя понять,
    существует ли такой пользователь.
    """
    return hash_password(secrets.token_urlsafe(16))


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


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
