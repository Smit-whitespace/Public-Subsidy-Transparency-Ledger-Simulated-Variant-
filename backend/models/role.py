"""
backend/models/role.py

Defines the Role model for managing user roles and permissions in the application.

Roles represent named collections of permissions that can be assigned to users to control
their access to various features and operations within the system. Each role has a canonical
name (like "admin" or "auditor"), optional display information for user interfaces, and a
flexible permissions field that stores the specific capabilities granted to users with that role.

In a larger production system, you would typically implement roles using a many-to-many
relationship with users (via an association table like user_roles) and store permissions in
a normalized table or use PostgreSQL's JSONB type for efficient querying by specific permission
values. The current implementation uses a simple Text field for permissions to maintain database
portability during development, but this should be upgraded to JSONB or a dedicated permissions
table as your permission model becomes more sophisticated.

Schema changes should always be applied via Alembic migrations rather than using create_all
in production environments to ensure proper version control and rollback capabilities.
"""

import json
from typing import Any, Dict

from sqlalchemy import Column, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.connection import Base


__all__ = ["Role"]


class Role(Base):
    """
    Represents a named role with associated permissions for access control.
    
    This model defines roles that can be assigned to users to control their access to
    different parts of the application. Each role has a unique name that serves as the
    canonical identifier, along with optional display and description fields that provide
    human-readable context about what the role represents and when it should be used.
    
    The permissions field stores a JSON-encoded string listing the specific capabilities
    or scopes that this role grants. For a simple system, this might be a JSON array like
    ["read:subsidies", "write:projects"]. For more complex permission models with hierarchies
    or fine-grained controls, consider migrating to PostgreSQL's JSONB type which supports
    efficient indexing and querying, or normalize permissions into a separate table with
    proper foreign key relationships for maximum flexibility and query performance.
    
    In production systems, roles are typically linked to users through an association table
    that implements a many-to-many relationship, since users often have multiple roles and
    roles are shared across many users. You would create a user_roles table with user_id
    and role_id foreign keys to support this pattern.
    
    Example usage in the REPL:
        role = Role(name="auditor", display_name="Financial Auditor", permissions='["read:audits", "read:disbursements"]')
    """
    
    __tablename__ = "roles"
    
    # Primary key for this role record. The index is implicit on primary keys but we
    # document it explicitly for clarity about query performance characteristics.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    
    # The canonical machine-readable name for this role. This should be a stable identifier
    # that code can reference reliably, like "admin", "auditor", "reviewer", or "viewer".
    # The unique constraint ensures no two roles can have the same name, preventing confusion
    # and potential security issues from duplicate role definitions. We use lowercase names
    # by convention to avoid case-sensitivity issues across different parts of the application.
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    
    # Human-friendly label for this role that can be displayed in user interfaces. This might
    # be a more descriptive version like "Financial Auditor" or "Project Reviewer" that makes
    # sense to non-technical users selecting or viewing role assignments. Keeping this separate
    # from the canonical name gives you flexibility to change display text without breaking
    # code that references roles by their machine name.
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Detailed explanation of what this role is for and when it should be assigned. This is
    # useful for administrators who need to understand the purpose and scope of each role when
    # making access control decisions. Using Text rather than String allows for longer
    # documentation without worrying about length limits.
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # JSON-encoded string listing the permissions or scopes that this role grants. For simple
    # systems, this might be a JSON array like ["read:subsidies", "write:projects", "approve:disbursements"].
    # The current implementation stores this as Text for database portability, but if you need
    # to query roles by specific permissions (e.g., "find all roles that grant write:projects"),
    # you should migrate to PostgreSQL's JSONB type which supports efficient GIN indexing and
    # JSON path queries. Alternatively, normalize permissions into a separate table with a
    # many-to-many relationship through role_permissions for maximum flexibility.
    permissions: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Timestamp marking when this role was first created in the database. The server_default
    # ensures the database itself sets this value automatically on INSERT, providing a reliable
    # audit trail that doesn't depend on application code remembering to set it correctly.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Timestamp marking the most recent update to this role record. The onupdate parameter
    # tells SQLAlchemy to include this column in UPDATE statements with a new timestamp, and
    # the server_default ensures it gets initialized correctly during INSERT operations.
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    def has_permission(self, perm: str) -> bool:
        """
        Check whether this role grants a specific permission.
        
        This convenience method attempts to parse the permissions field as JSON and checks
        whether the requested permission string is present in the list. The implementation
        handles several formats defensively: if permissions is None or empty, it returns False;
        if permissions is a valid JSON array, it checks for membership; if parsing fails, it
        falls back to treating permissions as a comma-separated string.
        
        This naive implementation works for simple use cases during development, but for
        production systems with complex permission models, you should implement a more robust
        permission checking system. Consider using a dedicated RBAC (Role-Based Access Control)
        library, storing permissions in JSONB for efficient querying, or normalizing permissions
        into a separate table with proper indexing.
        
        Args:
            perm: The permission string to check for, like "read:subsidies" or "approve:projects"
        
        Returns:
            True if the role grants this permission, False otherwise. Also returns False if
            the permissions field is malformed or empty rather than raising an exception.
        """
        # If there are no permissions defined, the role obviously doesn't grant anything.
        # This check also handles the None case gracefully without needing additional guards.
        if not self.permissions:
            return False
        
        try:
            # Attempt to parse the permissions field as a JSON array. This is the expected
            # format for structured permission storage, where permissions might look like
            # ["read:subsidies", "write:projects", "approve:disbursements"].
            perms_list = json.loads(self.permissions)
            
            # If parsing succeeded and we got a list, check for membership. The isinstance
            # check ensures we handle cases where someone stored a JSON object or other type.
            if isinstance(perms_list, list):
                return perm in perms_list
            
            # If we got valid JSON but it wasn't a list (maybe a string or object), fall
            # through to the simple string matching fallback below.
        except (json.JSONDecodeError, TypeError):
            # JSON parsing failed, which might mean permissions is stored in a simpler format
            # like comma-separated values. We'll fall through to handle that case below.
            pass
        
        # Fallback for simple comma-separated permission strings or direct string matching.
        # This handles cases like permissions="read:subsidies,write:projects" or even just
        # permissions="admin" for single-permission roles. We check for exact match or
        # presence in a comma-separated list, being careful with whitespace.
        simple_perms = [p.strip() for p in self.permissions.split(',')]
        return perm in simple_perms
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert this role record to a JSON-serializable dictionary.
        
        This method transforms the ORM model into a plain Python dictionary suitable for API
        responses, logging, or serialization to JSON. Special handling is applied to datetime
        fields which aren't natively JSON-serializable, converting them to ISO 8601 formatted
        strings which are widely supported and human-readable.
        
        The permissions field is included as a string without parsing, since it might not
        always contain valid JSON and we don't want serialization to fail if someone stored
        malformed data. Calling code can parse the permissions string as needed for their
        specific use case.
        
        Returns:
            A dictionary containing all role fields in JSON-compatible formats.
        """
        return {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            # Include permissions as-is without parsing, since it's stored as a string and
            # may not always be valid JSON. Calling code can parse it if needed.
            "permissions": self.permissions,
            # Convert datetime fields to ISO 8601 strings for consistent JSON representation
            # across different systems. The isoformat() method produces strings like
            # "2024-03-15T14:30:00+00:00" which clearly communicate timezone information.
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }