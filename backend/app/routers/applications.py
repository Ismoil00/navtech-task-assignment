import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from fastapi.responses import StreamingResponse

from app.domain.enums import ApplicationStatus
from app.routers.deps import (
    ApplicantDep,
    ApplicationServiceDep,
    AttachmentServiceDep,
    require_applicant,
)
from app.routers.files import document_response, read_upload
from app.schemas.application import (
    ApplicationCreate,
    ApplicationListItem,
    ApplicationRead,
    ApplicationUpdate,
)
from app.schemas.common import Page

# Кабинет заявителя: роль проверяется для всех эндпоинтов роутера,
# а владелец заявки — в каждом запросе к БД.
router = APIRouter(
    prefix="/applications",
    tags=["applicant"],
    dependencies=[Depends(require_applicant)],
)


@router.get("", response_model=Page[ApplicationListItem])
async def list_my_applications(
    user: ApplicantDep,
    service: ApplicationServiceDep,
    status_filter: Annotated[ApplicationStatus | None, Query(alias="status")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
):
    result = await service.list_own(user, status=status_filter, page=page, page_size=page_size)
    return Page.from_result(result, ApplicationListItem)


@router.post("", response_model=ApplicationRead, status_code=status.HTTP_201_CREATED)
async def create_application(
    payload: ApplicationCreate, user: ApplicantDep, service: ApplicationServiceDep
):
    return ApplicationRead.build(*await service.create(user, payload))


@router.get("/{application_id}", response_model=ApplicationRead)
async def get_application(
    application_id: uuid.UUID, user: ApplicantDep, service: ApplicationServiceDep
):
    return ApplicationRead.build(*await service.get_own(user, application_id))


@router.patch("/{application_id}", response_model=ApplicationRead)
async def update_application(
    application_id: uuid.UUID,
    payload: ApplicationUpdate,
    user: ApplicantDep,
    service: ApplicationServiceDep,
):
    return ApplicationRead.build(*await service.update(user, application_id, payload))


@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_application(
    application_id: uuid.UUID, user: ApplicantDep, service: ApplicationServiceDep
):
    await service.delete(user, application_id)


@router.put("/{application_id}/file", response_model=ApplicationRead)
async def upload_document(
    application_id: uuid.UUID,
    file: Annotated[UploadFile, File(description="PDF, JPG или PNG, не больше 5 МБ")],
    user: ApplicantDep,
    service: AttachmentServiceDep,
):
    result = await service.upload(
        user, application_id, filename=file.filename, chunks=read_upload(file)
    )
    return ApplicationRead.build(*result)


@router.get("/{application_id}/file", response_class=StreamingResponse)
async def download_document(
    application_id: uuid.UUID, user: ApplicantDep, service: AttachmentServiceDep
):
    return document_response(*await service.download_own(user, application_id))
