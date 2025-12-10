"""
backend/models/subsidy.py

Defines the authoritative Subsidy model for tracking government grants and subsidy programs.

This model serves as the central record for all subsidy allocations in the system. Each subsidy
represents a financial commitment or grant that has been approved and authorized, along with its
associated metadata, timeline, and administrative details. The model is designed to support both
internal business operations and external audit trails, providing a reliable source of truth for
all subsidy-related queries and reporting.

The design prioritizes financial precision and data integrity, using proper decimal types for
monetary values and maintaining comprehensive audit timestamps. The flexible metadata field allows
for extensibility without requiring schema migrations for every new attribute, though production
systems should consider migrating to JSONB for performance when querying nested data becomes common.

Schema changes should always be applied via Alembic migrations rather than using create_all in
production environments to ensure proper version control and rollback capabilities for your
database evolution.
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
    Represents an authorized subsidy or grant allocation in the system.
    
    This model captures the essential information about government subsidies including the
    authorized amount, recipient details, validity period, and associated metadata. Each subsidy
    record represents a formal financial commitment that may later be disbursed in one or more
    installments tracked separately in the Disbursement model.
    
    Financial precision is critical in this model. We use SQLAlchemy's Numeric type paired with
    Python's Decimal class to ensure exact decimal arithmetic without the rounding errors that
    would occur with floating-point numbers. This is essential for government financial systems
    where even small discrepancies can cause serious compliance and auditing issues. Always store
    monetary amounts in Numeric columns and work with Decimal objects in Python code, never floats.
    
    The metadata field stores optional JSON-stringified data as Text for maximum database
    compatibility during development. For production systems using PostgreSQL, consider migrating
    this field to JSONB type to enable efficient querying and indexing of specific metadata
    attributes without needing to parse the entire JSON string in application code.
    
    The proof_id field provides an optional reference to blockchain-based proof records. Since
    blockchain writes are asynchronous and may fail or be delayed, this field remains nullable
    and should be populated by a separate background service that manages the actual chain
    interactions. This service should maintain a mapping table between subsidy records and their
    corresponding on-chain transaction hashes or proof identifiers for verification purposes.
    
    Example usage in the REPL for local testing:
        subsidy = Subsidy(title="Rural Infrastructure Grant 2024", recipient="District Council XYZ", amount=Decimal("100000.00"), currency="INR")
    """
    
    __tablename__ = "subsidies"
    
    # Primary key for this subsidy record. The index is implicit on primary keys but we
    # document it explicitly for clarity about query performance characteristics.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    
    # Short human-readable title identifying this subsidy. We index this field because subsidy
    # listings and search operations often filter or sort by title, and the index significantly
    # speeds up those queries especially as the subsidy catalog grows over time.
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Name or identifier of the subsidy recipient. This might be an individual beneficiary,
    # an organization, a district council, or any other entity receiving the grant. We index
    # this field to enable fast lookups like "show me all subsidies for recipient X" which is
    # a common query pattern in reporting and audit workflows.
    recipient: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # The authorized monetary amount for this subsidy. We use Numeric(18, 2) which provides
    # 18 total digits with 2 decimal places, sufficient for most currency values while
    # maintaining exact decimal precision. NEVER use Float for money - floating-point arithmetic
    # introduces rounding errors that accumulate over time and can cause serious discrepancies
    # in financial reports. Always pair SQLAlchemy's Numeric type with Python's Decimal class
    # for all monetary calculations to ensure accuracy down to the smallest currency unit.
    amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=2),
        nullable=False
    )
    
    # ISO 4217 three-letter currency code (e.g., "INR", "USD", "EUR"). We default to INR since
    # this appears to be an Indian government subsidy system, but the field supports any valid
    # currency code to enable international grants or multi-currency programs. The String(3)
    # constraint matches the ISO standard length for currency codes.
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="INR"
    )
    
    # Detailed description of the subsidy's purpose, scope, eligibility criteria, or other
    # relevant information. Using Text rather than String allows for arbitrarily long descriptions
    # without worrying about length limits, which is appropriate for government documentation
    # that may need to capture substantial detail about program requirements and objectives.
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Flexible JSON-stringified metadata field for storing additional subsidy attributes that
    # don't warrant their own dedicated columns. This might include program-specific fields,
    # approval workflow data, compliance markers, or integration details with external systems.
    # Currently stored as Text for database portability, but if you need to query or index
    # specific fields within this JSON (e.g., "find all subsidies where metadata.program_year = 2024"),
    # migrate to PostgreSQL's JSONB type which provides efficient querying with GIN indexes
    # and supports native JSON path operations without parsing the entire string.
    metadata: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Simple boolean flag indicating whether this subsidy is currently active. This supports
    # soft-deletion patterns where you want to hide subsidies from normal queries without
    # actually removing historical records from the database. The server_default ensures new
    # subsidies are active by default unless explicitly marked otherwise at creation time.
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="true"
    )
    
    # Optional reference to an on-chain proof identifier or transaction hash for subsidies that
    # have been recorded on a blockchain for transparency and immutability. This field is nullable
    # because blockchain writes are asynchronous, may fail, or might not be required for all
    # subsidy types. A separate background service should manage the actual chain interactions
    # and populate this field once proof is successfully recorded. That service should maintain
    # a comprehensive mapping table with transaction hashes, block numbers, and verification
    # status for full auditability of the blockchain proof lifecycle.
    proof_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # The date and time when this subsidy becomes valid or was officially approved. Using
    # DateTime with timezone awareness ensures that subsidy timelines are unambiguous even
    # when administrators or beneficiaries are in different time zones. Nullable to support
    # subsidies that are created before formal approval dates are determined.
    start_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # The date and time when this subsidy expires or reaches the end of its validity period.
    # Together with start_date, this defines the active window during which the subsidy can
    # be disbursed or claimed. Also timezone-aware to avoid ambiguity in distributed systems.
    end_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Timestamp marking when this subsidy record was first created in the database. The
    # server_default ensures the database itself sets this value automatically on INSERT,
    # providing a reliable audit trail that doesn't depend on application code remembering
    # to set timestamps correctly. This is crucial for government systems where creation
    # timestamps may have legal or compliance significance.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Timestamp marking the most recent update to this subsidy record. The onupdate parameter
    # tells SQLAlchemy to include this column in UPDATE statements with a new timestamp from
    # the database server, and the server_default ensures it gets initialized correctly during
    # INSERT operations. This provides automatic tracking of when subsidy information was last
    # modified, which is valuable for audit trails and change detection.
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    def amount_as_decimal(self) -> Decimal:
        """
        Return the subsidy amount as a Python Decimal object for precise calculations.
        
        This convenience method ensures you always get a proper Decimal instance when working
        with the subsidy amount, which is critical for financial calculations that require
        exact decimal precision. While SQLAlchemy already returns Decimal for Numeric columns,
        this method makes the type guarantee explicit and provides a clear API for business
        logic code that needs to perform arithmetic with subsidy amounts.
        
        Never convert these values to float for calculations, as floating-point arithmetic
        introduces rounding errors that violate financial precision requirements.
        
        Returns:
            The subsidy amount as a Decimal, suitable for exact arithmetic operations without
            precision loss or rounding errors.
        """
        # The amount column is already stored as Decimal by SQLAlchemy, but we explicitly
        # construct a new Decimal from its string representation to guarantee the type and
        # make the contract clear to calling code.
        return Decimal(str(self.amount))
    
    def duration_days(self) -> Optional[int]:
        """
        Calculate the duration of the subsidy validity period in calendar days.
        
        This convenience method computes the integer number of days between the subsidy's
        start_date and end_date, which is useful for reporting on subsidy timelines, analyzing
        program durations, and detecting subsidies that may be expiring soon. The calculation
        counts calendar days including weekends and holidays, not business days.
        
        The method only works if both start_date and end_date are populated. If either is
        missing (for example, a subsidy might be created before formal dates are assigned),
        this method returns None rather than making assumptions or raising an error.
        
        Returns:
            The number of calendar days between start and end dates as an integer, or None
            if either date is not set. A negative result indicates the end date is before
            the start date, which may represent a data quality issue.
        """
        # Check if both dates are present before attempting calculation. This guard prevents
        # TypeErrors and makes the behavior predictable when dates are missing.
        if self.start_date is not None and self.end_date is not None:
            # Calculate the timedelta between the two dates and extract the days component.
            # The timedelta.days attribute gives us the integer number of whole days, which
            # is appropriate for most subsidy duration reporting and analysis use cases.
            delta = self.end_date - self.start_date
            return delta.days
        
        # Return None if we can't calculate duration, signaling to calling code that the
        # duration is unavailable rather than returning zero which could be misleading.
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert this subsidy record to a JSON-serializable dictionary for API responses.
        
        This method transforms the ORM model into a plain Python dictionary suitable for
        returning from API endpoints, logging to external systems, or serialization to JSON
        format. Special handling is applied to types that aren't natively JSON-serializable:
        
        - Decimal amounts are converted to strings to preserve exact precision and avoid
          JavaScript's number type limitations (which uses floating-point internally)
        - Datetime fields are converted to ISO 8601 formatted strings which are widely
          supported and human-readable across different systems and time zones
        
        The metadata field is included as-is without parsing, since it's stored as a string
        and may not always contain valid JSON. Calling code can parse it if needed for their
        specific use case.
        
        Returns:
            A dictionary containing all subsidy fields in JSON-compatible formats, ready for
            serialization with json.dumps() or FastAPI's automatic JSON encoding.
        """
        return {
            "id": self.id,
            "title": self.title,
            "recipient": self.recipient,
            # Convert Decimal to string to preserve exact decimal precision in JSON output.
            # JavaScript's number type uses IEEE 754 floating-point which can't represent
            # all decimal values exactly, so we send amounts as strings to avoid any loss
            # of precision on the client side. The string "100000.00" is unambiguous and
            # can be parsed back into exact decimal representation in any language.
            "amount": str(self.amount),
            "currency": self.currency,
            "description": self.description,
            # Include metadata as-is without parsing, since it's stored as a string and may
            # not always be valid JSON. API consumers can parse it if needed.
            "metadata": self.metadata,
            "is_active": self.is_active,
            "proof_id": self.proof_id,
            # Convert datetime fields to ISO 8601 strings for consistent JSON representation
            # across different systems and programming languages. The isoformat() method
            # produces strings like "2024-03-15T14:30:00+00:00" which clearly communicate
            # both the date/time and timezone information, avoiding ambiguity.
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


# Composite index to accelerate queries that filter by recipient and active status together,
# which is a common pattern in queries like "show me all active subsidies for recipient X".
# This index allows the database to quickly locate relevant rows without scanning the entire
# table, which becomes increasingly important as the subsidy catalog grows over time.
Index("ix_subsidies_recipient_active", Subsidy.recipient, Subsidy.is_active)