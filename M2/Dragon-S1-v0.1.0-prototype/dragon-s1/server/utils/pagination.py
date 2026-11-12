from __future__ import annotations

import math
from typing import Any, Generic, TypeVar
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.orm import Session

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool


def paginate(
    db: Session,
    statement: Any,
    page: int = 1,
    page_size: int = 20,
    dict_converter: Any = None
) -> dict:
    """Utility function to paginate SQLAlchemy statements."""
    page = max(1, page)
    page_size = max(1, min(100, page_size)) # Limit max page size to 100
    
    # 1. Calculate total count
    count_statement = select(func.count()).select_from(statement.subquery())
    total = db.scalar(count_statement) or 0
    
    # 2. Get subset of results
    offset = (page - 1) * page_size
    results_statement = statement.offset(offset).limit(page_size)
    items = db.scalars(results_statement).all()
    
    # 3. Convert results to dict if converter is provided
    if dict_converter:
        items = [dict_converter(item) for item in items]

    total_pages = math.ceil(total / page_size) if total > 0 else 1
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }
