"""
backend/schemas/subsidy.py

Pydantic schemas for Subsidy entity — create/update/read shapes; normalizes monetary inputs into Decimal and accepts flexible metadata.
"""

from __future__ import annotations
from typing import Optional, Dict, Any
from decimal import Decimal, InvalidOperation
from datetime import datetime
from pydantic import BaseModel, Field, validator


class SubsidyBase(BaseModel):
    """
    Base schema for subsidy records containing shared fields.
    Monetary inputs are normalized to Decimal for safe storage.
    Used as foundation for create/update request models.
    """
    title: str = Field(..., max_length=255, description="Short human title")
    recipient: str = Field(..., max_length=255, description="Recipient name or identifier")
    amount: Decimal = Field(..., description="Authorized amount as Decimal")
    currency: str = Field("INR", min_length=3, max_length=3, description="ISO 4217 code")
    description: Optional[str] = Field(None, description="Long description")
    meta_data: Optional[str] = Field(None, description="Optional JSON string for free-form metadata")
    is_active: Optional[bool] = Field(True, description="Is the subsidy active?")
    proof_id: Optional[int] = Field(None, description="Optional on-chain proof id")
    start_date: Optional[datetime] = Field(None, description="Optional start datetime")
    end_date: Optional[datetime] = Field(None, description="Optional end datetime")


class SubsidyCreate(SubsidyBase):
    """
    Schema for creating new subsidy records.
    Server normalizes amount to Decimal and metadata to compact JSON string when provided as dict.
    Accepts amount as string, float, or Decimal and converts safely for storage.
    """
    amount: str | float | Decimal = Field(..., description="Authorized amount (accepts string, float, or Decimal)")
    
    @validator("title")
    def normalize_title(cls, v):
        """Strip whitespace from title and reject empty values."""
        if v is None:
            raise ValueError("Title cannot be None")
        stripped = v.strip()
        if not stripped:
            raise ValueError("Title cannot be empty after stripping whitespace")
        return stripped
    
    @validator("recipient")
    def normalize_recipient(cls, v):
        """Strip whitespace from recipient and reject empty values."""
        if v is None:
            raise ValueError("Recipient cannot be None")
        stripped = v.strip()
        if not stripped:
            raise ValueError("Recipient cannot be empty after stripping whitespace")
        return stripped
    
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
    
    @validator("currency", pre=True, always=True)
    def normalize_currency(cls, v):
        """Normalize currency code to uppercase and strip whitespace."""
        if v is None:
            return "INR"
        return v.strip().upper()
    
    @validator("meta_data", pre=True)
    def normalize_metadata(cls, v):
        """
        Convert metadata dict to compact JSON string.
        Accepts dict or string input; stores as string.
        """
        if v is None:
            return None
        if isinstance(v, dict):
            import json
            return json.dumps(v, separators=(",", ":"))
        if isinstance(v, str):
            return v.strip()
        return v


class SubsidyUpdate(BaseModel):
    """
    Schema for partial updates to subsidy records (PATCH operations).
    All fields optional; same normalization applied when provided.
    """
    title: Optional[str] = Field(None, max_length=255, description="Short human title")
    recipient: Optional[str] = Field(None, max_length=255, description="Recipient name or identifier")
    amount: Optional[str | float | Decimal] = Field(None, description="Authorized amount (accepts string, float, or Decimal)")
    currency: Optional[str] = Field(None, min_length=3, max_length=3, description="ISO 4217 code")
    description: Optional[str] = Field(None, description="Long description")
    meta_data: Optional[str] = Field(None, description="Optional JSON string for free-form metadata")
    is_active: Optional[bool] = Field(None, description="Is the subsidy active?")
    proof_id: Optional[int] = Field(None, description="Optional on-chain proof id")
    start_date: Optional[datetime] = Field(None, description="Optional start datetime")
    end_date: Optional[datetime] = Field(None, description="Optional end datetime")
    
    @validator("title")
    def normalize_title(cls, v):
        """Strip whitespace from title and reject empty values if provided."""
        if v is None:
            return None
        stripped = v.strip()
        if not stripped:
            raise ValueError("Title cannot be empty after stripping whitespace")
        return stripped
    
    @validator("recipient")
    def normalize_recipient(cls, v):
        """Strip whitespace from recipient and reject empty values if provided."""
        if v is None:
            return None
        stripped = v.strip()
        if not stripped:
            raise ValueError("Recipient cannot be empty after stripping whitespace")
        return stripped
    
    @validator("amount", pre=True)
    def validate_and_convert_amount(cls, v):
        """
        Convert amount to Decimal safely and validate it's positive if provided.
        Accepts string, float, or Decimal input.
        """
        if v is None:
            return None
        
        try:
            decimal_value = Decimal(str(v))
        except (InvalidOperation, ValueError, TypeError):
            raise ValueError(f"Invalid amount value: {v}. Must be a valid number.")
        
        if decimal_value <= 0:
            raise ValueError(f"Amount must be positive, got: {decimal_value}")
        
        return decimal_value
    
    @validator("currency", pre=True)
    def normalize_currency(cls, v):
        """Normalize currency code to uppercase and strip whitespace if provided."""
        if v is None:
            return None
        return v.strip().upper()
    
    @validator("meta_data", pre=True)
    def normalize_metadata(cls, v):
        """
        Convert metadata dict to compact JSON string.
        Accepts dict or string input; stores as string.
        """
        if v is None:
            return None
        if isinstance(v, dict):
            import json
            return json.dumps(v, separators=(",", ":"))
        if isinstance(v, str):
            return v.strip()
        return v


class Subsidy(SubsidyBase):
    """
    Full subsidy record schema returned by API endpoints.
    Read-only model with auto-generated fields like id, created_at, and updated_at.
    """
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True
        from_attributes = True


__all__ = ["SubsidyBase", "SubsidyCreate", "SubsidyUpdate", "Subsidy"]

# Example: SubsidyCreate(title="School Grant", recipient="District X", amount="500000.00", currency="INR")