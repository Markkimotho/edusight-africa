from typing import Generic, TypeVar, Any
from pydantic import BaseModel

T = TypeVar("T")


class Meta(BaseModel):
    page: int
    per_page: int
    total: int
    total_pages: int


class PaginatedResponse(BaseModel, Generic[T]):
    data: list[T]
    meta: Meta

    @classmethod
    def create(cls, items: list[T], page: int, per_page: int, total: int) -> "PaginatedResponse[T]":
        import math
        total_pages = math.ceil(total / per_page) if per_page > 0 else 0
        return cls(
            data=items,
            meta=Meta(page=page, per_page=per_page, total=total, total_pages=total_pages),
        )


class SingleResponse(BaseModel, Generic[T]):
    data: T


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail
