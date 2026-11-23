from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ServiceType
from app.repositories.service_type_repository import ServiceTypeRepository


class ServiceTypeService:
    def __init__(self, session: AsyncSession) -> None:
        self._service_types = ServiceTypeRepository(session)

    async def list_active(self) -> Sequence[ServiceType]:
        return await self._service_types.list_active()
