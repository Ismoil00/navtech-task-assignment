import uuid

from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import PaymentStatus
from app.models import Payment


class PaymentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def has_succeeded(self, application_id: uuid.UUID) -> bool:
        query = select(
            exists().where(
                Payment.application_id == application_id,
                Payment.status == PaymentStatus.SUCCEEDED,
            )
        )
        return bool(await self._session.scalar(query))
