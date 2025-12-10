"""
backend/services/audit_service.py

Audit service helpers: create, retrieve, and list audit records (DB transactional helpers).
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from backend.models.audit import AuditRecord as AuditRecordModel
from backend.schemas.audit import AuditCreate, AuditRecord as AuditRecordSchema


def create_audit(db: Session, audit_in: AuditCreate, commit: bool = True) -> AuditRecordModel:
    """
    Create and persist a new audit record.
    
    Args:
        db: SQLAlchemy session
        audit_in: Validated AuditCreate schema
        commit: Whether to commit immediately (default True)
    
    Returns:
        Created AuditRecordModel instance
    
    Raises:
        RuntimeError: If database operation fails
    """
    try:
        audit_data = audit_in.dict()
        audit_record = AuditRecordModel(
            entity=audit_data["entity"],
            entity_id=audit_data["entity_id"],
            action=audit_data["action"],
            details=audit_data.get("details")
        )
        
        db.add(audit_record)
        
        if commit:
            db.commit()
            db.refresh(audit_record)
            
            # TODO: Publish audit event to message queue (e.g., Kafka)
            # from backend.services.event_service import publish_event
            # publish_event("audit.created", {"id": audit_record.id, "entity": audit_record.entity})
            
            # TODO: Optional on-chain proof writing for critical audit events
            # from backend.services.blockchain_service import write_proof_to_chain
            # from backend.utils.hashing import sha256_of
            # proof_hash = sha256_of({"entity": audit_record.entity, "entity_id": audit_record.entity_id, "action": audit_record.action})
            # write_proof_to_chain(proof_hash)
        
        return audit_record
        
    except SQLAlchemyError as e:
        db.rollback()
        raise RuntimeError(f"DB error while creating audit record: {str(e)}")


def get_audit_by_id(db: Session, audit_id: int) -> Optional[AuditRecordModel]:
    """
    Retrieve a single audit record by ID.
    
    Args:
        db: SQLAlchemy session
        audit_id: Primary key of audit record
    
    Returns:
        AuditRecordModel if found, None otherwise
    """
    return db.query(AuditRecordModel).filter(AuditRecordModel.id == audit_id).first()


def list_audits(
    db: Session,
    *,
    entity: Optional[str] = None,
    entity_id: Optional[int] = None,
    action: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> List[AuditRecordModel]:
    """
    List audit records with optional filters and pagination.
    
    Args:
        db: SQLAlchemy session
        entity: Filter by entity type (optional)
        entity_id: Filter by entity ID (optional)
        action: Filter by action (optional)
        limit: Maximum number of records to return (must be >= 1)
        offset: Number of records to skip (must be >= 0)
    
    Returns:
        List of AuditRecordModel instances
    
    Raises:
        ValueError: If limit or offset are invalid
    """
    if limit < 1:
        raise ValueError(f"limit must be >= 1, got {limit}")
    if offset < 0:
        raise ValueError(f"offset must be >= 0, got {offset}")
    
    query = db.query(AuditRecordModel)
    
    if entity is not None:
        query = query.filter(AuditRecordModel.entity == entity)
    
    if entity_id is not None:
        query = query.filter(AuditRecordModel.entity_id == entity_id)
    
    if action is not None:
        query = query.filter(AuditRecordModel.action == action)
    
    query = query.order_by(AuditRecordModel.created_at.desc())
    query = query.limit(limit).offset(offset)
    
    return query.all()


def count_audits(
    db: Session,
    *,
    entity: Optional[str] = None,
    entity_id: Optional[int] = None,
    action: Optional[str] = None
) -> int:
    """
    Count audit records matching the given filters.
    
    Args:
        db: SQLAlchemy session
        entity: Filter by entity type (optional)
        entity_id: Filter by entity ID (optional)
        action: Filter by action (optional)
    
    Returns:
        Total count of matching records
    """
    query = db.query(AuditRecordModel)
    
    if entity is not None:
        query = query.filter(AuditRecordModel.entity == entity)
    
    if entity_id is not None:
        query = query.filter(AuditRecordModel.entity_id == entity_id)
    
    if action is not None:
        query = query.filter(AuditRecordModel.action == action)
    
    return query.count()


def record_action(
    db: Session,
    entity: str,
    entity_id: int,
    action: str,
    details: Optional[str] = None,
    commit: bool = True
) -> AuditRecordModel:
    """
    Convenience wrapper to record an audit action.
    
    Args:
        db: SQLAlchemy session
        entity: Entity type (e.g., 'subsidy', 'project')
        entity_id: ID of the entity
        action: Action performed (e.g., 'create', 'update', 'delete')
        details: Optional details or JSON string
        commit: Whether to commit immediately (default True)
    
    Returns:
        Created AuditRecordModel instance
    """
    audit_in = AuditCreate(
        entity=entity,
        entity_id=entity_id,
        action=action,
        details=details
    )
    return create_audit(db, audit_in, commit=commit)


__all__ = ["create_audit", "get_audit_by_id", "list_audits", "count_audits", "record_action"]

# Test hint: use an in-memory sqlite Session and call create_audit(db, AuditCreate(...), commit=True) then assert the returned .id is not None.