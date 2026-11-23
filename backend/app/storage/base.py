from collections.abc import AsyncIterable, AsyncIterator
from typing import Protocol


class FileStorage(Protocol):
    """Хранилище файлов. Сервисы работают только с этим интерфейсом.

    Сейчас реализация одна — локальный диск (том Docker). Облачное хранилище
    (S3, Vercel Blob) добавляется новой реализацией без изменений в сервисах.
    """

    async def save(self, key: str, chunks: AsyncIterable[bytes]) -> None:
        """Сохраняет поток. При ошибке в потоке частично записанный файл удаляется."""

    def read(self, key: str) -> AsyncIterator[bytes]:
        """Отдаёт файл кусками, не загружая его целиком в память."""

    async def exists(self, key: str) -> bool:
        """Есть ли файл. Проверяется до отправки заголовков ответа при скачивании."""

    async def delete(self, key: str) -> None:
        """Удаляет файл; отсутствие файла ошибкой не считается."""
