"""
backend/schemas/disbursement.py

Pydantic schemas for disbursement endpoints — create, update, and read models;
normalizes monetary inputs into Decimal.
"""

from __future__ import annotations

from typing import Optional
from decimal import Decimal, InvalidOperation
from datetime import datetime

from pydantic import BaseModel, Field, validator


# ---------------------------------------------------------
# BASE
# ---------------------------------------------------------

class DisbursementBase(BaseModel):
    """
    Base schema for disbursement records containing shared fields.
    Used as foundation for create/update request models.
    """

    subsidy_id: int = Field(..., ge=1, description="ID of the related subsidy")
    amount: Decimal = Field(..., description="Monetary amount as Decimal")
    currency: str = Field("INR", min_length=3, max_length=3, description="ISO 4217 currency code")
    reference: Optional[str] = Field(None, max_length=255, description="External transaction/reference id")
    date: Optional[datetime] = Field(None, description="Timestamp of disbursement")
    notes: Optional[str] = Field(None, description="Optional notes")

    @validator("currency")
    def normalize_currency(cls, v):
        """Normalize currency code to uppercase."""
        if v is None:
            return v
        return v.upper()

    @validator("reference")
    def normalize_reference(cls, v):
        """Strip leading and trailing whitespace from reference."""
        if v is None:
            return v
        return v.strip()


# ---------------------------------------------------------
# CREATE
# ---------------------------------------------------------

class DisbursementCreate(DisbursementBase):
    """
    Schema for creating new disbursement records.
    Accepts amount as string, float, or Decimal and converts safely to Decimal.
    """

    amount: str | float | Decimal = Field(
        ..., description="Monetary amount (accepts string, float, or Decimal)"
    )

    @validator("amount", pre=True)
    def validate_and_convert_amount(cls, v):
        """Convert amount safely to Decimal and validate positivity."""
        if v is None:
            raise ValueError("Amount cannot be None")

        try:
            decimal_value = Decimal(str(v))
        except (InvalidOperation, ValueError, TypeError):
            raise ValueError(f"Invalid amount value: {v}")

        if decimal_value <= 0:
            raise ValueError("Amount must be positive")

        return decimal_value


# ---------------------------------------------------------
# UPDATE
# ---------------------------------------------------------

class DisbursementUpdate(BaseModel):
    """
    Schema for partial updates to disbursement records.
    All fields optional.
    """

    subsidy_id: Optional[int] = Field(None, ge=1)
    amount: Optional[str | float | Decimal] = None
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    reference: Optional[str] = Field(None, max_length=255)
    date: Optional[datetime] = None
    notes: Optional[str] = None

    @validator("amount", pre=True)
    def validate_and_convert_amount(cls, v):
        """Convert amount to Decimal safely if provided."""
        if v is None:
            return v

        try:
            decimal_value = Decimal(str(v))
        except (InvalidOperation, ValueError, TypeError):
            raise ValueError(f"Invalid amount value: {v}")

        if decimal_value <= 0:
            raise ValueError("Amount must be positive")

        return decimal_value

    @validator("currency")
    def normalize_currency(cls, v):
        if v is None:
            return v
        return v.upper()

    @validator("reference")
    def normalize_reference(cls, v):
        if v is None:
            return v
        return v.strip()


# ---------------------------------------------------------
# RESPONSE MODEL
# ---------------------------------------------------------

class Disbursement(DisbursementBase):
    """
    Full disbursement record schema returned by API endpoints.
    """

    id: int
    approval_status: Optional[str] = "pending"
    approved_by: Optional[int] = None
    proof_document_url: Optional[str] = None
    is_late: Optional[bool] = False
    is_suspicious: Optional[bool] = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True


__all__ = [
    "DisbursementBase",
    "DisbursementCreate",
    "DisbursementUpdate",
    "Disbursement",
]