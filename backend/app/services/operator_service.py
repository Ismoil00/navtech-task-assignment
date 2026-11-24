import uuid
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BusinessValidationError, NotFoundError
from app.domain.enums import AllowedAction, ApplicationStatus
from app.domain.status_machine import OPERATOR_VISIBLE_STATUSES
from app.models import Application, Attachment
from app.repositories.application_repository import ApplicationRepository
from app.repositories.attachment_repository import AttachmentRepository
from app.services import allowed_actions
from app.services.pagination import PageResult, page_offset
from app.storage import FileStorage


class OperatorService:
    """Кабинет оператора: очередь отправленных заявок, карточка, документ.

    Оператор видит заявку, только если её хотя бы раз отправили на рассмотрение:
    черновики и оплаченные, но не отправленные заявки для него не существуют (404).
    """

    def __init__(self, session: AsyncSession, storage: FileStorage) -> None:
        self._session = session
        self._storage = storage
        self._applications = ApplicationRepository(session)
        self._attachments = AttachmentRepository(session)

    async def list_queue(
        self,
        *,
        status: ApplicationStatus | None,
        service_type_id: int | None,
        page: int,
        page_size: int,
    ) -> PageResult:
        if status is not None and status not in OPERATOR_VISIBLE_STATUSES:
            raise BusinessValidationError(
                "Оператору доступны только отправленные заявки",
                details=[{"field": "status", "message": "Недопустимый статус для фильтра"}],
            )
        statuses = {status} if status is not None else OPERATOR_VISIBLE_STATUSES
        items, total = await self._applications.list_with_status_in(
            statuses,
            service_type_id=service_type_id,
            offset=page_offset(page, page_size),
            limit=page_size,
        )
        return PageResult(items=items, total=total, page=page, page_size=page_size)

    async def get(self, application_id: uuid.UUID) -> tuple[Application, list[AllowedAction]]:
        await self._get_visible(application_id)
        application = await self._applications.get_details(application_id)
        if application is None:
            raise NotFoundError("Заявка не найдена", code="APPLICATION_NOT_FOUND")
        return application, allowed_actions.for_operator(application)

    async def download(self, application_id: uuid.UUID) -> tuple[Attachment, AsyncIterator[bytes]]:
        await self._get_visible(application_id)
        attachment = await self._attachments.get_by_application(application_id)
        if attachment is None or not await self._storage.exists(attachment.storage_key):
            raise NotFoundError("Документ не приложен", code="ATTACHMENT_NOT_FOUND")
        return attachment, self._storage.read(attachment.storage_key)

    async def _get_visible(
        self, application_id: uuid.UUID, *, for_update: bool = False
    ) -> Application:
        application = await self._applications.get_with_status_in(
            application_id, OPERATOR_VISIBLE_STATUSES, for_update=for_update
        )
        if application is None:
            raise NotFoundError("Заявка не найдена", code="APPLICATION_NOT_FOUND")
        return application
