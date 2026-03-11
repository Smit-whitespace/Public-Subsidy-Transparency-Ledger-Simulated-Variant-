"""
backend/models/project.py

Defines the Project model for tracking projects associated with subsidy programs.

Projects represent specific initiatives, programs, or activities that are funded or supported
by subsidies. Each project can be linked to a parent subsidy and tracks key metadata like
timeline, ownership, status, and descriptive information. This model supports planning,
execution tracking, and reporting on subsidy-funded initiatives.

The model uses ondelete="SET NULL" on the subsidy foreign key to preserve project records
even if the parent subsidy is deleted, maintaining historical data for audit and reporting
purposes. This is a common pattern in financial and government systems where you need to
maintain complete records of all activities regardless of whether parent entities are removed.

Schema changes should always be applied via Alembic migrations rather than using create_all
in production environments to ensure proper version control and rollback capabilities.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.connection import Base


__all__ = ["Project"]


class Project(Base):
    """
    Represents a project or initiative funded or supported by a subsidy program.
    
    This model captures the essential information about projects including their relationship
    to subsidies, timeline, ownership, and current status. Projects are the concrete activities
    or programs that subsidies enable, and tracking them separately allows for detailed
    reporting on how subsidy funds are being utilized.
    
    The subsidy_id foreign key uses ondelete="SET NULL" so that project records remain in the
    database for historical reference even if the parent subsidy is removed from the system.
    This design choice prioritizes data retention and audit capabilities over strict referential
    integrity, which is appropriate for government and financial record-keeping.
    
    The metadata field stores additional JSON-stringified data as Text for flexibility. If you
    need to query or index specific fields within the metadata, consider migrating to PostgreSQL's
    JSONB type which supports efficient querying and indexing of JSON structure. For now, Text
    keeps the model compatible with multiple database backends during development.
    
    The status field currently uses a simple string, but consider migrating to a proper SQLAlchemy
    Enum type or a separate status reference table as the application matures and status values
    become more formalized across the team.
    
    Example usage in the REPL:
        project = Project(name="Rural Electrification Phase 2", subsidy_id=1, status="active")
    """
    
    __tablename__ = "projects"
    
    # Primary key for this project record. The index is implicit on primary keys but we
    # document it explicitly for clarity about query performance characteristics.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    
    # The human-readable name of the project. We index this field because project listings
    # and searches often filter or sort by name, and the index significantly speeds up those
    # operations especially as the project catalog grows over time.
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Foreign key linking this project to its parent subsidy. The ondelete="SET NULL" behavior
    # means that if the subsidy record is deleted, this project's subsidy_id becomes NULL rather
    # than cascading the deletion to the project itself. This preserves the complete historical
    # record of all projects that were ever created, which is important for auditing, reporting,
    # and compliance purposes in government and financial systems. The index accelerates queries
    # like "find all projects for subsidy #42".
    subsidy_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("subsidies.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Detailed description of the project's purpose, scope, and objectives. Using Text rather
    # than String allows for arbitrarily long descriptions without worrying about length limits,
    # which is appropriate for project documentation that may be quite detailed.
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Flexible JSON-stringified metadata field for storing additional project attributes that
    # don't warrant their own columns. This might include custom fields, integration data, or
    # application-specific configuration. Currently stored as Text for database portability, but
    # if you need to query or index specific fields within this JSON, consider migrating to
    # PostgreSQL's JSONB type which provides efficient querying and GIN indexing capabilities.
    meta_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Identifier of the department, organization, or individual that owns or manages this project.
    # This is stored as a flexible string rather than a foreign key to avoid creating tight coupling
    # to a specific user or department model, giving you flexibility in how ownership is tracked.
    owner: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # The date and time when the project started or is planned to start. Using DateTime with
    # timezone awareness ensures that project timelines are unambiguous even when team members
    # or beneficiaries are in different time zones.
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # The date and time when the project ended or is planned to end. Together with start_date,
    # this enables calculation of project duration and tracking of whether projects are completing
    # on schedule. Also timezone-aware to avoid ambiguity in distributed environments.
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Current status of the project as a short string code. Common values might include "planned",
    # "active", "completed", "paused", "cancelled". This simple string approach works well during
    # early development, but consider migrating to a SQLAlchemy Enum type or a separate status
    # reference table as your status vocabulary becomes more formalized and you want to enforce
    # valid values at the database level.
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="planned")
    
    # Timestamp marking when this project record was first created in the database. The
    # server_default ensures the database itself sets this value automatically on INSERT,
    # providing a reliable audit trail that doesn't depend on application code remembering
    # to set it correctly.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Timestamp marking the most recent update to this project record. The onupdate parameter
    # tells SQLAlchemy to include this column in UPDATE statements with a new timestamp, and
    # the server_default ensures it gets initialized correctly during INSERT operations. This
    # gives you automatic tracking of when project information was last modified.
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    def duration_days(self) -> Optional[int]:
        """
        Calculate the duration of the project in days.
        
        This convenience method computes the integer number of days between the project's
        start_date and end_date, which is useful for reporting on project timelines, detecting
        overruns, and analyzing how long different types of projects typically take to complete.
        
        The calculation only works if both start_date and end_date are populated. If either is
        missing (for example, a planned project might not have concrete dates yet, or an active
        project might not have an end date), this method returns None rather than making
        assumptions or raising an error.
        
        Returns:
            The number of days between start and end dates as an integer, or None if either
            date is not set. Note that this uses simple date subtraction which counts calendar
            days including weekends and holidays, not business days.
        """
        # Check if both dates are present before attempting to calculate the duration. This
        # guard prevents errors and makes the behavior predictable when dates are missing.
        if self.start_date is not None and self.end_date is not None:
            # Calculate the timedelta between the two dates and extract the days component.
            # The timedelta.days attribute gives us the integer number of whole days, which
            # is appropriate for most project duration reporting use cases.
            delta = self.end_date - self.start_date
            return delta.days
        
        # Return None if we can't calculate duration, signaling to calling code that the
        # duration is unavailable rather than returning a potentially misleading zero or
        # raising an exception that would need to be caught everywhere this is called.
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert this project record to a JSON-serializable dictionary.
        
        This method transforms the ORM model into a plain Python dictionary suitable for API
        responses, logging, or serialization to JSON. Special handling is applied to datetime
        fields which aren't natively JSON-serializable, converting them to ISO 8601 formatted
        strings which are widely supported and human-readable.
        
        The metadata field is included as a string rather than being parsed, since it may not
        always contain valid JSON and we don't want serialization to fail if someone stored
        malformed data. Calling code can parse the metadata string if needed.
        
        Returns:
            A dictionary containing all project fields in JSON-compatible formats.
        """
        return {
            "id": self.id,
            "name": self.name,
            "subsidy_id": self.subsidy_id,
            "description": self.description,
            "meta_data": self.meta_data,
            "owner": self.owner,
            # Convert datetime fields to ISO 8601 strings for consistent JSON representation
            # across different systems and programming languages. The isoformat() method is
            # standard and produces strings like "2024-03-15T14:30:00+00:00" which clearly
            # communicate both the date/time and timezone information.
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
