from fastapi import FastAPI

from app.core.config import get_settings
from app.core.errors import register_error_handlers
from app.routers import auth, health


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        docs_url=f"{settings.api_prefix}/docs",
        openapi_url=f"{settings.api_prefix}/openapi.json",
        redoc_url=None,
    )
    register_error_handlers(app)
    app.include_router(health.router, prefix=settings.api_prefix)
    app.include_router(auth.router, prefix=settings.api_prefix)
    return app


app = create_app()
