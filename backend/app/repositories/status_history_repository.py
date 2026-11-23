from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ApplicationStatusHistory


class StatusHistoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, entry: ApplicationStatusHistory) -> None:
        self._session.add(entry)
