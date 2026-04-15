"""
backend/schemas/user.py

Pydantic schemas for user operations: registration, update, and read models.
Responses must not include sensitive fields like hashed passwords.
"""

from __future__ import annotations
from typing import Optional, List
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class UserBase(BaseModel):
    """
    Base schema containing shared fields for user payloads.
    """
    username: str = Field(..., min_length=1, max_length=150, description="Unique username")


class UserCreate(UserBase):
    """
    Schema for user registration (POST body).
    Accepts plain-text password which will be hashed before storing.
    SECURITY: Raw password must never be returned in any response.
    """

    password: str = Field(..., min_length=6, max_length=256, description="Plain-text password")
    role: Optional[str] = Field("auditor", description="Role to assign")

    @field_validator("username")
    @classmethod
    def normalize_username(cls, v: str):
        if v is None:
            raise ValueError("Username cannot be None")

        normalized = v.strip().lower()

        if not normalized:
            raise ValueError("Username cannot be empty after stripping whitespace")

        return normalized

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str):
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
    """

    username: Optional[str] = Field(None, min_length=1, max_length=150)
    password: Optional[str] = Field(None, min_length=6, max_length=256)

    @field_validator("username")
    @classmethod
    def normalize_username(cls, v: Optional[str]):
        if v is None:
            return v

        normalized = v.strip().lower()

        if not normalized:
            raise ValueError("Username cannot be empty after stripping whitespace")

        return normalized

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: Optional[str]):
        if v is None:
            return v

        if not v.strip():
            raise ValueError("Password cannot be empty or whitespace only")

        if len(v.strip()) < 6:
            raise ValueError("Password must be at least 6 characters long")

        return v


class UserRead(BaseModel):
    """
    Safe API read model for user responses.
    SECURITY: Must NOT include hashed_password.
    """

    id: int
    username: str
    created_at: datetime
    roles: List[str] = []

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_with_roles(cls, user):
        return cls(
            id=user.id,
            username=user.username,
            created_at=user.created_at,
            roles=[role.name for role in getattr(user, "roles", [])],
        )


class UserPublic(BaseModel):
    """
    Minimal public view of user for public endpoints.
    """

    id: int
    username: str

    class Config:
        from_attributes = True


__all__ = ["UserBase", "UserCreate", "UserUpdate", "UserRead", "UserPublic"]