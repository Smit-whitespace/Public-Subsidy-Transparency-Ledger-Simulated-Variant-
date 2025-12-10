"""
backend/schemas/audit.py

Pydantic schemas for audit record endpoints.
Provides read models, create models, and paginated response wrapper for audit logs.
"""

from __future__ import annotations
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, validator


class AuditBase(BaseModel):
    """
    Base schema for audit records containing core fields.
    """
    entity: str = Field(..., max_length=100, description="Entity type, e.g. 'subsidy' or 'project'")
    entity_id: int = Field(..., ge=1, description="Primary key of the affected entity")
    action: str = Field(..., max_length=100, description="Action performed, e.g. create/update/delete")
    details: Optional[str] = Field(None, description="Optional freeform details or JSON string describing the change")


class AuditCreate(AuditBase):
    """
    Schema for creating new audit records (POST body).
    Normalizes action field to lowercase for consistency.
    """
    
    @validator("action")
    def normalize_action(cls, v):
        """Strip whitespace and convert action to lowercase."""
        if v is None:
            return v
        return v.strip().lower()


class AuditRecord(AuditBase):
    """
    Full audit record schema returned by API endpoints.
    Includes auto-generated fields like id and created_at.
    """
    id: int
    created_at: datetime
    
    class Config:
        orm_mode = True
        from_attributes = True


class PaginatedAuditResponse(BaseModel):
    """
    Paginated wrapper for audit record list endpoints.
    Contains total count and list of items for client-side pagination.
    """
    total: int = Field(..., ge=0)
    items: List[AuditRecord] = Field(..., description="List of audit records")


__all__ = ["AuditBase", "AuditCreate", "AuditRecord", "PaginatedAuditResponse"]

# Example: AuditCreate(entity="subsidy", entity_id=1, action="Create", details="initial import")