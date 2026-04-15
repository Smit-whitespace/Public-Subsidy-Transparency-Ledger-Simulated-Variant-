"""
backend/config.py

Application settings loaded from environment (Pydantic BaseSettings).
Provides a typed Settings class and a ready-to-import settings instance.
"""

from __future__ import annotations
from typing import Optional, Dict, Any
from pydantic import Field, validator, AnyUrl
from pydantic_settings import BaseSettings
import os


# Reminder: do not commit SECRET_KEY or other secrets into VCS


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables and .env file.

    All settings are typed and validated. Sensitive values can be masked
    for safe logging/debugging using the masked() or as_dict() methods.
    """

    # =========================================================
    # Application metadata
    # =========================================================

    APP_NAME: str = Field("subsidy-ledger", description="Application name")
    ENVIRONMENT: str = Field(
        "development",
        description="Runtime environment, e.g., development|staging|production"
    )
    
    # Demo Mode Control
    DEMO_MODE: bool = Field(
        True,
        description="Enable demo mode with seed data (default: True for development)"
    )

    # =========================================================
    # Database configuration
    # =========================================================

    DATABASE_URL: AnyUrl = Field(
        ...,
        description="Sync DB URL, e.g., postgresql://user:pass@host:5432/db"
    )

    ASYNC_DATABASE_URL: Optional[AnyUrl] = Field(
        None,
        description="Optional async DB URL (e.g., postgresql+asyncpg://...)"
    )

    DATABASE_MIN_POOL_SIZE: int = Field(1, description="DB pool min size")
    DATABASE_MAX_POOL_SIZE: int = Field(10, description="DB pool max size")

    # =========================================================
    # Security & JWT
    # =========================================================

    SECRET_KEY: str = Field(
        ...,
        description="Secret key for signing (must be set in production)"
    )

    JWT_ALGORITHM: str = Field(
        "HS256",
        description="JWT signing algorithm"
    )

    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        60,
        description="Default access token expiry in minutes"
    )

    # ---------------------------------------------------------
    # Compatibility aliases (used by security/auth modules)
    # ---------------------------------------------------------

    JWT_SECRET: Optional[str] = None
    JWT_EXPIRE_MINUTES: Optional[int] = None

    # =========================================================
    # Logging configuration
    # =========================================================

    LOG_LEVEL: str = Field("INFO", description="Logging level")
    LOG_AS_JSON: bool = Field(False, description="JSON logging")

    # =========================================================
    # Blockchain / external services (optional)
    # =========================================================

    BLOCKCHAIN_RPC: Optional[str] = Field(
        None,
        description="Blockchain RPC URL (optional)"
    )

    CONTRACT_ADDRESS: Optional[str] = Field(
        None,
        description="Optional on-chain contract address for proofs"
    )

    REDIS_URL: Optional[str] = Field(
        None,
        description="Optional Redis URL for caching/queues"
    )

    SENTRY_DSN: Optional[str] = Field(
        None,
        description="Optional Sentry DSN"
    )

    # =========================================================
    # CORS configuration
    # =========================================================

    ALLOW_ORIGINS: Optional[str] = Field(
        None,
        description="Comma-separated CORS origins (optional)"
    )

    # =========================================================
    # Pydantic config
    # =========================================================

    class Config:
        env_file = ".env"
        case_sensitive = True
        env_file_encoding = "utf-8"
        extra = "ignore"

    # =========================================================
    # Validators
    # =========================================================

    @validator("DATABASE_URL", pre=True)
    def validate_database_url(cls, v):
        """
        Normalize DATABASE_URL from environment.
        """
        if v is None or v == "":
            fallback = os.getenv("DATABASE_URL")
            if fallback:
                return fallback
            return None
        return v

    @validator("SECRET_KEY")
    def validate_secret_key(cls, v, values):
        """
        Validate SECRET_KEY length in non-development environments.
        """
        environment = values.get("ENVIRONMENT", "development")

        if environment != "development":
            if not v or len(v) < 32:
                raise ValueError(
                    "SECRET_KEY must be at least 32 characters in production."
                )

        return v

    # =========================================================
    # Post-init normalization
    # =========================================================

    def __init__(self, **data):
        super().__init__(**data)

        # Compatibility aliases for other modules
        if not self.JWT_SECRET:
            self.JWT_SECRET = self.SECRET_KEY

        if not self.JWT_EXPIRE_MINUTES:
            self.JWT_EXPIRE_MINUTES = self.ACCESS_TOKEN_EXPIRE_MINUTES

    # =========================================================
    # Mask helpers
    # =========================================================

    def _mask_value(self, value: str, show_chars: int = 4) -> str:
        if not value or len(value) <= show_chars * 2:
            return "<masked>"

        return f"{value[:show_chars]}{'*' * (len(value) - show_chars * 2)}{value[-show_chars:]}"

    def masked(self) -> Dict[str, Any]:
        data = self.dict()

        if data.get("SECRET_KEY"):
            data["SECRET_KEY"] = self._mask_value(data["SECRET_KEY"])

        if data.get("DATABASE_URL"):
            try:
                url = str(data["DATABASE_URL"])
                if "@" in url:
                    parts = url.split("@")
                    data["DATABASE_URL"] = f"{parts[0].split('//')[0]}//<masked>@{parts[1]}"
                else:
                    data["DATABASE_URL"] = "<masked>"
            except Exception:
                data["DATABASE_URL"] = "<masked>"

        if data.get("SENTRY_DSN"):
            data["SENTRY_DSN"] = self._mask_value(data["SENTRY_DSN"])

        if data.get("ASYNC_DATABASE_URL"):
            data["ASYNC_DATABASE_URL"] = "<masked>"

        return data

    def as_dict(self, *, mask_sensitive: bool = True) -> Dict[str, Any]:
        if mask_sensitive:
            return self.masked()

        return self.dict(exclude_none=True)


# =========================================================
# Singleton instance
# =========================================================

settings: Settings = Settings()


__all__ = ["Settings", "settings"]