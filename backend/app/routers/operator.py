import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from app.domain.enums import ApplicationStatus
from app.routers.deps import OperatorServiceDep, require_operator
from app.routers.files import document_response
from app.schemas.application import ApplicationListItem, ApplicationRead
from app.schemas.common import Page

# Кабинет оператора: роль проверяется для всех эндпоинтов роутера
router = APIRouter(
    prefix="/operator/applications",
    tags=["operator"],
    dependencies=[Depends(require_operator)],
)


@router.get("", response_model=Page[ApplicationListItem])
async def list_queue(
    service: OperatorServiceDep,
    status_filter: Annotated[ApplicationStatus | None, Query(alias="status")] = None,
    service_type_id: Annotated[int | None, Query(gt=0)] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
):
    result = await service.list_queue(
        status=status_filter, service_type_id=service_type_id, page=page, page_size=page_size
    )
    return Page.from_result(result, ApplicationListItem)


@router.get("/{application_id}", response_model=ApplicationRead)
async def get_application(application_id: uuid.UUID, service: OperatorServiceDep):
    return ApplicationRead.build(*await service.get(application_id))


@router.get("/{application_id}/file", response_class=StreamingResponse)
async def download_document(application_id: uuid.UUID, service: OperatorServiceDep):
    return document_response(*await service.download(application_id))
