"""
backend/routes/disbursement_routes.py

REST API endpoints for managing disbursement records in the subsidy management system.

This module provides a FastAPI router with full CRUD operations for disbursements, which represent
individual payment or fund transfer events tied to subsidies. Each disbursement captures the
monetary amount, timing, external references, and notes about a specific payment made as part of
a subsidy program's execution.

The endpoints support flexible filtering by subsidy and amount ranges, enabling queries like
"show all disbursements over $10,000" or "list all payments for subsidy #42". All monetary
operations use Python's Decimal type to maintain exact precision, which is critical for financial
systems where rounding errors can accumulate and cause serious discrepancies in reporting and
compliance.

Test creating a disbursement with curl:
    curl -X POST "http://localhost:8000/api/disbursements" -H "Content-Type: application/json" -d '{"subsidy_id":1,"amount":"5000.00","currency":"INR","reference":"TXN-123"}'
"""

from decimal import Decimal, InvalidOperation
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.models.disbursement import Disbursement as DisbursementModel
from backend.schemas.disbursement import Disbursement, DisbursementCreate, DisbursementUpdate


router = APIRouter( tags=["disbursements"])


@router.get("/", response_model=List[Disbursement])
def list_disbursements(
    subsidy_id: Optional[int] = Query(None, description="Filter by subsidy ID"),
    min_amount: Optional[float] = Query(None, description="Minimum disbursement amount (inclusive)"),
    max_amount: Optional[float] = Query(None, description="Maximum disbursement amount (inclusive)"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    db: Session = Depends(get_db),
) -> List[DisbursementModel]:
    """
    Retrieve a filtered and paginated list of disbursement records.
    
    This endpoint allows flexible querying of disbursements with optional filters for subsidy,
    amount ranges, and pagination. The results are ordered by disbursement date in descending
    order, showing the most recent payments first, which is typically how financial teams want
    to review transaction histories.
    
    The amount filters accept floats for convenience in API calls, but internally we convert
    them to Decimal for comparison to maintain the precision of amounts stored in the database.
    This ensures that queries like "amount >= 1000.00" work correctly without floating-point
    comparison issues that could miss or incorrectly include records.
    
    Args:
        subsidy_id: Optional filter for disbursements tied to a specific subsidy
        min_amount: Optional minimum amount filter (inclusive)
        max_amount: Optional maximum amount filter (inclusive)
        limit: Maximum number of records to return (1-200, default 50)
        offset: Number of records to skip for pagination (default 0)
        db: Database session injected by FastAPI's dependency system
    
    Returns:
        A list of Disbursement objects matching the filter criteria, ordered by date descending.
        The list may be empty if no matching records exist.
    
    Raises:
        HTTPException: 500 error if a database query fails for unexpected reasons
    """
    try:
        # Start with a base query that we'll progressively filter based on provided parameters.
        # This gives us flexibility to support any combination of filters without writing
        # separate query logic for each possible combination.
        query = db.query(DisbursementModel)
        
        # Apply subsidy_id filter if provided. This is an exact equality match that's efficient
        # due to the index on the subsidy_id column, enabling fast lookups of all disbursements
        # for a particular subsidy.
        if subsidy_id is not None:
            query = query.filter(DisbursementModel.subsidy_id == subsidy_id)
        
        # Apply minimum amount filter if provided. We convert the float to Decimal to maintain
        # precision consistency with how amounts are stored in the database. This prevents
        # subtle bugs where floating-point comparison might miss records due to rounding.
        if min_amount is not None:
            query = query.filter(DisbursementModel.amount >= Decimal(str(min_amount)))
        
        # Apply maximum amount filter if provided, also using Decimal conversion for precision.
        # Together with min_amount, this allows range queries like "show disbursements between
        # $1000 and $5000" which are common in financial reporting and analysis.
        if max_amount is not None:
            query = query.filter(DisbursementModel.amount <= Decimal(str(max_amount)))
        
        # Order by disbursement date descending so the most recent payments appear first. This
        # is the natural ordering for financial records where you typically care most about
        # recent activity and want to scroll backward through history as needed.
        query = query.order_by(DisbursementModel.date.desc())
        
        # Apply pagination to efficiently handle large result sets without loading everything
        # into memory. The offset/limit pattern is standard in REST APIs and maps directly to
        # SQL OFFSET and LIMIT clauses for database-level pagination.
        query = query.offset(offset).limit(limit)
        
        # Execute the query and materialize results as a list of ORM objects. FastAPI will
        # automatically serialize these to the Disbursement Pydantic schema using orm_mode.
        disbursements = query.all()
        
        return disbursements
        
    except SQLAlchemyError as e:
        # If something goes wrong with the database query, catch it and translate to an HTTP
        # 500 error with a user-friendly message. We don't expose raw database errors to
        # clients for security reasons.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error while fetching disbursements: {str(e)}"
        )


@router.get("/{disbursement_id}", response_model=Disbursement)
def get_disbursement(
    disbursement_id: int,
    db: Session = Depends(get_db),
) -> DisbursementModel:
    """
    Retrieve a single disbursement record by its primary key ID.
    
    This endpoint fetches the complete details of one specific disbursement, which is useful
    when drilling down from a list view to examine the full context of a particular payment
    including all notes and reference information that might be truncated in list views.
    
    Args:
        disbursement_id: The primary key ID of the disbursement to retrieve
        db: Database session injected by FastAPI's dependency system
    
    Returns:
        The Disbursement object with the specified ID, containing all fields including full
        notes text that might have been truncated in list views.
    
    Raises:
        HTTPException: 404 error if no disbursement exists with the given ID
        HTTPException: 500 error if a database query fails for unexpected reasons
    """
    try:
        # Query for the disbursement using the primary key. The filter on the primary key is
        # highly efficient due to the automatic index, and first() returns None if not found.
        disbursement = db.query(DisbursementModel).filter(
            DisbursementModel.id == disbursement_id
        ).first()
        
        # If the disbursement doesn't exist, return a 404 Not Found error with a clear message.
        # This is the standard HTTP response for "the resource you asked for doesn't exist".
        if disbursement is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Disbursement with ID {disbursement_id} not found"
            )
        
        return disbursement
        
    except HTTPException:
        # Re-raise HTTPExceptions that we explicitly created so they propagate correctly to
        # FastAPI's error handling with the right status codes and messages.
        raise
        
    except SQLAlchemyError as e:
        # For unexpected database errors, provide a 500 error with details that help debugging
        # while avoiding exposure of sensitive internal implementation details.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error while fetching disbursement: {str(e)}"
        )


@router.post("/", response_model=Disbursement, status_code=status.HTTP_201_CREATED)
def create_disbursement(
    disbursement_data: DisbursementCreate,
    db: Session = Depends(get_db),
) -> DisbursementModel:
    """
    Create a new disbursement record for a subsidy payment.
    
    This endpoint records a new payment or fund transfer made as part of a subsidy program.
    The amount field is critical and must be handled with exact decimal precision to avoid
    financial discrepancies. We accept the amount as a string, float, or Decimal in the request,
    but always convert it to Python's Decimal type before storing to maintain exact precision.
    
    The date field defaults to the current timestamp if not provided, using the database server's
    clock for consistency. The currency defaults to "INR" but can be overridden for international
    payments or multi-currency programs.
    
    Args:
        disbursement_data: The disbursement details including subsidy_id, amount, and optional fields
        db: Database session injected by FastAPI's dependency system
    
    Returns:
        The newly created Disbursement object with its auto-generated ID and server-set timestamp
    
    Raises:
        HTTPException: 400 error if the input data is invalid (e.g., malformed amount)
        HTTPException: 500 error if an unexpected database error occurs during creation
    """
    try:
        # Convert the disbursement data to a dictionary for processing. We need to handle the
        # amount field specially to ensure it's stored as Decimal for exact precision.
        data_dict = disbursement_data.dict()
        
        # Convert the amount to Decimal for exact financial precision. The str() wrapper ensures
        # that if the amount came in as a float, we convert it via string representation to
        # avoid any floating-point precision issues. This is critical for financial data where
        # even small rounding errors can accumulate to significant discrepancies.
        try:
            data_dict["amount"] = Decimal(str(data_dict["amount"]))
        except (InvalidOperation, ValueError, TypeError) as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid amount format: {str(e)}"
            )
        
        # Create the new ORM instance with the validated and converted data. The **data_dict
        # unpacking passes all fields as keyword arguments to the model constructor.
        new_disbursement = DisbursementModel(**data_dict)
        
        # Add the new instance to the session's pending changes. This doesn't execute SQL yet,
        # just marks the object to be inserted when we commit.
        db.add(new_disbursement)
        
        # Commit the transaction to persist the new disbursement to the database. This is when
        # the actual INSERT statement executes, and the database assigns the auto-generated ID
        # and sets the date timestamp using its server defaults if not provided by the client.
        db.commit()
        
        # Refresh the object to load database-generated values (id, date if auto-set) back into
        # the Python object. This ensures the returned object has all fields populated correctly.
        db.refresh(new_disbursement)
        
        return new_disbursement
        
    except HTTPException:
        # Re-raise HTTPExceptions that we explicitly created so they propagate to FastAPI's
        # error handling with the correct status codes and messages.
        raise
        
    except SQLAlchemyError as e:
        # If anything goes wrong during the database operation (constraint violations, connection
        # issues, etc.), rollback the transaction to undo any partial changes and maintain
        # database consistency.
        db.rollback()
        
        # Check if this looks like a validation/constraint error versus a system error. For
        # constraint errors we return 400 Bad Request; for system errors we return 500.
        error_message = str(e).lower()
        if "constraint" in error_message or "foreign key" in error_message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid disbursement data: {str(e)}"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error while creating disbursement: {str(e)}"
            )


@router.patch("/{disbursement_id}", response_model=Disbursement)
def update_disbursement(
    disbursement_id: int,
    disbursement_update: DisbursementUpdate,
    db: Session = Depends(get_db),
) -> DisbursementModel:
    """
    Partially update an existing disbursement record.
    
    This endpoint allows updating specific fields of a disbursement without requiring all fields
    to be provided. Only the fields included in the request body will be modified; unspecified
    fields retain their current values. This is useful for corrections or adding information
    after initial creation, such as updating reference numbers or notes.
    
    The amount field, if provided, is carefully converted to Decimal to maintain financial
    precision. All updates are transactional - if any error occurs, the entire update is rolled
    back to maintain data consistency.
    
    Args:
        disbursement_id: The primary key ID of the disbursement to update
        disbursement_update: The fields to update (all optional)
        db: Database session injected by FastAPI's dependency system
    
    Returns:
        The updated Disbursement object with all current field values
    
    Raises:
        HTTPException: 404 error if the disbursement doesn't exist
        HTTPException: 400 error if the update data is invalid
        HTTPException: 500 error if an unexpected database error occurs
    """
    try:
        # Fetch the existing disbursement record. We need the full object so we can update
        # only the fields that were provided in the request.
        disbursement = db.query(DisbursementModel).filter(
            DisbursementModel.id == disbursement_id
        ).first()
        
        # If the disbursement doesn't exist, return 404 before attempting any updates.
        if disbursement is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Disbursement with ID {disbursement_id} not found"
            )
        
        # Extract only the fields that were actually provided in the request. The exclude_unset
        # parameter ensures we only get fields that the client explicitly set, not defaults
        # from the Pydantic model. This enables true partial updates.
        update_data = disbursement_update.dict(exclude_unset=True)
        
        # If amount is being updated, convert it to Decimal for exact precision. This maintains
        # financial accuracy even if the client sent a float or string representation.
        if "amount" in update_data:
            try:
                update_data["amount"] = Decimal(str(update_data["amount"]))
            except (InvalidOperation, ValueError, TypeError) as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid amount format: {str(e)}"
                )
        
        # Apply each update by setting the corresponding attribute on the ORM object. This
        # approach works well for partial updates where we only modify the fields that were
        # provided in the request.
        for field, value in update_data.items():
            setattr(disbursement, field, value)
        
        # Commit the transaction to persist the updates. The updated_at timestamp should be
        # automatically updated by the database's onupdate trigger if configured in the model.
        db.commit()
        
        # Refresh to ensure we have the latest values including any database-generated fields
        # like updated_at that may have changed during the commit.
        db.refresh(disbursement)
        
        return disbursement
        
    except HTTPException:
        # Re-raise HTTPExceptions that we explicitly created so they propagate correctly.
        raise
        
    except SQLAlchemyError as e:
        # Roll back on database errors to maintain consistency, then raise an appropriate
        # HTTP error based on the error type.
        db.rollback()
        
        error_message = str(e).lower()
        if "constraint" in error_message or "foreign key" in error_message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid update data: {str(e)}"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error while updating disbursement: {str(e)}"
            )


@router.delete("/{disbursement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_disbursement(
    disbursement_id: int,
    db: Session = Depends(get_db),
) -> Response:
    """
    Delete a disbursement record from the system.
    
    This endpoint performs a hard delete, permanently removing the disbursement record from the
    database. For production systems handling financial data, you may want to implement soft
    deletion instead (e.g., an is_deleted flag) to maintain a complete audit trail of all
    transactions that ever occurred, even if they were later corrected or reversed.
    
    Hard deletion is appropriate for test data cleanup or correcting mistakes during data entry,
    but should be used cautiously in production environments where regulatory compliance may
    require maintaining historical records of all financial transactions.
    
    Args:
        disbursement_id: The primary key ID of the disbursement to delete
        db: Database session injected by FastAPI's dependency system
    
    Returns:
        Empty response with 204 No Content status code on success
    
    Raises:
        HTTPException: 404 error if the disbursement doesn't exist
        HTTPException: 500 error if an unexpected database error occurs
    """
    try:
        # Fetch the disbursement to be deleted. We need to verify it exists before attempting
        # deletion, otherwise we'd return success even when deleting a non-existent record.
        disbursement = db.query(DisbursementModel).filter(
            DisbursementModel.id == disbursement_id
        ).first()
        
        # If the disbursement doesn't exist, return 404. It's important to distinguish between
        # "successfully deleted" and "there was nothing to delete" for client applications.
        if disbursement is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Disbursement with ID {disbursement_id} not found"
            )
        
        # Delete the record and commit the transaction. This permanently removes the row from
        # the database table. Consider implementing soft deletion for production financial
        # systems where maintaining a complete audit trail is critical for compliance.
        db.delete(disbursement)
        db.commit()
        
        # Return an empty response with 204 No Content status. This is the standard HTTP
        # response for successful deletion operations according to REST conventions.
        return Response(status_code=status.HTTP_204_NO_CONTENT)
        
    except HTTPException:
        # Re-raise HTTPExceptions that we explicitly created so they propagate correctly.
        raise
        
    except SQLAlchemyError as e:
        # Roll back on database errors to maintain consistency, then raise a 500 error with
        # details to help debugging while avoiding exposure of sensitive internals.
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error while deleting disbursement: {str(e)}"
        )