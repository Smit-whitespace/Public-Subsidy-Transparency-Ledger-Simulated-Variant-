"""
backend/config.py

Application settings loaded from environment (Pydantic BaseSettings). Provides a typed Settings class and a ready-to-import settings instance.
"""

from __future__ import annotations
from typing import Optional, Dict, Any
from pydantic import BaseSettings, Field, validator, AnyUrl
import os


# Reminder: do not commit SECRET_KEY or other secrets into VCS


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables and .env file.
    
    All settings are typed and validated. Sensitive values can be masked
    for safe logging/debugging using the masked() or as_dict() methods.
    """
    
    # Application metadata
    APP_NAME: str = Field("subsidy-ledger", description="Application name")
    ENVIRONMENT: str = Field("development", description="Runtime environment, e.g., development|staging|production")
    
    # Database configuration
    DATABASE_URL: AnyUrl = Field(..., description="Sync DB URL, e.g., postgresql://user:pass@host:5432/db")
    ASYNC_DATABASE_URL: Optional[AnyUrl] = Field(None, description="Optional async DB URL (e.g., postgresql+asyncpg://...)")
    DATABASE_MIN_POOL_SIZE: int = Field(1, description="DB pool min size")
    DATABASE_MAX_POOL_SIZE: int = Field(10, description="DB pool max size")
    
    # Security & JWT
    SECRET_KEY: str = Field(..., description="Secret key for signing (must be set in production)")
    JWT_ALGORITHM: str = Field("HS256", description="JWT signing algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(60, description="Default access token expiry in minutes")
    
    # Logging configuration
    LOG_LEVEL: str = Field("INFO", description="Logging level")
    LOG_AS_JSON: bool = Field(False, description="Whether logs should be formatted as JSON")
    
    # Blockchain / external services (optional)
    BLOCKCHAIN_RPC: Optional[str] = Field(None, description="Blockchain RPC URL (optional)")
    CONTRACT_ADDRESS: Optional[str] = Field(None, description="Optional on-chain contract address for proofs")
    REDIS_URL: Optional[str] = Field(None, description="Optional Redis URL for caching/queues")
    SENTRY_DSN: Optional[str] = Field(None, description="Optional Sentry DSN")
    
    # CORS configuration
    ALLOW_ORIGINS: Optional[str] = Field(None, description="Comma-separated CORS origins (optional)")
    
    class Config:
        """Pydantic configuration for Settings."""
        env_file = ".env"
        case_sensitive = True
        env_file_encoding = "utf-8"
    
    @validator("DATABASE_URL", pre=True)
    def validate_database_url(cls, v):
        """
        Normalize DATABASE_URL from environment.
        
        Allows fallback to os.getenv and converts empty strings to None
        so Pydantic can properly validate required fields.
        """
        if v is None or v == "":
            # Try to get from environment directly as fallback
            fallback = os.getenv("DATABASE_URL")
            if fallback:
                return fallback
            # Return None to trigger Pydantic's required field validation
            return None
        return v
    
    @validator("SECRET_KEY")
    def validate_secret_key(cls, v, values):
        """
        Validate SECRET_KEY length in non-development environments.
        
        Requires at least 32 characters for production/staging to ensure
        adequate cryptographic strength.
        """
        environment = values.get("ENVIRONMENT", "development")
        
        # In non-development environments, enforce strong secret key
        if environment != "development":
            if not v or len(v) < 32:
                raise ValueError(
                    "SECRET_KEY must be at least 32 characters in production. "
                    "Generate a strong random key for production use."
                )
        
        return v
    
    def _mask_value(self, value: str, show_chars: int = 4) -> str:
        """
        Mask sensitive string value for safe logging.
        
        Shows first and last few characters with asterisks in between.
        
        Args:
            value: String to mask
            show_chars: Number of characters to show at start/end
        
        Returns:
            Masked string
        """
        if not value or len(value) <= show_chars * 2:
            return "<masked>"
        
        return f"{value[:show_chars]}{'*' * (len(value) - show_chars * 2)}{value[-show_chars:]}"
    
    def masked(self) -> Dict[str, Any]:
        """
        Return settings dict with sensitive fields masked.
        
        Masks SECRET_KEY, DATABASE_URL, SENTRY_DSN and other sensitive values
        for safe logging and debugging.
        
        Returns:
            Dict with sensitive values masked
        """
        data = self.dict()
        
        # Mask SECRET_KEY
        if data.get("SECRET_KEY"):
            data["SECRET_KEY"] = self._mask_value(data["SECRET_KEY"])
        
        # Mask DATABASE_URL (show only scheme and host if possible)
        if data.get("DATABASE_URL"):
            try:
                url = str(data["DATABASE_URL"])
                # Simple masking - show scheme and host only
                if "@" in url:
                    parts = url.split("@")
                    data["DATABASE_URL"] = f"{parts[0].split('//')[0]}//<masked>@{parts[1]}"
                else:
                    data["DATABASE_URL"] = "<masked>"
            except Exception:
                data["DATABASE_URL"] = "<masked>"
        
        # Mask SENTRY_DSN
        if data.get("SENTRY_DSN"):
            data["SENTRY_DSN"] = self._mask_value(data["SENTRY_DSN"])
        
        # Mask ASYNC_DATABASE_URL
        if data.get("ASYNC_DATABASE_URL"):
            try:
                url = str(data["ASYNC_DATABASE_URL"])
                if "@" in url:
                    parts = url.split("@")
                    data["ASYNC_DATABASE_URL"] = f"{parts[0].split('//')[0]}//<masked>@{parts[1]}"
                else:
                    data["ASYNC_DATABASE_URL"] = "<masked>"
            except Exception:
                data["ASYNC_DATABASE_URL"] = "<masked>"
        
        return data
    
    def as_dict(self, *, mask_sensitive: bool = True) -> Dict[str, Any]:
        """
        Export settings as dictionary.
        
        Args:
            mask_sensitive: If True, masks sensitive fields for safe logging
        
        Returns:
            Settings dictionary with optional masking
        """
        if mask_sensitive:
            return self.masked()
        
        return self.dict(exclude_none=True)


# Create singleton settings instance
# WARNING: settings reads env at import time — import early in your app startup.
settings: Settings = Settings()


__all__ = ["Settings", "settings"]