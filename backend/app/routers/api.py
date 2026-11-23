from fastapi import APIRouter, Depends

from app.routers import auth, health, service_types
from app.routers.deps import get_current_user


def build_api_router() -> APIRouter:
    api = APIRouter()

    # Публичные эндпоинты. Только они доступны без access-токена.
    api.include_router(health.router)
    api.include_router(auth.public_router)

    # Всё остальное закрыто по умолчанию: проверка токена висит на самом роутере,
    # поэтому новый эндпоинт не может случайно оказаться публичным.
    # Проверка роли добавляется на роутерах конкретного кабинета.
    protected = APIRouter(dependencies=[Depends(get_current_user)])
    protected.include_router(auth.protected_router)
    protected.include_router(service_types.router)

    api.include_router(protected)
    return api
