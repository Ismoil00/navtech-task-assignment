import uuid
from collections.abc import AsyncIterable, AsyncIterator
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, NotFoundError
from app.domain.documents import DocumentValidator, safe_filename
from app.domain.enums import AllowedAction
from app.domain.status_machine import EDITABLE_STATUSES, STATUS_LABELS
from app.models import Application, Attachment, User
from app.repositories.application_repository import ApplicationRepository
from app.repositories.attachment_repository import AttachmentRepository
from app.services import allowed_actions
from app.storage import FileStorage


class AttachmentService:
    """Документ заявки: загрузка с проверкой и скачивание с проверкой доступа."""

    def __init__(self, session: AsyncSession, storage: FileStorage) -> None:
        self._session = session
        self._storage = storage
        self._applications = ApplicationRepository(session)
        self._attachments = AttachmentRepository(session)

    async def upload(
        self,
        applicant: User,
        application_id: uuid.UUID,
        *,
        filename: str | None,
        chunks: AsyncIterable[bytes],
    ) -> tuple[Application, list[AllowedAction]]:
        application = await self._applications.get_own(
            application_id, applicant.id, for_update=True
        )
        if application is None:
            raise NotFoundError("Заявка не найдена", code="APPLICATION_NOT_FOUND")
        if application.status not in EDITABLE_STATUSES:
            raise ConflictError(
                f"В статусе «{STATUS_LABELS[application.status]}» документ заменить нельзя",
                code="APPLICATION_NOT_EDITABLE",
            )

        name = safe_filename(filename)
        validator = DocumentValidator(name)

        async def checked_chunks() -> AsyncIterator[bytes]:
            async for chunk in chunks:
                validator.feed(chunk)  # превышение размера или чужой тип обрывают запись
                yield chunk

        key = uuid.uuid4().hex
        await self._storage.save(key, checked_chunks())
        try:
            info = validator.finish()
            attachment = await self._attachments.get_by_application(application.id)
            previous_key = attachment.storage_key if attachment else None
            if attachment is None:
                attachment = Attachment(application_id=application.id)
                self._attachments.add(attachment)
            # у заявки один документ: новый файл заменяет старый
            attachment.original_filename = name
            attachment.content_type = info.content_type
            attachment.size_bytes = info.size_bytes
            attachment.sha256 = info.sha256
            attachment.storage_key = key
            attachment.uploaded_by = applicant.id
            attachment.created_at = datetime.now(UTC)
            await self._session.commit()
        except BaseException:
            await self._storage.delete(key)
            raise

        # старый файл удаляем только после успешного коммита
        if previous_key:
            await self._storage.delete(previous_key)

        details = await self._applications.get_details(application.id)
        if details is None:
            raise NotFoundError("Заявка не найдена", code="APPLICATION_NOT_FOUND")
        return details, allowed_actions.for_applicant(details)

    async def download_own(
        self, applicant: User, application_id: uuid.UUID
    ) -> tuple[Attachment, AsyncIterator[bytes]]:
        # владелец проверяется в запросе: чужой документ не найти, даже зная id заявки
        application = await self._applications.get_own(application_id, applicant.id)
        if application is None:
            raise NotFoundError("Заявка не найдена", code="APPLICATION_NOT_FOUND")
        return await self._open(application.id)

    async def _open(self, application_id: uuid.UUID) -> tuple[Attachment, AsyncIterator[bytes]]:
        attachment = await self._attachments.get_by_application(application_id)
        if attachment is None or not await self._storage.exists(attachment.storage_key):
            raise NotFoundError("Документ не приложен", code="ATTACHMENT_NOT_FOUND")
        return attachment, self._storage.read(attachment.storage_key)
