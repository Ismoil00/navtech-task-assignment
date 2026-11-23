from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.errors import ForbiddenError, UnauthorizedError
from app.domain.enums import UserRole
from app.models import User
from app.services.auth_service import AuthService

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_auth_service(session: SessionDep) -> AuthService:
    return AuthService(session)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]

# auto_error=False: отсутствие токена отдаём в нашем формате ошибок, а не стандартным 403
_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    service: AuthServiceDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User:
    if credentials is None:
        raise UnauthorizedError("Требуется авторизация", code="NOT_AUTHENTICATED")
    return await service.authenticate(credentials.credentials)


CurrentUserDep = Annotated[User, Depends(get_current_user)]


def require_role(role: UserRole) -> Callable[[User], Awaitable[User]]:
    async def dependency(user: CurrentUserDep) -> User:
        if user.role != role:
            raise ForbiddenError()
        return user

    return dependency


# Один экземпляр на роль: FastAPI кеширует зависимость в рамках запроса по самой функции
require_applicant = require_role(UserRole.APPLICANT)
require_operator = require_role(UserRole.OPERATOR)

ApplicantDep = Annotated[User, Depends(require_applicant)]
OperatorDep = Annotated[User, Depends(require_operator)]
