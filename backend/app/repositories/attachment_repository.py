import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Attachment


class AttachmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_application(self, application_id: uuid.UUID) -> Attachment | None:
        return await self._session.scalar(
            select(Attachment).where(Attachment.application_id == application_id)
        )

    def add(self, attachment: Attachment) -> None:
        self._session.add(attachment)
