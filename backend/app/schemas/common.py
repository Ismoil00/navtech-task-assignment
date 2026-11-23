from math import ceil

from pydantic import BaseModel

from app.services.pagination import PageResult


class Page[ItemT](BaseModel):
    items: list[ItemT]
    total: int
    page: int
    page_size: int
    pages: int

    @classmethod
    def from_result(cls, result: PageResult, item_schema: type[ItemT]) -> "Page[ItemT]":
        return cls(
            items=[item_schema.model_validate(item) for item in result.items],
            total=result.total,
            page=result.page,
            page_size=result.page_size,
            pages=ceil(result.total / result.page_size) if result.total else 0,
        )
