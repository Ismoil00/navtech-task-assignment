"""Unit-тесты проверки документа.

Требование ТЗ: один файл PDF, JPG или PNG не больше 5 МБ; тип и размер
проверяются на сервере.
"""

import hashlib

import pytest

from app.domain.documents import (
    MAX_DOCUMENT_SIZE,
    DocumentInfo,
    DocumentValidator,
    EmptyFileError,
    FileTooLargeError,
    UnsupportedFileTypeError,
    safe_filename,
)

PDF = b"%PDF-1.7\n" + b"0" * 100
PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 100
JPEG = b"\xff\xd8\xff\xe0" + b"0" * 100
EXE = b"MZ\x90\x00" + b"0" * 100


def validate(filename: str, data: bytes, chunk_size: int = 64 * 1024) -> DocumentInfo:
    validator = DocumentValidator(filename)
    for start in range(0, len(data), chunk_size):
        validator.feed(data[start : start + chunk_size])
    return validator.finish()


@pytest.mark.parametrize(
    ("filename", "data", "content_type"),
    [
        ("справка.pdf", PDF, "application/pdf"),
        ("scan.png", PNG, "image/png"),
        ("photo.jpg", JPEG, "image/jpeg"),
        ("photo.jpeg", JPEG, "image/jpeg"),
        ("SCAN.PDF", PDF, "application/pdf"),
    ],
)
def test_allowed_documents_are_accepted(filename: str, data: bytes, content_type: str) -> None:
    info = validate(filename, data)
    assert info.content_type == content_type
    assert info.size_bytes == len(data)
    assert info.sha256 == hashlib.sha256(data).hexdigest()


@pytest.mark.parametrize("filename", ["virus.exe", "doc.docx", "image.gif", "no_extension"])
def test_other_extensions_are_rejected(filename: str) -> None:
    with pytest.raises(UnsupportedFileTypeError):
        DocumentValidator(filename)


@pytest.mark.parametrize(
    ("filename", "data"),
    [
        ("invoice.pdf", EXE),  # переименованный исполняемый файл
        ("invoice.pdf", PNG),  # картинка под видом PDF
        ("photo.png", PDF),
        ("photo.jpg", b"just some text"),
    ],
)
def test_content_must_match_extension(filename: str, data: bytes) -> None:
    with pytest.raises(UnsupportedFileTypeError) as error:
        validate(filename, data)
    assert error.value.status_code == 415


def test_signature_split_across_chunks_is_detected() -> None:
    assert validate("scan.png", PNG, chunk_size=1).content_type == "image/png"


def test_short_file_with_valid_signature() -> None:
    assert validate("tiny.jpg", b"\xff\xd8\xff\xd9").content_type == "image/jpeg"


def test_exactly_five_megabytes_is_accepted() -> None:
    data = PDF + b"0" * (MAX_DOCUMENT_SIZE - len(PDF))
    assert validate("big.pdf", data).size_bytes == MAX_DOCUMENT_SIZE


def test_more_than_five_megabytes_is_rejected_while_reading() -> None:
    validator = DocumentValidator("big.pdf")
    validator.feed(PDF + b"0" * (MAX_DOCUMENT_SIZE - len(PDF)))
    # чтение обрывается на первом же байте сверх лимита, не дожидаясь конца файла
    with pytest.raises(FileTooLargeError) as error:
        validator.feed(b"0")
    assert error.value.status_code == 413


def test_empty_file_is_rejected() -> None:
    with pytest.raises(EmptyFileError):
        validate("empty.pdf", b"")


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("C:\\Users\\me\\Документы\\паспорт.pdf", "паспорт.pdf"),
        ("../../etc/passwd.png", "passwd.png"),
        ('bad"name\x00.pdf', "badname.pdf"),
        ("  много   пробелов .jpg ", "много пробелов .jpg"),
        ("", "document"),
        (None, "document"),
    ],
)
def test_safe_filename(raw: str | None, expected: str) -> None:
    assert safe_filename(raw) == expected
