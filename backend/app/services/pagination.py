from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PageResult:
    """Страница результатов: сервис отдаёт её роутеру, роутер — схеме Page."""

    items: Sequence[Any]
    total: int
    page: int
    page_size: int


def page_offset(page: int, page_size: int) -> int:
    return (page - 1) * page_size
