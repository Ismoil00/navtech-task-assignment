from typing import Annotated

from fastapi import APIRouter, Cookie, Response, status

from app.core.config import get_settings
from app.routers.deps import AuthServiceDep
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserRead
from app.services.auth_service import AuthSession

settings = get_settings()

router = APIRouter(prefix="/auth", tags=["auth"])

# refresh-токен живёт в httpOnly cookie: JavaScript его не видит,
# а браузер отправляет его только на эндпоинты /api/auth
RefreshCookie = Annotated[str | None, Cookie(alias=settings.refresh_cookie_name)]
_COOKIE_PATH = f"{settings.api_prefix}/auth"


def _set_refresh_cookie(response: Response, auth: AuthSession) -> None:
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=auth.refresh_token,
        max_age=settings.refresh_token_ttl_days * 24 * 60 * 60,
        path=_COOKIE_PATH,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite="lax",
    )


def _token_response(auth: AuthSession) -> TokenResponse:
    return TokenResponse(
        access_token=auth.access_token.token,
        expires_in=auth.access_token.expires_in,
        user=UserRead.model_validate(auth.user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, response: Response, service: AuthServiceDep):
    auth = await service.login(payload.username, payload.password, payload.portal)
    _set_refresh_cookie(response, auth)
    return _token_response(auth)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(response: Response, service: AuthServiceDep, refresh_token: RefreshCookie = None):
    auth = await service.refresh(refresh_token)
    _set_refresh_cookie(response, auth)
    return _token_response(auth)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response, service: AuthServiceDep, refresh_token: RefreshCookie = None):
    await service.logout(refresh_token)
    response.delete_cookie(settings.refresh_cookie_name, path=_COOKIE_PATH)
