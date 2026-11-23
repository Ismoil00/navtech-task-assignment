"""HTTP-обвязка для файлов: чтение загрузки кусками и ответ на скачивание."""

from collections.abc import AsyncIterator
from pathlib import PurePosixPath
from urllib.parse import quote

from fastapi import UploadFile
from fastapi.responses import StreamingResponse

from app.models import Attachment

_CHUNK_SIZE = 64 * 1024


async def read_upload(file: UploadFile) -> AsyncIterator[bytes]:
    while chunk := await file.read(_CHUNK_SIZE):
        yield chunk


def _content_disposition(filename: str) -> str:
    # filename — запасной вариант латиницей для старых клиентов,
    # filename* (RFC 5987) — настоящее имя, в том числе кириллицей
    path = PurePosixPath(filename)
    ascii_stem = path.stem.encode("ascii", "ignore").decode().replace('"', "").strip()
    ascii_name = f"{ascii_stem or 'document'}{path.suffix}"
    return f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(filename)}"


def document_response(attachment: Attachment, chunks: AsyncIterator[bytes]) -> StreamingResponse:
    return StreamingResponse(
        chunks,
        media_type=attachment.content_type,
        headers={
            "Content-Disposition": _content_disposition(attachment.original_filename),
            "Content-Length": str(attachment.size_bytes),
            # браузер не будет «угадывать» тип и исполнять содержимое
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "private, no-store",
        },
    )
