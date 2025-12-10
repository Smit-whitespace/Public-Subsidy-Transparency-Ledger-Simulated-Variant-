"""
backend/schemas/common.py

Common reusable Pydantic schemas: pagination, generic responses, and simple error shapes used across API endpoints.
"""

from __future__ import annotations
from typing import TypeVar, Generic, Optional, List, Dict
from pydantic import BaseModel, Field
from pydantic.generics import GenericModel
from enum import Enum
from datetime import datetime


class SortOrder(Enum):
    """
    Enumeration for sort direction in query parameters.
    Used across list endpoints to specify ascending or descending order.
    """
    ASC = "asc"
    DESC = "desc"


class PaginationParams(BaseModel):
    """
    Lightweight container for pagination and sorting parameters.
    Used as a reusable dependency or inline model for list endpoints.
    """
    limit: int = Field(50, ge=1, le=1000, description="Max items to return")
    offset: int = Field(0, ge=0, description="Pagination offset")
    sort_by: Optional[str] = Field(None, description="Optional sort field (whitelist on server)")
    order: SortOrder = Field(SortOrder.DESC, description="Sort direction")


T = TypeVar("T")


class PaginatedResponse(GenericModel, Generic[T]):
    """
    Generic paginated response wrapper.
    Provides total count, current page items, and pagination metadata.
    Use this for endpoints that return lists with pagination.
    """
    total: int = Field(..., ge=0, description="Total number of matching items")
    items: List[T] = Field(..., description="Page of results")
    limit: int = Field(..., ge=1)
    offset: int = Field(..., ge=0)
    
    class Config:
        orm_mode = True


class APIResponse(GenericModel, Generic[T]):
    """
    Generic API response envelope.
    Wraps success or error responses in a consistent structure.
    Set status to 'ok' with data for successful responses, or 'error' with error dict for failures.
    """
    status: str = Field("ok", description="ok or error")
    data: Optional[T] = Field(None, description="Response payload when status is ok")
    error: Optional[Dict[str, str]] = Field(None, description="Error information when status is error")
    
    class Config:
        orm_mode = True


class ErrorResponse(BaseModel):
    """
    Structured error response schema.
    Provides human-readable detail, optional machine-readable code, and timestamp.
    """
    detail: str = Field(..., description="Human-readable error message")
    code: Optional[str] = Field(None, description="Optional machine-readable error code")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


__all__ = ["SortOrder", "PaginationParams", "T", "PaginatedResponse", "APIResponse", "ErrorResponse"]

# Example: PaginatedResponse[int](total=100, items=[1,2,3], limit=10, offset=0)