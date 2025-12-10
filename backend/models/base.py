"""
backend/models/base.py

Shared base utilities for all SQLAlchemy models in this FastAPI application.

This module imports the declarative Base from our database connection module and provides
a reusable mixin class that adds common timestamp columns to all domain models. It also
includes a helper function for development-time table creation.

Why this module exists:
- Provides a single import point for Base to avoid circular import issues
- Defines common patterns (timestamps, serialization) that all models should follow
- Works seamlessly with Alembic autogeneration by re-exporting the shared Base

For Alembic configuration:
In your alembic/env.py file, use these lines to enable autogeneration:

    from backend.models.base import Base
    target_metadata = Base.metadata

Then import all your model classes before Alembic scans (typically in backend/models/__init__.py):

    # Example: from backend.models.user import User
    # Example: from backend.models.subsidy import Subsidy
    # This ensures all tables are registered with Base.metadata for migration detection

Production note: Use Alembic migrations for schema changes, not create_all_tables().
"""

from datetime import datetime
from typing import Any, List

from sqlalchemy import Column, Integer, DateTime, func, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Mapped, mapped_column

# Import the shared declarative Base that all models inherit from. This Base is
# configured in backend.database.connection with the engine and session factory.
from backend.database.connection import Base


__all__ = ["Base", "BaseModelMixin", "create_all_tables"]


class BaseModelMixin:
    """
    A mixin class that adds standard columns to all domain models.
    
    This mixin provides three essential columns that should appear on virtually every
    table in the system: a primary key id, and automatic timestamps for creation and
    last modification. The database server handles timestamp values to ensure consistency
    across application instances and avoid clock synchronization issues.
    
    Usage example:
        class User(Base, BaseModelMixin):
            __tablename__ = "users"
            email: Mapped[str] = mapped_column(String(255), unique=True)
            # Now User automatically has id, created_at, and updated_at columns
    
    The to_dict() method provides basic serialization for API responses. For complex
    models with relationships or sensitive fields, consider using Pydantic schemas
    instead of relying on this simple implementation.
    """
    
    # The primary key column uses Integer for simplicity and broad database compatibility.
    # For high-scale applications generating millions of records, consider BigInteger or
    # UUID types instead. The index is implicit on primary keys but mentioned here for clarity.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    
    # Timestamp marking when this record was first inserted into the database. The
    # server_default means the database itself sets this value, which is more reliable
    # than depending on application code to remember to set it correctly.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    # Timestamp marking the most recent UPDATE operation on this record. The onupdate
    # parameter tells SQLAlchemy to include this column in the SET clause of UPDATE
    # statements, triggering the database's NOW() function. The server_default ensures
    # it gets initialized correctly during INSERT operations.
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    
    def to_dict(self) -> dict[str, Any]:
        """
        Convert this model instance to a JSON-serializable dictionary.
        
        This method iterates over all mapped columns and extracts their current values,
        handling datetime objects by converting them to ISO 8601 formatted strings. This
        naive implementation works well for simple models with basic column types.
        
        For production APIs with complex serialization requirements (nested relationships,
        field exclusions, computed properties, etc.), replace this with Pydantic response
        models that give you fine-grained control over the serialization process.
        
        Returns:
            A dictionary mapping column names to their serialized values, suitable for
            JSON encoding in API responses.
        """
        # The inspect function from SQLAlchemy gives us access to the mapper, which knows
        # about all the columns defined on this model class. We iterate through them and
        # pull out the current value for each one.
        result = {}
        inspector = inspect(self)
        
        for column in inspector.mapper.column_attrs:
            value = getattr(self, column.key)
            
            # DateTime objects need special handling because they're not natively JSON
            # serializable. We convert them to ISO 8601 strings which are widely supported
            # and human-readable. Other types (int, str, bool, None) pass through as-is.
            if isinstance(value, datetime):
                result[column.key] = value.isoformat()
            else:
                result[column.key] = value
        
        return result


def create_all_tables(engine: Engine) -> List[str]:
    """
    Create all tables registered with Base.metadata in the target database.
    
    This function is useful during local development, testing, or initial prototyping
    when you want to quickly materialize your model schema without running migrations.
    It's safe to call multiple times because SQLAlchemy only issues CREATE TABLE
    statements for tables that don't already exist.
    
    Important: In production environments, always use Alembic migrations instead of this
    function. Migrations provide version control for schema changes, allow rollbacks,
    and create an audit trail of how your database structure evolved over time.
    
    Args:
        engine: A SQLAlchemy Engine instance connected to your target database. This
                should be the same engine used throughout the application for consistency.
    
    Returns:
        A list of table names that are now registered in Base.metadata. This includes
        both newly created tables and any that already existed in the database.
    """
    # The create_all method scans Base.metadata for all Table objects and issues CREATE
    # TABLE statements for any that don't exist in the database yet. It's idempotent and
    # safe to run repeatedly.
    Base.metadata.create_all(bind=engine)
    
    # Return the list of table names so the caller can verify what's been registered.
    # This is helpful for debugging when tables mysteriously don't appear (usually because
    # the model class wasn't imported before calling create_all).
    return list(Base.metadata.tables.keys())


# This block demonstrates standalone usage of create_all_tables for local development.
# Running this file directly with "python -m backend.models.base" will create all tables
# and print their names. It's non-destructive and safe to run multiple times.
if __name__ == "__main__":
    # Import the configured engine from our database connection module. Make sure your
    # DATABASE_URL environment variable is set to a valid connection string before running.
    from backend.database.connection import engine
    
    print("Attempting to create all tables defined in Base.metadata...")
    print("(This is safe - tables that already exist will be skipped)\n")
    
    # Call our helper function to create tables and get back the list of names
    table_names = create_all_tables(engine)
    
    if table_names:
        print(f"Successfully verified {len(table_names)} table(s) in metadata:")
        for name in table_names:
            print(f"  - {name}")
    else:
        print("Warning: No tables found in Base.metadata!")
        print("\nThis usually means you haven't imported your model classes yet.")
        print("Remember: Models must be imported for SQLAlchemy to register them.")
        print("\nExample imports you might need:")
        print("  from backend.models.user import User")
        print("  from backend.models.subsidy import Subsidy")
        print("  from backend.models.audit import AuditRecord")