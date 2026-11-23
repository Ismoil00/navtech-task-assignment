from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.error_handlers import error_body


class RequestSizeLimitMiddleware:
    """Отклоняет слишком большие запросы до того, как FastAPI начнёт разбирать тело.

    Без фильтра multipart-парсер сначала целиком сохранил бы огромную загрузку
    во временный файл. Точный размер документа всё равно проверяется при чтении
    (DocumentValidator): этот фильтр лишь отсекает заведомо огромные запросы.
    """

    def __init__(self, app: ASGIApp, max_body_size: int) -> None:
        self.app = app
        self.max_body_size = max_body_size
        # сколько максимум дочитать «вхолостую», прежде чем закрыть соединение
        self.drain_limit = max_body_size * 4

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and self._too_large(scope):
            await self._drain(receive)
            response = JSONResponse(
                status_code=413,
                content=error_body("FILE_TOO_LARGE", "Файл больше 5 МБ"),
                headers={"Connection": "close"},
            )
            await response(scope, receive, send)
            return
        await self.app(scope, receive, send)

    def _too_large(self, scope: Scope) -> bool:
        content_length = dict(scope["headers"]).get(b"content-length", b"")
        return content_length.isdigit() and int(content_length) > self.max_body_size

    async def _drain(self, receive: Receive) -> None:
        # Тело дочитывается и сразу выбрасывается (ничего не сохраняется). Иначе клиент,
        # который ещё отправляет файл, может так и не прочитать наш ответ и зависнуть.
        received = 0
        while received <= self.drain_limit:
            message = await receive()
            if message["type"] != "http.request":
                return
            received += len(message.get("body", b""))
            if not message.get("more_body", False):
                return
