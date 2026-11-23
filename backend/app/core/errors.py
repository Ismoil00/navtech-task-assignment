"""Ошибки приложения и единый формат ответа об ошибке.

Любая ошибка API возвращается в виде:
    {"error": {"code": "INVALID_STATUS_TRANSITION", "message": "...", "details": ...}}
code — стабильный машинный код для фронтенда, message — текст для пользователя.
"""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class AppError(Exception):
    status_code: int = 400
    code: str = "BAD_REQUEST"
    message: str = "Некорректный запрос"

    def __init__(
        self, message: str | None = None, *, code: str | None = None, details: Any = None
    ) -> None:
        self.message = message or self.message
        self.code = code or self.code
        self.details = details
        super().__init__(self.message)


class UnauthorizedError(AppError):
    status_code = 401
    code = "UNAUTHORIZED"
    message = "Требуется авторизация"


class ForbiddenError(AppError):
    status_code = 403
    code = "FORBIDDEN"
    message = "Недостаточно прав для этого действия"


class NotFoundError(AppError):
    status_code = 404
    code = "NOT_FOUND"
    message = "Не найдено"


class ConflictError(AppError):
    status_code = 409
    code = "CONFLICT"
    message = "Действие недоступно в текущем состоянии"


class BusinessValidationError(AppError):
    status_code = 422
    code = "VALIDATION_ERROR"
    message = "Проверьте правильность заполнения полей"


def error_body(code: str, message: str, details: Any = None) -> dict[str, Any]:
    return {"error": {"code": code, "message": message, "details": details}}


# Сообщения Pydantic по умолчанию на английском — переводим основные типы ошибок
_VALIDATION_MESSAGES = {
    "missing": "Обязательное поле",
    "string_too_short": "Слишком короткое значение (минимум {min_length} симв.)",
    "string_too_long": "Слишком длинное значение (максимум {max_length} симв.)",
    "string_type": "Ожидается строка",
    "int_parsing": "Ожидается целое число",
    "int_type": "Ожидается целое число",
    "greater_than_equal": "Значение должно быть не меньше {ge}",
    "less_than_equal": "Значение должно быть не больше {le}",
    "enum": "Недопустимое значение",
    "literal_error": "Недопустимое значение",
    "uuid_parsing": "Некорректный идентификатор",
    "json_invalid": "Некорректный JSON",
    "extra_forbidden": "Неизвестное поле",
}


def _translate(error: dict[str, Any]) -> str:
    context = error.get("ctx") or {}
    if error["type"] == "value_error" and "error" in context:
        # наши собственные валидаторы уже пишут сообщения по-русски
        return str(context["error"])
    template = _VALIDATION_MESSAGES.get(error["type"])
    if template is None:
        return "Некорректное значение"
    try:
        return template.format(**context)
    except (KeyError, IndexError):
        return template


async def _app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
    return JSONResponse(
        status_code=exc.status_code,
        content=error_body(exc.code, exc.message, exc.details),
        headers=headers,
    )


async def _validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    details = [
        {
            # первый элемент loc — источник (body/query/path), поле идёт дальше
            "field": ".".join(str(part) for part in error["loc"][1:]) or None,
            "message": _translate(error),
        }
        for error in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content=error_body("VALIDATION_ERROR", BusinessValidationError.message, details),
    )


async def _http_error_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    known = {
        404: ("NOT_FOUND", "Ресурс не найден"),
        405: ("METHOD_NOT_ALLOWED", "Метод не поддерживается"),
    }
    code, message = known.get(exc.status_code, ("HTTP_ERROR", str(exc.detail)))
    return JSONResponse(status_code=exc.status_code, content=error_body(code, message))


async def _unhandled_error_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Необработанная ошибка", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content=error_body("INTERNAL_ERROR", "Внутренняя ошибка сервера. Попробуйте позже."),
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, _app_error_handler)
    app.add_exception_handler(RequestValidationError, _validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, _http_error_handler)
    app.add_exception_handler(Exception, _unhandled_error_handler)
