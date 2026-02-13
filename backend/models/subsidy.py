"""
backend/models/subsidy.py
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional

from sqlalchemy import Boolean, DateTime, Index, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.connection import Base


__all__ = ["Subsidy"]


class Subsidy(Base):
    __tablename__ = "subsidies"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, index=True
    )

    title: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True
    )

    recipient: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=2), nullable=False
    )

    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, default="INR"
    )

    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # IMPORTANT: NOT metadata (reserved)
    meta_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )

    proof_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    start_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    end_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def amount_as_decimal(self) -> Decimal:
        return Decimal(str(self.amount))

    def duration_days(self) -> Optional[int]:
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "recipient": self.recipient,
            "amount": str(self.amount),
            "currency": self.currency,
            "description": self.description,
            "meta_data": self.meta_data,
            "is_active": self.is_active,
            "proof_id": self.proof_id,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


Index(
    "ix_subsidies_recipient_active",
    Subsidy.recipient,
    Subsidy.is_active,
)
