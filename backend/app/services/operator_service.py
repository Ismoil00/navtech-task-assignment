import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError, BusinessValidationError, NotFoundError
from app.domain.enums import AllowedAction, ApplicationAction, ApplicationStatus, PaymentStatus
from app.domain.status_machine import OPERATOR_VISIBLE_STATUSES
from app.integrations.payment_gateway import PaymentGateway, PaymentGatewayError
from app.models import Application, Attachment, User
from app.repositories.application_repository import ApplicationRepository
from app.repositories.attachment_repository import AttachmentRepository
from app.repositories.payment_repository import PaymentRepository
from app.services import allowed_actions
from app.services.application_workflow import ApplicationWorkflow
from app.services.pagination import PageResult, page_offset
from app.storage import FileStorage


class RefundFailedError(AppError):
    status_code = 502
    code = "REFUND_FAILED"
    message = "Не удалось вернуть оплату заявителю. Решение не сохранено, попробуйте ещё раз"


class OperatorService:
    """Кабинет оператора: очередь отправленных заявок, карточка, документ, решение.

    Оператор видит заявку, только если её хотя бы раз отправили на рассмотрение:
    черновики и оплаченные, но не отправленные заявки для него не существуют (404).
    """

    def __init__(
        self, session: AsyncSession, storage: FileStorage, gateway: PaymentGateway
    ) -> None:
        self._session = session
        self._storage = storage
        self._gateway = gateway
        self._applications = ApplicationRepository(session)
        self._attachments = AttachmentRepository(session)
        self._payments = PaymentRepository(session)
        self._workflow = ApplicationWorkflow(session)

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
        return await self._details(application_id)

    async def download(self, application_id: uuid.UUID) -> tuple[Attachment, AsyncIterator[bytes]]:
        await self._get_visible(application_id)
        attachment = await self._attachments.get_by_application(application_id)
        if attachment is None or not await self._storage.exists(attachment.storage_key):
            raise NotFoundError("Документ не приложен", code="ATTACHMENT_NOT_FOUND")
        return attachment, self._storage.read(attachment.storage_key)

    async def decide(
        self,
        operator: User,
        application_id: uuid.UUID,
        action: ApplicationAction,
        comment: str | None,
    ) -> tuple[Application, list[AllowedAction]]:
        """Одобрить, отклонить или вернуть на доработку.

        Строка заявки заблокирована: если два оператора решают одновременно,
        второй увидит уже изменённый статус и получит 409.
        """
        application = await self._get_visible(application_id, for_update=True)
        await self._workflow.apply(application, action, operator, comment)
        if action == ApplicationAction.REJECT:
            # услуга не оказана — деньги возвращаются в той же транзакции, что и решение
            await self._refund(application)
        await self._session.commit()
        return await self._details(application_id)

    async def _refund(self, application: Application) -> None:
        payment = await self._payments.get_succeeded(application.id)
        if payment is None:
            return
        try:
            await self._gateway.refund(payment.id, payment.provider_ref or "")
        except PaymentGatewayError as exc:
            # commit не случится: решение откатится вместе с попыткой возврата
            raise RefundFailedError() from exc
        payment.status = PaymentStatus.REFUNDED
        payment.refunded_at = datetime.now(UTC)

    async def _get_visible(
        self, application_id: uuid.UUID, *, for_update: bool = False
    ) -> Application:
        application = await self._applications.get_with_status_in(
            application_id, OPERATOR_VISIBLE_STATUSES, for_update=for_update
        )
        if application is None:
            raise NotFoundError("Заявка не найдена", code="APPLICATION_NOT_FOUND")
        return application

    async def _details(self, application_id: uuid.UUID) -> tuple[Application, list[AllowedAction]]:
        application = await self._applications.get_details(application_id)
        if application is None:
            raise NotFoundError("Заявка не найдена", code="APPLICATION_NOT_FOUND")
        return application, allowed_actions.for_operator(application)
