"""Правила для документа заявки: один файл PDF, JPG или PNG не больше 5 МБ.

Тип определяется по первым байтам содержимого (сигнатуре), а не по расширению
или заголовку Content-Type от клиента: переименованный .exe не пройдёт.
"""

import hashlib
import re
import unicodedata
from dataclasses import dataclass
from pathlib import PurePosixPath

from app.core.errors import AppError, BusinessValidationError

MAX_DOCUMENT_SIZE = 5 * 1024 * 1024  # 5 МБ

ALLOWED_EXTENSIONS = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}

_SIGNATURES = (
    (b"%PDF-", "application/pdf"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"\xff\xd8\xff", "image/jpeg"),
)
_SIGNATURE_LENGTH = max(len(signature) for signature, _ in _SIGNATURES)
_ALLOWED_TYPES_TEXT = "PDF, JPG или PNG"


class UnsupportedFileTypeError(AppError):
    status_code = 415
    code = "UNSUPPORTED_FILE_TYPE"
    message = f"Допустимы только файлы {_ALLOWED_TYPES_TEXT}"


class FileTooLargeError(AppError):
    status_code = 413
    code = "FILE_TOO_LARGE"
    message = "Файл больше 5 МБ"


class EmptyFileError(BusinessValidationError):
    code = "EMPTY_FILE"
    message = "Файл пустой"


@dataclass(frozen=True)
class DocumentInfo:
    content_type: str
    size_bytes: int
    sha256: str


def detect_content_type(head: bytes) -> str | None:
    for signature, content_type in _SIGNATURES:
        if head.startswith(signature):
            return content_type
    return None


class DocumentValidator:
    """Проверяет файл по мере чтения, не загружая его целиком в память.

    feed() вызывается для каждого куска: размер считается сразу, и чтение
    обрывается, как только файл превысил лимит. finish() — в конце потока.
    """

    def __init__(self, filename: str) -> None:
        extension = PurePosixPath(filename.lower()).suffix
        expected = ALLOWED_EXTENSIONS.get(extension)
        if expected is None:
            raise UnsupportedFileTypeError()
        self._expected_type = expected
        self._head = b""
        self._signature_checked = False
        self._size = 0
        self._sha256 = hashlib.sha256()

    def feed(self, chunk: bytes) -> None:
        self._size += len(chunk)
        if self._size > MAX_DOCUMENT_SIZE:
            raise FileTooLargeError()
        if not self._signature_checked:
            self._head += chunk[:_SIGNATURE_LENGTH]
            if len(self._head) >= _SIGNATURE_LENGTH:
                self._check_signature()
        self._sha256.update(chunk)

    def finish(self) -> DocumentInfo:
        if self._size == 0:
            raise EmptyFileError()
        if not self._signature_checked:
            self._check_signature()  # файл короче самой длинной сигнатуры
        return DocumentInfo(
            content_type=self._expected_type,
            size_bytes=self._size,
            sha256=self._sha256.hexdigest(),
        )

    def _check_signature(self) -> None:
        self._signature_checked = True
        if detect_content_type(self._head) != self._expected_type:
            raise UnsupportedFileTypeError(
                f"Содержимое файла не соответствует расширению. "
                f"Допустимы только файлы {_ALLOWED_TYPES_TEXT}"
            )


_UNSAFE_CHARS = re.compile(r"[\x00-\x1f\x7f\"]")


def safe_filename(filename: str | None) -> str:
    """Имя для показа и скачивания: без пути, управляющих символов и кавычек."""
    name = (filename or "").replace("\\", "/").rsplit("/", 1)[-1]
    name = _UNSAFE_CHARS.sub("", unicodedata.normalize("NFC", name))
    name = " ".join(name.split())
    if len(name) > 255:
        path = PurePosixPath(name)
        name = path.stem[: 255 - len(path.suffix)] + path.suffix
    return name or "document"
