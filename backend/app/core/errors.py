"""Ошибки приложения.

Обычные исключения без зависимости от FastAPI: их бросают сервисы и доменный
слой, а в HTTP-ответ их превращает core/error_handlers.py.
"""

from typing import Any


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
