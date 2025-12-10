"""
backend/models/audit.py

Defines the AuditRecord model for capturing immutable audit trail events across the application.

This model serves as a universal audit log that can track changes to any entity in the system
(subsidies, projects, disbursements, users, etc.) without creating tight coupling through
foreign key constraints. By storing entity type and ID as flexible fields, we ensure that
audit records remain queryable even after the original entities have been soft-deleted or
purged from the database.

The audit log is append-only by design — records should never be updated or deleted in
normal operations, providing a reliable historical record for compliance, debugging, and
system transparency.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import Column, Integer, String, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.connection import Base


__all__ = ["AuditRecord"]


class AuditRecord(Base):
    """
    Immutable audit trail record capturing significant events across all entities.
    
    Each audit record represents a discrete action taken on some entity in the system.
    Common use cases include tracking when subsidies are created, when projects receive
    approvals, when disbursements are marked as complete, or when users modify sensitive
    configuration settings.
    
    The flexible schema (entity/entity_id instead of strict foreign keys) means this
    model can track any type of entity without requiring schema migrations when new
    entity types are introduced. This design trades strict referential integrity for
    flexibility and historical preservation.
    
    Example usage in application code:
        audit = AuditRecord(
            entity="subsidy",
            entity_id=subsidy.id,
            action="approved",
            details=json.dumps({"approved_by": user.id, "amount": 50000})
        )
        session.add(audit)
        session.commit()
    """
    
    __tablename__ = "audits"
    
    # Primary key for this audit entry. The index is implicit on primary keys but we
    # mention it explicitly here for clarity about query performance expectations.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    
    # The type of entity being audited. This should be a consistent string identifier
    # like "subsidy", "project", "user", "disbursement". Using lowercase singular form
    # helps maintain consistency across the codebase.
    entity: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    # The primary key of the entity that was affected. Combined with entity, this gives
    # us a logical pointer to what changed. We index this for fast lookups when viewing
    # an entity's history (e.g., "show me all audits for subsidy #42").
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    
    # The action that was performed. Common values include "create", "update", "delete",
    # "approve", "reject", "disburse". Use consistent verbs to make querying easier.
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Freeform details about what happened. This is typically a JSON-encoded string
    # containing specifics like which fields changed, who initiated the action, or
    # additional context that would be useful for audit review or debugging. Keeping
    # this as Text rather than JSON type ensures maximum database compatibility.
    details: Mapped[str] = mapped_column(Text, nullable=True)
    
    # When this audit event occurred. The server_default ensures the database sets this
    # timestamp automatically, providing a consistent and tamper-resistant record of when
    # events happened. Using timezone-aware datetime helps avoid ambiguity in distributed
    # systems or when team members are in different time zones.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    
    def to_dict(self) -> dict[str, Any]:
        """
        Convert this audit record to a plain Python dictionary for serialization.
        
        This method is useful when returning audit logs through API endpoints or when
        logging audit events to external systems. The datetime field is included as-is;
        you may want to format it as an ISO 8601 string in your API layer depending on
        your client requirements.
        
        Returns:
            A dictionary containing all key fields of this audit record. The datetime
            object can be serialized by FastAPI's JSON encoder automatically.
        """
        return {
            "id": self.id,
            "entity": self.entity,
            "entity_id": self.entity_id,
            "action": self.action,
            "details": self.details,
            "created_at": self.created_at,
        }