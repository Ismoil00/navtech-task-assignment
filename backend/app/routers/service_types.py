from fastapi import APIRouter

from app.routers.deps import ServiceTypeServiceDep
from app.schemas.service_type import ServiceTypeRead

router = APIRouter(prefix="/service-types", tags=["service-types"])


@router.get("", response_model=list[ServiceTypeRead])
async def list_service_types(service: ServiceTypeServiceDep):
    return await service.list_active()
