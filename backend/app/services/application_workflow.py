from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError
from app.domain.enums import ApplicationAction, ApplicationStatus, UserRole
from app.domain.status_machine import Transition, ensure_role_allowed, get_transition
from app.models import Application, ApplicationStatusHistory, User
from app.repositories.attachment_repository import AttachmentRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.status_history_repository import StatusHistoryRepository


class PaymentInProgressError(ConflictError):
    code = "PAYMENT_IN_PROGRESS"
    message = "Идёт оплата — дождитесь результата"


# Статусы до отправки (или повторной отправки), в которых действуют требования ТЗ:
# без файла не оплатить и не отправить, без оплаты не отправить.
_BEFORE_SUBMISSION = frozenset(
    {ApplicationStatus.DRAFT, ApplicationStatus.PAID, ApplicationStatus.RETURNED}
)


class ApplicationWorkflow:
    """Единственное место, где меняется статус заявки.

    apply() проверяет переход по машине состояний, условия по данным из БД
    и пишет запись в историю. Вызывающий код заранее блокирует строку заявки
    (SELECT ... FOR UPDATE) и сам делает commit — так смена статуса и запись
    в истории попадают в одну транзакцию.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._attachments = AttachmentRepository(session)
        self._payments = PaymentRepository(session)
        self._history = StatusHistoryRepository(session)

    async def apply(
        self,
        application: Application,
        action: ApplicationAction,
        actor: User,
        comment: str | None = None,
    ) -> Transition:
        ensure_role_allowed(action, actor.role)
        await self.check_requirements(application, action)
        transition = get_transition(application.status, action, actor.role, comment)

        previous_status = application.status
        now = datetime.now(UTC)
        application.status = transition.target
        if action == ApplicationAction.SUBMIT:
            application.submitted_at = now
            application.decided_at = None
        elif transition.role == UserRole.OPERATOR:
            application.decided_at = now

        self._history.add(
            ApplicationStatusHistory(
                application_id=application.id,
                from_status=previous_status,
                to_status=transition.target,
                actor_id=actor.id,
                comment=comment.strip() if comment and comment.strip() else None,
            )
        )
        return transition

    async def ensure_no_payment_in_progress(self, application: Application) -> None:
        """Пока шлюз обрабатывает оплату, заявку нельзя менять: сумма зависит от услуги."""
        if await self._payments.has_processing(application.id):
            raise PaymentInProgressError()

    async def check_requirements(self, application: Application, action: ApplicationAction) -> None:
        """Условия ТЗ с понятной причиной отказа вместо общего «недопустимый переход»."""
        if application.status not in _BEFORE_SUBMISSION:
            return
        needs_file = action in (ApplicationAction.PAY, ApplicationAction.SUBMIT)
        if needs_file and await self._attachments.get_by_application(application.id) is None:
            raise ConflictError("Сначала прикрепите документ", code="FILE_REQUIRED")
        needs_payment = action == ApplicationAction.SUBMIT
        if needs_payment and not await self._payments.has_succeeded(application.id):
            raise ConflictError("Сначала оплатите заявку", code="PAYMENT_REQUIRED")
