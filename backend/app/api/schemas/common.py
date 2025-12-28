"""
Common schemas for pagination and errors.
"""
from pydantic import BaseModel, Field
from typing import Generic, TypeVar, List


T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response"""
    data: List[T]
    total: int = Field(description="Total number of items")
    page: int = Field(description="Current page number")
    page_size: int = Field(description="Items per page")
    total_pages: int = Field(description="Total number of pages")

    model_config = {
        "json_schema_extra": {
            "example": {
                "data": [],
                "total": 150,
                "page": 1,
                "page_size": 50,
                "total_pages": 3
            }
        }
    }
