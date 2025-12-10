"""
backend/schemas/disbursement.py

Pydantic schemas for disbursement endpoints — create, update, and read models; normalizes monetary inputs into Decimal.
"""

from __future__ import annotations
from typing import Optional, Dict, Any
from decimal import Decimal, InvalidOperation
from datetime import datetime
from pydantic import BaseModel, Field, validator


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


class DisbursementCreate(DisbursementBase):
    """
    Schema for creating new disbursement records.
    Accepts amount as string, float, or Decimal and converts safely to Decimal for storage.
    Validates that amount is positive.
    """
    amount: str | float | Decimal = Field(..., description="Monetary amount (accepts string, float, or Decimal)")
    
    @validator("amount", pre=True)
    def validate_and_convert_amount(cls, v):
        """
        Convert amount to Decimal safely and validate it's positive.
        Accepts string, float, or Decimal input.
        """
        if v is None:
            raise ValueError("Amount cannot be None")
        
        try:
            decimal_value = Decimal(str(v))
        except (InvalidOperation, ValueError, TypeError):
            raise ValueError(f"Invalid amount value: {v}. Must be a valid number.")
        
        if decimal_value <= 0:
            raise ValueError(f"Amount must be positive, got: {decimal_value}")
        
        return decimal_value


class DisbursementUpdate(BaseModel):
    """
    Schema for partial updates to disbursement records.
    All fields optional; amount normalization applied if provided.
    """
    subsidy_id: Optional[int] = Field(None, ge=1, description="ID of the related subsidy")
    amount: Optional[str | float | Decimal] = Field(None, description="Monetary amount (accepts string, float, or Decimal)")
    currency: Optional[str] = Field(None, min_length=3, max_length=3, description="ISO 4217 currency code")
    reference: Optional[str] = Field(None, max_length=255, description="External transaction/reference id")
    date: Optional[datetime] = Field(None, description="Timestamp of disbursement")
    notes: Optional[str] = Field(None, description="Optional notes")
    
    @validator("amount", pre=True)
    def validate_and_convert_amount(cls, v):
        """
        Convert amount to Decimal safely and validate it's positive if provided.
        Accepts string, float, or Decimal input.
        """
        if v is None:
            return v
        
        try:
            decimal_value = Decimal(str(v))
        except (InvalidOperation, ValueError, TypeError):
            raise ValueError(f"Invalid amount value: {v}. Must be a valid number.")
        
        if decimal_value <= 0:
            raise ValueError(f"Amount must be positive, got: {decimal_value}")
        
        return decimal_value
    
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


class Disbursement(DisbursementBase):
    """
    Full disbursement record schema returned by API endpoints.
    Read-only model with auto-generated fields like id and created_at.
    """
    id: int
    created_at: datetime
    
    class Config:
        orm_mode = True
        from_attributes = True


__all__ = ["DisbursementBase", "DisbursementCreate", "DisbursementUpdate", "Disbursement"]

# Example: DisbursementCreate(subsidy_id=1, amount="10000.50", currency="INR", reference="TX123")