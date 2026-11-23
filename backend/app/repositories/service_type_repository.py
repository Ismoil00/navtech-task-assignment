from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ServiceType


class ServiceTypeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_active(self) -> Sequence[ServiceType]:
        result = await self._session.scalars(
            select(ServiceType)
            .where(ServiceType.is_active.is_(True))
            .order_by(ServiceType.sort_order, ServiceType.id)
        )
        return result.all()

    async def get_active(self, service_type_id: int) -> ServiceType | None:
        return await self._session.scalar(
            select(ServiceType).where(
                ServiceType.id == service_type_id, ServiceType.is_active.is_(True)
            )
        )
