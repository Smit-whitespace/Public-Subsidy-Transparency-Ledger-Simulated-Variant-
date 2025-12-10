"""
backend/schemas/auth.py

Pydantic schemas for authentication: tokens, token payloads, and login/register request/response shapes.
"""

from __future__ import annotations
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field, validator


class Token(BaseModel):
    """
    JWT token response schema.
    Contains the access token string and token type.
    """
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """
    Decoded JWT token payload schema.
    Used for validating and typing decoded token contents.
    """
    user_id: Optional[int] = None
    username: Optional[str] = None
    exp: Optional[datetime] = None
    
    @validator("exp")
    def validate_expiration(cls, v):
        """Ensure expiration timestamp is in the future if provided."""
        if v is not None and v < datetime.utcnow():
            raise ValueError("Token expiration must be in the future")
        return v
    
    class Config:
        orm_mode = True
        from_attributes = True


class LoginRequest(BaseModel):
    """
    Schema for login endpoint request body.
    Validates and normalizes username and password inputs.
    """
    username: str = Field(..., min_length=1, max_length=150)
    password: str = Field(..., min_length=6, max_length=256)
    
    @validator("username")
    def normalize_username(cls, v):
        """Strip whitespace and convert username to lowercase."""
        if not v or not v.strip():
            raise ValueError("Username cannot be empty or whitespace only")
        return v.strip().lower()
    
    @validator("password")
    def validate_password(cls, v):
        """Ensure password is not whitespace-only."""
        if not v or not v.strip():
            raise ValueError("Password cannot be empty or whitespace only")
        return v


class RegisterRequest(LoginRequest):
    """
    Schema for user registration endpoint.
    Inherits login fields and adds optional admin flag.
    
    Note: This is a simple V1 implementation. Production systems typically
    require additional fields (email, email verification, etc.) and stricter validation.
    """
    is_admin: Optional[bool] = False


class AuthResponse(BaseModel):
    """
    Unified authentication response schema.
    
    Contains non-sensitive user information and access token.
    Security note: Never include password or password hash in the user dict.
    The user dict should contain only safe fields like: id, username, is_admin.
    """
    user: Dict[str, Any]
    token: Token


__all__ = ["Token", "TokenPayload", "LoginRequest", "RegisterRequest", "AuthResponse"]

# Example: LoginRequest(username="alice", password="s3cret")