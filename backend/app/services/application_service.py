import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BusinessValidationError, ConflictError, NotFoundError
from app.domain.enums import AllowedAction, ApplicationStatus
from app.domain.status_machine import DELETABLE_STATUSES, EDITABLE_STATUSES, STATUS_LABELS
from app.models import Application, ApplicationStatusHistory, User
from app.repositories.application_repository import ApplicationRepository
from app.repositories.service_type_repository import ServiceTypeRepository
from app.repositories.status_history_repository import StatusHistoryRepository
from app.schemas.application import ApplicationCreate, ApplicationUpdate
from app.services import allowed_actions
from app.services.pagination import PageResult, page_offset


class ApplicationService:
    """Заявки в кабинете заявителя: черновики, их изменение и просмотр."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._applications = ApplicationRepository(session)
        self._service_types = ServiceTypeRepository(session)
        self._history = StatusHistoryRepository(session)

    async def list_own(
        self, applicant: User, *, status: ApplicationStatus | None, page: int, page_size: int
    ) -> PageResult:
        items, total = await self._applications.list_own(
            applicant.id, status=status, offset=page_offset(page, page_size), limit=page_size
        )
        return PageResult(items=items, total=total, page=page, page_size=page_size)

    async def get_own(
        self, applicant: User, application_id: uuid.UUID
    ) -> tuple[Application, list[AllowedAction]]:
        await self._get_own(applicant, application_id)
        return await self._details(application_id)

    async def create(
        self, applicant: User, data: ApplicationCreate
    ) -> tuple[Application, list[AllowedAction]]:
        await self._ensure_service_type_active(data.service_type_id)

        application = Application(
            applicant_id=applicant.id,
            service_type_id=data.service_type_id,
            full_name=data.full_name,
            phone=data.phone,
            comment=data.comment,
            status=ApplicationStatus.DRAFT,
        )
        self._applications.add(application)
        await self._session.flush()
        # первая запись истории — создание черновика
        self._history.add(
            ApplicationStatusHistory(
                application_id=application.id,
                from_status=None,
                to_status=ApplicationStatus.DRAFT,
                actor_id=applicant.id,
            )
        )
        await self._session.commit()
        return await self._details(application.id)

    async def update(
        self, applicant: User, application_id: uuid.UUID, data: ApplicationUpdate
    ) -> tuple[Application, list[AllowedAction]]:
        application = await self._get_own(applicant, application_id, for_update=True)
        if application.status not in EDITABLE_STATUSES:
            raise ConflictError(
                f"Заявку в статусе «{STATUS_LABELS[application.status]}» изменить нельзя",
                code="APPLICATION_NOT_EDITABLE",
            )

        changes = data.model_dump(exclude_unset=True)
        new_service_type = changes.get("service_type_id", application.service_type_id)
        if new_service_type != application.service_type_id:
            # после оплаты тип услуги зафиксирован: от него зависела списанная сумма
            if application.status != ApplicationStatus.DRAFT:
                raise ConflictError(
                    "Тип услуги нельзя изменить после оплаты", code="SERVICE_TYPE_LOCKED"
                )
            await self._ensure_service_type_active(new_service_type)

        for field, value in changes.items():
            setattr(application, field, value)
        await self._session.commit()
        return await self._details(application.id)

    async def delete(self, applicant: User, application_id: uuid.UUID) -> None:
        application = await self._get_own(applicant, application_id, for_update=True)
        if application.status not in DELETABLE_STATUSES:
            raise ConflictError(
                "Удалить можно только неоплаченный черновик", code="APPLICATION_NOT_DELETABLE"
            )
        # мягкое удаление: попытки оплаты и история остаются в базе
        application.deleted_at = datetime.now(UTC)
        await self._session.commit()

    async def _get_own(
        self, applicant: User, application_id: uuid.UUID, *, for_update: bool = False
    ) -> Application:
        application = await self._applications.get_own(
            application_id, applicant.id, for_update=for_update
        )
        if application is None:
            raise NotFoundError("Заявка не найдена", code="APPLICATION_NOT_FOUND")
        return application

    async def _details(self, application_id: uuid.UUID) -> tuple[Application, list[AllowedAction]]:
        application = await self._applications.get_details(application_id)
        if application is None:
            raise NotFoundError("Заявка не найдена", code="APPLICATION_NOT_FOUND")
        return application, allowed_actions.for_applicant(application)

    async def _ensure_service_type_active(self, service_type_id: int) -> None:
        if await self._service_types.get_active(service_type_id) is None:
            raise BusinessValidationError(
                "Выбранная услуга недоступна",
                code="SERVICE_TYPE_NOT_FOUND",
                details=[{"field": "service_type_id", "message": "Выберите услугу из списка"}],
            )
