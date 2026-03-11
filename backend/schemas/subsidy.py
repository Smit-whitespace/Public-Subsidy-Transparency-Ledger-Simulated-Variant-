"""
backend/schemas/subsidy.py

Pydantic schemas for Subsidy entity — create/update/read shapes.
Aligned with SQLAlchemy model using `total_allocation`.
"""

from __future__ import annotations
from typing import Optional
from decimal import Decimal, InvalidOperation
from datetime import datetime
from pydantic import BaseModel, Field, validator


# ============================================================
# BASE SCHEMA (Shared Fields)
# ============================================================

class SubsidyBase(BaseModel):
    """
    Base schema shared across create/update/read.
    Field names MUST match SQLAlchemy model exactly.
    """

    title: str = Field(..., max_length=255)
    recipient: str = Field(..., max_length=255)

    # 🔥 FIXED: aligned with ORM model
    total_allocation: Decimal = Field(..., description="Total authorized allocation")

    currency: str = Field("INR", min_length=3, max_length=3)

    description: Optional[str] = None
    meta_data: Optional[str] = None

    status: Optional[str] = None

    is_active: Optional[bool] = True

    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


# ============================================================
# CREATE
# ============================================================

class SubsidyCreate(SubsidyBase):
    """
    Accept flexible monetary input but store as Decimal.
    """

    title: str
    recipient: str
    sector: str

    total_allocation: str | float | Decimal
    currency: str | None = "INR"

    description: str | None = None
    meta_data: str | dict | None = None

    status: str | None = "active"
    is_active: bool | None = True

    start_date: datetime | None = None
    end_date: datetime | None = None

    @validator("title")
    def normalize_title(cls, v):
        stripped = v.strip()
        if not stripped:
            raise ValueError("Title cannot be empty")
        return stripped

    @validator("recipient")
    def normalize_recipient(cls, v):
        stripped = v.strip()
        if not stripped:
            raise ValueError("Recipient cannot be empty")
        return stripped

    @validator("sector")
    def normalize_sector(cls, v):
        stripped = v.strip().lower()
        if not stripped:
            raise ValueError("Sector cannot be empty")
        return stripped

    @validator("total_allocation", pre=True)
    def validate_total_allocation(cls, v):
        try:
            value = Decimal(str(v))
        except (InvalidOperation, TypeError):
            raise ValueError("Invalid total_allocation value")

        if value <= 0:
            raise ValueError("total_allocation must be positive")

        return value

    @validator("currency", pre=True, always=True)
    def normalize_currency(cls, v):
        return (v or "INR").strip().upper()

    @validator("meta_data", pre=True)
    def normalize_metadata(cls, v):
        if v is None:
            return None
        if isinstance(v, dict):
            import json
            return json.dumps(v, separators=(",", ":"))
        if isinstance(v, str):
            return v.strip()
        return v
    
# ============================================================
# UPDATE (PATCH)
# ============================================================

class SubsidyUpdate(BaseModel):
    """
    Partial update schema.
    """

    title: Optional[str] = None
    recipient: Optional[str] = None
    total_allocation: Optional[str | float | Decimal] = None
    currency: Optional[str] = None
    description: Optional[str] = None
    meta_data: Optional[str] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    @validator("title")
    def normalize_title(cls, v):
        if v is None:
            return None
        stripped = v.strip()
        if not stripped:
            raise ValueError("Title cannot be empty")
        return stripped

    @validator("recipient")
    def normalize_recipient(cls, v):
        if v is None:
            return None
        stripped = v.strip()
        if not stripped:
            raise ValueError("Recipient cannot be empty")
        return stripped

    @validator("total_allocation", pre=True)
    def validate_total_allocation(cls, v):
        if v is None:
            return None
        try:
            value = Decimal(str(v))
        except (InvalidOperation, TypeError):
            raise ValueError("Invalid total_allocation value")

        if value <= 0:
            raise ValueError("total_allocation must be positive")

        return value

    @validator("currency", pre=True)
    def normalize_currency(cls, v):
        if v is None:
            return None
        return v.strip().upper()

    @validator("meta_data", pre=True)
    def normalize_metadata(cls, v):
        if v is None:
            return None
        if isinstance(v, dict):
            import json
            return json.dumps(v, separators=(",", ":"))
        if isinstance(v, str):
            return v.strip()
        return v


# ============================================================
# READ (Response Model)
# ============================================================

class Subsidy(SubsidyBase):
    """
    Full API response model.
    """

    id: int
    risk_score: Optional[Decimal] = None
    transparency_score: Optional[Decimal] = None
    is_flagged: Optional[bool] = None

    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True


__all__ = [
    "SubsidyBase",
    "SubsidyCreate",
    "SubsidyUpdate",
    "Subsidy",
]