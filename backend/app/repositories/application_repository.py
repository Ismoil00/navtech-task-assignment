import uuid
from collections.abc import Sequence

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.enums import ApplicationStatus
from app.models import Application, ApplicationStatusHistory


class ApplicationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, application: Application) -> None:
        self._session.add(application)

    async def get_own(
        self, application_id: uuid.UUID, applicant_id: uuid.UUID, *, for_update: bool = False
    ) -> Application | None:
        """Заявка заявителя. Чужая или удалённая заявка просто не находится.

        Владелец проверяется в самом запросе, поэтому подобрать чужой id бесполезно.
        """
        query = select(Application).where(
            Application.id == application_id,
            Application.applicant_id == applicant_id,
            Application.deleted_at.is_(None),
        )
        if for_update:
            # блокировка строки: параллельные изменения одной заявки идут по очереди
            query = query.with_for_update()
        return await self._session.scalar(query)

    async def get_details(self, application_id: uuid.UUID) -> Application | None:
        """Заявка со всеми связями для карточки (услуга, файл, платежи, история)."""
        query = (
            select(Application)
            .where(Application.id == application_id)
            .options(
                selectinload(Application.service_type),
                selectinload(Application.attachment),
                selectinload(Application.payments),
                selectinload(Application.history).selectinload(ApplicationStatusHistory.actor),
            )
            # перечитать объект, даже если он уже есть в сессии (после изменений)
            .execution_options(populate_existing=True)
        )
        return await self._session.scalar(query)

    async def list_own(
        self,
        applicant_id: uuid.UUID,
        *,
        status: ApplicationStatus | None,
        offset: int,
        limit: int,
    ) -> tuple[Sequence[Application], int]:
        conditions = [Application.applicant_id == applicant_id, Application.deleted_at.is_(None)]
        if status is not None:
            conditions.append(Application.status == status)

        query = select(Application).where(*conditions)
        items = await self._page(query.order_by(Application.created_at.desc()), offset, limit)
        total = await self._session.scalar(
            select(func.count()).select_from(Application).where(*conditions)
        )
        return items, total or 0

    async def _page(
        self, query: Select[tuple[Application]], offset: int, limit: int
    ) -> Sequence[Application]:
        result = await self._session.scalars(
            query.options(selectinload(Application.service_type)).offset(offset).limit(limit)
        )
        return result.all()
