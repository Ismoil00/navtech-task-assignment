from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.errors import register_error_handlers
from app.routers.api import build_api_router


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        docs_url=f"{settings.api_prefix}/docs",
        openapi_url=f"{settings.api_prefix}/openapi.json",
        redoc_url=None,
    )

    app.add_middleware(
        CORSMiddleware,
        # Явный список адресов: с allow_credentials "*" использовать нельзя
        allow_origins=settings.cors_origin_list,
        # нужно, чтобы браузер отправлял cookie с refresh-токеном
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "Idempotency-Key"],
        # без этого фронтенд не прочитает имя файла при скачивании
        expose_headers=["Content-Disposition"],
        max_age=600,
    )

    register_error_handlers(app)
    app.include_router(build_api_router(), prefix=settings.api_prefix)
    return app


app = create_app()
