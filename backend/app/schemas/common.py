"""Shared response schemas."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    """Generic paginated response envelope.

    Returned by every list endpoint. `items` is the current page, `total` is
    the unpaginated row count, `limit` and `offset` echo the request so the
    client can self-correct when it changes pagination state.
    """

    items: list[T]
    total: int
    limit: int
    offset: int
