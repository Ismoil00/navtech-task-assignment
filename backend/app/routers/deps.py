from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.db import get_session, get_session_factory
from app.core.errors import ForbiddenError, UnauthorizedError
from app.domain.enums import UserRole
from app.integrations.payment_gateway import PaymentGateway, get_payment_gateway
from app.models import User
from app.services.application_service import ApplicationService
from app.services.attachment_service import AttachmentService
from app.services.auth_service import AuthService
from app.services.operator_service import OperatorService
from app.services.payment_service import PaymentService
from app.services.service_type_service import ServiceTypeService
from app.storage import FileStorage, get_file_storage

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_auth_service(session: SessionDep) -> AuthService:
    return AuthService(session)


def get_service_type_service(session: SessionDep) -> ServiceTypeService:
    return ServiceTypeService(session)


def get_application_service(session: SessionDep) -> ApplicationService:
    return ApplicationService(session)


def get_attachment_service(
    session: SessionDep, storage: Annotated[FileStorage, Depends(get_file_storage)]
) -> AttachmentService:
    return AttachmentService(session, storage)


def get_payment_service(
    session: SessionDep,
    session_factory: Annotated[async_sessionmaker[AsyncSession], Depends(get_session_factory)],
    gateway: Annotated[PaymentGateway, Depends(get_payment_gateway)],
) -> PaymentService:
    return PaymentService(session, session_factory, gateway)


def get_operator_service(
    session: SessionDep, storage: Annotated[FileStorage, Depends(get_file_storage)]
) -> OperatorService:
    return OperatorService(session, storage)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
ServiceTypeServiceDep = Annotated[ServiceTypeService, Depends(get_service_type_service)]
ApplicationServiceDep = Annotated[ApplicationService, Depends(get_application_service)]
AttachmentServiceDep = Annotated[AttachmentService, Depends(get_attachment_service)]
PaymentServiceDep = Annotated[PaymentService, Depends(get_payment_service)]
OperatorServiceDep = Annotated[OperatorService, Depends(get_operator_service)]

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
