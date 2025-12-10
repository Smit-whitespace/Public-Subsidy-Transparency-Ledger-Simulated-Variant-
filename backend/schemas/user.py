"""
backend/schemas/user.py

Pydantic schemas for user operations: registration, update, and read models. Responses must not include sensitive fields like hashed passwords.
"""

from __future__ import annotations
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator


class UserBase(BaseModel):
    """
    Base schema containing shared fields for user payloads.
    """
    username: str = Field(..., min_length=1, max_length=150, description="Unique username")
    is_admin: bool = Field(False, description="Admin flag")


class UserCreate(UserBase):
    """
    Schema for user registration (POST body).
    Accepts plain-text password which will be hashed before storing.
    SECURITY: Raw password must never be returned in any response.
    """
    password: str = Field(..., min_length=6, max_length=256, description="Plain-text password (will be hashed before storing)")
    
    @validator("username")
    def normalize_username(cls, v):
        """Strip whitespace and convert username to lowercase."""
        if v is None:
            raise ValueError("Username cannot be None")
        normalized = v.strip().lower()
        if not normalized:
            raise ValueError("Username cannot be empty after stripping whitespace")
        return normalized
    
    @validator("password")
    def validate_password(cls, v):
        """Ensure password is not whitespace-only and meets minimum length."""
        if v is None:
            raise ValueError("Password cannot be None")
        if not v.strip():
            raise ValueError("Password cannot be empty or whitespace only")
        if len(v.strip()) < 6:
            raise ValueError("Password must be at least 6 characters long")
        return v


class UserUpdate(BaseModel):
    """
    Schema for partial user updates (PATCH operations).
    All fields optional; changing password requires passing new password (server will hash it).
    """
    username: Optional[str] = Field(None, min_length=1, max_length=150, description="Unique username")
    password: Optional[str] = Field(None, min_length=6, max_length=256, description="Plain-text password (will be hashed before storing)")
    is_admin: Optional[bool] = Field(None, description="Admin flag")
    
    @validator("username")
    def normalize_username(cls, v):
        """Strip whitespace and convert username to lowercase if provided."""
        if v is None:
            return None
        normalized = v.strip().lower()
        if not normalized:
            raise ValueError("Username cannot be empty after stripping whitespace")
        return normalized
    
    @validator("password")
    def validate_password(cls, v):
        """Ensure password is not whitespace-only and meets minimum length if provided."""
        if v is None:
            return None
        if not v.strip():
            raise ValueError("Password cannot be empty or whitespace only")
        if len(v.strip()) < 6:
            raise ValueError("Password must be at least 6 characters long")
        return v


class UserRead(BaseModel):
    """
    Safe API read model for user responses.
    SECURITY: Must NOT include hashed_password or other sensitive data.
    """
    id: int
    username: str
    is_admin: bool
    created_at: datetime
    
    class Config:
        orm_mode = True
        from_attributes = True


class UserPublic(BaseModel):
    """
    Minimal public view of user for public-facing endpoints.
    Never include is_admin, hashed_password, or other sensitive fields.
    """
    id: int
    username: str
    
    class Config:
        orm_mode = True
        from_attributes = True


__all__ = ["UserBase", "UserCreate", "UserUpdate", "UserRead", "UserPublic"]

# Example: UserCreate(username="alice", password="s3cretP@ss")