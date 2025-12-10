"""
backend/models/subsidy.py

Defines the authoritative Subsidy model representing government grants and subsidy allocations.

This model serves as the central financial record for all subsidy programs in the system. Each
subsidy represents an approved financial commitment with precise monetary amounts, recipient
details, validity periods, and administrative metadata. The model is designed to support both
operational workflows and comprehensive audit trails, providing a reliable source of truth for
all subsidy-related operations across the application.

Financial integrity is paramount in this model. We use exact decimal arithmetic throughout to
avoid the rounding errors inherent in floating-point calculations, which is critical for
government financial systems where even small discrepancies can have serious compliance and
legal implications.

Schema changes should always be applied through Alembic migrations rather than using create_all
in production to maintain proper version control and enable safe rollbacks.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional

from sqlalchemy import Boolean, Column, DateTime, Index, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.connection import Base


__all__ = ["Subsidy"]


class Subsidy(Base):
    """
    Represents an authorized government subsidy or grant allocation.
    
    This model captures the complete financial and administrative details of subsidy programs,
    including the authorized amount, recipient information, validity period, and flexible
    metadata for program-specific attributes. Each subsidy record represents a formal financial
    commitment that may be disbursed in one or multiple installments tracked separately.
    
    The design emphasizes financial precision and auditability. Monetary amounts use the Numeric
    database type paired with Python's Decimal class to ensure exact decimal arithmetic without
    the precision loss that occurs with floating-point numbers. This is essential for government
    financial systems where accuracy is both a legal requirement and a matter of public trust.
    
    The metadata field provides extensibility for program-specific attributes without requiring
    schema migrations for every new field. For production PostgreSQL deployments, consider
    migrating this to JSONB type if you need to query or index specific metadata attributes,
    as JSONB supports efficient JSON operations and GIN indexing.
    
    The proof_id field supports optional integration with blockchain-based proof systems for
    transparency and immutability. Since blockchain writes are asynchronous and may fail, this
    field remains nullable and should be populated by a separate service that manages the
    on-chain recording process and maintains verification mappings.
    
    Example REPL usage for testing:
        subsidy = Subsidy(title="Infrastructure Grant 2024", recipient="City Council", amount=Decimal("500000.00"))
    """
    
    __tablename__ = "subsidies"
    
    # Primary key identifier for this subsidy record. The index is implicit on primary keys
    # but we note it here for documentation clarity about query performance.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    
    # Human-readable title for this subsidy program. Indexed to support fast filtering and
    # sorting in subsidy listing and search operations.
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Name or identifier of the subsidy recipient, whether an individual, organization, or
    # government entity. Indexed because queries frequently filter by recipient.
    recipient: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Authorized monetary amount for this subsidy. We use Numeric(18,2) with Python's Decimal
    # class to maintain exact decimal precision for financial calculations. Never use float
    # for money as it introduces rounding errors that accumulate and violate financial accuracy
    # requirements in government systems.
    amount: Mapped[Decimal] = mapped_column(Numeric(precision=18, scale=2), nullable=False)
    
    # ISO 4217 three-letter currency code (INR, USD, EUR, etc). Defaults to INR for Indian
    # subsidy programs but supports any valid currency for international or multi-currency grants.
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    
    # Detailed description of the subsidy's purpose, scope, eligibility criteria, and other
    # relevant documentation. Text type allows unlimited length for comprehensive documentation.
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Flexible JSON-stringified metadata for program-specific attributes that don't warrant
    # dedicated columns. Stored as Text for database portability, but consider migrating to
    # PostgreSQL JSONB if you need to query or index specific metadata fields efficiently.
    metadata: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Boolean flag indicating whether this subsidy is currently active. Supports soft-deletion
    # patterns where subsidies are hidden from normal operations without losing historical data.
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    
    # Optional reference to blockchain proof identifier for subsidies recorded on-chain for
    # transparency and immutability. Nullable because blockchain writes are asynchronous and
    # optional. A separate service should manage the actual chain interactions and maintain
    # verification mappings between subsidy records and on-chain proof hashes.
    proof_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Start of the subsidy validity period. Timezone-aware to avoid ambiguity across different
    # geographic locations. Nullable to support subsidies created before formal dates are set.
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # End of the subsidy validity period. Together with start_date, defines the window during
    # which the subsidy can be disbursed or claimed. Also timezone-aware for consistency.
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Timestamp when this subsidy record was first created. Server default ensures the database
    # sets this automatically on INSERT, providing reliable audit trails independent of
    # application code correctness.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    
    # Timestamp of the most recent update to this subsidy. The onupdate parameter triggers
    # automatic timestamp updates on every UPDATE statement, and server_default initializes
    # it correctly during INSERT. This provides automatic change tracking for audit purposes.
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    
    def amount_as_decimal(self) -> Decimal:
        """
        Return the subsidy amount as a Python Decimal object for precise financial calculations.
        
        This method ensures you always work with exact decimal precision when performing
        calculations involving subsidy amounts. While SQLAlchemy already returns Decimal for
        Numeric columns, this method makes the type contract explicit and provides a clear
        API for business logic that requires guaranteed decimal precision.
        
        Returns:
            The subsidy amount as a Decimal suitable for exact arithmetic without precision loss.
        """
        return Decimal(str(self.amount))
    
    def duration_days(self) -> Optional[int]:
        """
        Calculate the duration of the subsidy validity period in calendar days.
        
        This method computes the number of days between start_date and end_date, which is
        useful for reporting on subsidy timelines, analyzing program durations, and identifying
        subsidies approaching expiration. The calculation counts calendar days including
        weekends and holidays, not business days.
        
        Returns:
            Integer number of days between start and end dates, or None if either date is
            missing. Negative values indicate the end date precedes the start date, which
            may represent a data quality issue requiring attention.
        """
        if self.start_date is not None and self.end_date is not None:
            delta = self.end_date.date() - self.start_date.date()
            return delta.days
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert this subsidy record to a JSON-serializable dictionary for API responses.
        
        This method transforms the ORM model into a plain dictionary suitable for JSON
        serialization in API endpoints, logging systems, or external integrations. Special
        handling ensures that types not natively JSON-serializable are converted appropriately:
        
        Decimal amounts become strings to preserve exact precision and avoid JavaScript's
        floating-point number limitations. Datetime fields become ISO 8601 strings which are
        widely supported and unambiguous across time zones and systems.
        
        Returns:
            Dictionary containing all subsidy fields in JSON-compatible formats ready for
            serialization with json.dumps() or FastAPI's automatic JSON encoding.
        """
        return {
            "id": self.id,
            "title": self.title,
            "recipient": self.recipient,
            "amount": str(self.amount),
            "currency": self.currency,
            "description": self.description,
            "metadata": self.metadata,
            "is_active": self.is_active,
            "proof_id": self.proof_id,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


# Composite index to optimize queries filtering by both recipient and active status, which
# is a common pattern in queries like "show all active subsidies for recipient X". This index
# allows efficient lookups without full table scans as the subsidy catalog grows.
Index("idx_subsidy_recipient_active", Subsidy.recipient, Subsidy.is_active)