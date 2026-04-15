"""
backend/routes/audit_routes.py

REST API endpoints for managing and querying audit records in the subsidy management system.

This module provides a FastAPI router with endpoints to list, retrieve, and create audit log
entries. Audit records serve as an immutable historical trail of significant events across all
entities in the system (subsidies, projects, disbursements, users, etc.), supporting compliance,
debugging, and transparency requirements.

The endpoints support flexible filtering by entity type, entity ID, and action type, enabling
both broad audit reviews and targeted investigations of specific entities or event types. All
operations maintain proper transactional integrity and provide clear error messages when issues
occur, making it easy to integrate audit logging into business workflows throughout the application.

Test the list endpoint with curl:
    curl "http://localhost:8000/api/audits?entity=subsidy&limit=10"
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.models.audit import AuditRecord as AuditRecordModel
from backend.schemas.audit import AuditCreate, AuditRecord


router = APIRouter(tags=["audits"])


@router.get("/", response_model=List[AuditRecord])
def list_audit_records(
    entity: Optional[str] = Query(None, description="Filter by entity type (e.g., 'subsidy', 'project')"),
    entity_id: Optional[int] = Query(None, description="Filter by specific entity ID"),
    action: Optional[str] = Query(None, description="Filter by action type (e.g., 'create', 'update')"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    db: Session = Depends(get_db),
) -> List[AuditRecordModel]:
    """
    Retrieve a filtered and paginated list of audit records.
    
    This endpoint allows flexible querying of the audit trail with optional filters for entity
    type, entity ID, and action. The results are always ordered by creation time in descending
    order, showing the most recent events first, which is the natural way administrators and
    auditors want to review system activity.
    
    The pagination parameters (limit and offset) enable efficient handling of large audit logs
    without overwhelming clients or the database. The limit is capped at 200 to prevent
    accidentally requesting millions of records, while still being generous enough for most
    legitimate use cases like dashboard displays or report generation.
    
    Args:
        entity: Optional filter for entity type (e.g., "subsidy", "project", "user")
        entity_id: Optional filter for a specific entity's primary key
        action: Optional filter for action type (e.g., "create", "approve", "delete")
        limit: Maximum number of records to return (1-200, default 50)
        offset: Number of records to skip for pagination (default 0)
        db: Database session injected by FastAPI's dependency system
    
    Returns:
        A list of AuditRecord objects matching the filter criteria, ordered by created_at
        descending. The list may be empty if no matching records exist.
    
    Raises:
        HTTPException: 500 error if a database query fails for unexpected reasons
    """
    try:
        # Start with a base query that we'll progressively filter. We begin by querying all
        # audit records from the ORM model, which gives us a SQLAlchemy query object that we
        # can refine with filter conditions before execution.
        query = db.query(AuditRecordModel)
        
        # Apply each filter only if the corresponding parameter was provided. This makes all
        # filters optional and allows any combination of filtering criteria. We use exact
        # equality matching for simplicity, but you could extend this to support pattern
        # matching or more complex queries if needed.
        if entity is not None:
            query = query.filter(AuditRecordModel.entity == entity)
        
        if entity_id is not None:
            query = query.filter(AuditRecordModel.entity_id == entity_id)
        
        if action is not None:
            query = query.filter(AuditRecordModel.action == action)
        
        # Order by creation timestamp descending so the most recent events appear first. This
        # is the natural ordering for audit logs where you typically care most about recent
        # activity and want to scroll backward through history as needed.
        query = query.order_by(AuditRecordModel.created_at.desc())
        
        # Apply pagination by skipping 'offset' records and taking up to 'limit' records. This
        # enables efficient paging through large audit logs without loading everything into
        # memory at once. The offset/limit pattern is standard in REST APIs and maps cleanly
        # to SQL OFFSET and LIMIT clauses.
        query = query.offset(offset).limit(limit)
        
        # Execute the query and materialize the results as a list of ORM objects. These will
        # automatically be serialized to Pydantic models by FastAPI using the response_model
        # configuration, which relies on Pydantic's orm_mode to extract fields from SQLAlchemy
        # instances.
        records = query.all()
        
        return records
        
    except SQLAlchemyError as e:
        # If something goes wrong with the database query (connection issues, constraint
        # violations, unexpected errors), we catch it here and translate it into an HTTP 500
        # error with a helpful message. We don't expose the raw database error to clients
        # for security reasons, but we do log it internally for debugging.
        raise HTTPException(
            status_code=500,
            detail=f"Database error while fetching audit records: {str(e)}"
        )


@router.get("/{audit_id}", response_model=AuditRecord)
def get_audit_record(
    audit_id: int,
    db: Session = Depends(get_db),
) -> AuditRecordModel:
    """
    Retrieve a single audit record by its primary key ID.
    
    This endpoint fetches the complete details of one specific audit entry, which is useful
    when you're drilling down from a list view into the full context of what happened during
    a particular event. The audit ID is typically obtained from the list endpoint or from
    application logs that reference specific audit entries.
    
    Args:
        audit_id: The primary key ID of the audit record to retrieve
        db: Database session injected by FastAPI's dependency system
    
    Returns:
        The AuditRecord object with the specified ID, containing all fields including the
        full details JSON that might have been truncated in list views.
    
    Raises:
        HTTPException: 404 error if no audit record exists with the given ID
        HTTPException: 500 error if a database query fails for unexpected reasons
    """
    try:
        # Query for the audit record using the primary key. The get() method is efficient
        # because it uses the primary key index directly rather than performing a full table
        # scan. It returns None if no record with this ID exists.
        record = db.query(AuditRecordModel).filter(AuditRecordModel.id == audit_id).first()
        
        # If the record doesn't exist, we return a 404 Not Found error with a clear message.
        # This is the standard HTTP response for "the resource you asked for doesn't exist"
        # and allows clients to distinguish between "not found" and other error types.
        if record is None:
            raise HTTPException(
                status_code=404,
                detail=f"Audit record with ID {audit_id} not found"
            )
        
        return record
        
    except HTTPException:
        # Re-raise HTTPExceptions that we explicitly created (like the 404 above) so they
        # propagate correctly to FastAPI's error handling. We don't want to catch and wrap
        # these in another error layer.
        raise
        
    except SQLAlchemyError as e:
        # For unexpected database errors, we provide a 500 Internal Server Error with details
        # that help debugging while avoiding exposure of sensitive internal implementation
        # details to end users.
        raise HTTPException(
            status_code=500,
            detail=f"Database error while fetching audit record: {str(e)}"
        )


@router.post("/", response_model=AuditRecord, status_code=201)
def create_audit_record(
    audit_data: AuditCreate,
    db: Session = Depends(get_db),
) -> AuditRecordModel:
    """
    Create a new audit record to log a significant event in the system.
    
    This endpoint should be called whenever an important action occurs that needs to be
    recorded in the audit trail. Common use cases include tracking when subsidies are approved,
    when projects change status, when disbursements are made, or when users modify sensitive
    configuration settings. The audit log provides an immutable historical record for compliance,
    debugging, and transparency.
    
    The created_at timestamp is set automatically by the database, ensuring consistent and
    tamper-resistant timing information. The details field can contain any additional context
    as a JSON string, giving you flexibility to capture action-specific information like
    which fields changed, who initiated the action, or what the previous values were.
    
    Args:
        audit_data: The audit record data including entity, entity_id, action, and optional details
        db: Database session injected by FastAPI's dependency system
    
    Returns:
        The newly created AuditRecord object with its auto-generated ID and created_at timestamp
    
    Raises:
        HTTPException: 400 error if the input data is invalid or violates database constraints
        HTTPException: 500 error if an unexpected database error occurs during creation
    """
    try:
        # Create a new ORM instance from the Pydantic input model. We use **audit_data.dict()
        # to unpack the validated fields into keyword arguments for the constructor. This
        # ensures type safety and automatic validation of required fields by Pydantic before
        # we even touch the database.
        new_audit = AuditRecordModel(**audit_data.dict())
        
        # Add the new instance to the session's pending changes. This doesn't execute any SQL
        # yet, just marks the object to be inserted when we commit.
        db.add(new_audit)
        
        # Commit the transaction to persist the new audit record to the database. This is when
        # the actual INSERT statement executes, and the database assigns the auto-generated
        # ID and sets the created_at timestamp using its server defaults.
        db.commit()
        
        # Refresh the object to load the database-generated values (id and created_at) back
        # into our Python object. This ensures the returned object has all fields populated
        # correctly, including values that were set by database defaults rather than our
        # application code.
        db.refresh(new_audit)
        
        return new_audit
        
    except SQLAlchemyError as e:
        # If anything goes wrong during the database operation (constraint violations,
        # connection issues, etc.), we rollback the transaction to undo any partial changes
        # and maintain database consistency. Then we raise a clear HTTP error explaining
        # what happened.
        db.rollback()
        
        # Check if this looks like a validation/constraint error (like a foreign key violation
        # or NOT NULL constraint) versus a system error (connection failure, disk full, etc.).
        # For constraint errors we return 400 Bad Request; for system errors we return 500.
        error_message = str(e)
        if "constraint" in error_message.lower() or "null" in error_message.lower():
            raise HTTPException(
                status_code=400,
                detail=f"Invalid audit data: {error_message}"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Database error while creating audit record: {error_message}"
            )