import uuid

from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import PaymentStatus
from app.models import Payment

# «Живой» платёж: деньги списываются, списаны или уже возвращены.
# Таких у заявки не больше одного — это же гарантирует частичный уникальный индекс.
ACTIVE_PAYMENT_STATUSES = (
    PaymentStatus.PROCESSING,
    PaymentStatus.SUCCEEDED,
    PaymentStatus.REFUNDED,
)


class PaymentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, payment: Payment) -> None:
        self._session.add(payment)

    async def get(self, payment_id: uuid.UUID) -> Payment | None:
        # populate_existing: платёж мог измениться в другой сессии (завершение оплаты)
        return await self._session.get(Payment, payment_id, populate_existing=True)

    async def get_by_key(self, application_id: uuid.UUID, idempotency_key: str) -> Payment | None:
        return await self._session.scalar(
            select(Payment).where(
                Payment.application_id == application_id,
                Payment.idempotency_key == idempotency_key,
            )
        )

    async def get_active(self, application_id: uuid.UUID) -> Payment | None:
        return await self._session.scalar(
            select(Payment).where(
                Payment.application_id == application_id,
                Payment.status.in_(ACTIVE_PAYMENT_STATUSES),
            )
        )

    async def get_succeeded(self, application_id: uuid.UUID) -> Payment | None:
        return await self._session.scalar(
            select(Payment).where(
                Payment.application_id == application_id,
                Payment.status == PaymentStatus.SUCCEEDED,
            )
        )

    async def has_succeeded(self, application_id: uuid.UUID) -> bool:
        return await self._exists(application_id, PaymentStatus.SUCCEEDED)

    async def has_processing(self, application_id: uuid.UUID) -> bool:
        return await self._exists(application_id, PaymentStatus.PROCESSING)

    async def _exists(self, application_id: uuid.UUID, status: PaymentStatus) -> bool:
        query = select(
            exists().where(Payment.application_id == application_id, Payment.status == status)
        )
        return bool(await self._session.scalar(query))
