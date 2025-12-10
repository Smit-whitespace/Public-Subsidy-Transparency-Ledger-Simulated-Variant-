"""
backend/routes/project_routes.py

REST API endpoints for managing project records in the subsidy management system.

This module provides a FastAPI router with full CRUD operations for projects, which represent
specific initiatives or programs that are funded or supported by subsidies. Each project captures
essential information about the initiative including its relationship to subsidies, timeline,
ownership, status, and descriptive metadata.

Projects serve as the operational units within subsidy programs, allowing administrators to track
how funds are being utilized across different initiatives. The endpoints support flexible filtering
by subsidy, owner, and status, enabling queries like "show all active projects for subsidy #42" or
"list all projects owned by the Engineering department".

Test listing projects with curl:
    curl "http://localhost:8000/api/projects?status=active&limit=10"
Test creating a project with curl:
    curl -X POST "http://localhost:8000/api/projects" -H "Content-Type: application/json" -d '{"name":"Infrastructure Upgrade","subsidy_id":1,"owner":"City Council","status":"planned"}'
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.models.project import Project as ProjectModel
from backend.schemas.project import Project, ProjectCreate, ProjectUpdate


router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("/", response_model=List[Project])
def list_projects(
    subsidy_id: Optional[int] = Query(None, description="Filter by subsidy ID"),
    owner: Optional[str] = Query(None, description="Filter by project owner"),
    status: Optional[str] = Query(None, description="Filter by project status"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    db: Session = Depends(get_db),
) -> List[ProjectModel]:
    """
    Retrieve a filtered and paginated list of project records.
    
    This endpoint allows flexible querying of projects with optional filters for subsidy,
    owner, and status. The results are ordered by creation time in descending order, showing
    the most recently created projects first, which is typically how administrators want to
    review project portfolios and track new initiatives being added to the system.
    
    The filtering capabilities enable common operational queries like "show all active projects
    funded by subsidy #5" or "list all projects owned by the Infrastructure Department". These
    filters can be combined to create powerful queries for reporting and portfolio management.
    
    Args:
        subsidy_id: Optional filter for projects tied to a specific subsidy
        owner: Optional filter for projects belonging to a specific owner/department
        status: Optional filter for projects with a specific status (e.g., "active", "planned")
        limit: Maximum number of records to return (1-200, default 50)
        offset: Number of records to skip for pagination (default 0)
        db: Database session injected by FastAPI's dependency system
    
    Returns:
        A list of Project objects matching the filter criteria, ordered by created_at descending.
        The list may be empty if no matching records exist.
    
    Raises:
        HTTPException: 500 error if a database query fails for unexpected reasons
    """
    try:
        # Start with a base query that we'll progressively filter based on provided parameters.
        # This pattern allows flexible combinations of filters without requiring separate query
        # logic for each possible combination.
        query = db.query(ProjectModel)
        
        # Apply subsidy_id filter if provided. This enables queries like "show all projects
        # for subsidy #42", which is a common reporting need for administrators tracking how
        # specific subsidy programs are being utilized across multiple projects.
        if subsidy_id is not None:
            query = query.filter(ProjectModel.subsidy_id == subsidy_id)
        
        # Apply owner filter if provided. This enables organizational queries like "show all
        # projects owned by the Engineering department", which helps with portfolio management
        # and workload distribution across teams or departments.
        if owner is not None:
            query = query.filter(ProjectModel.owner == owner)
        
        # Apply status filter if provided. Status filtering is critical for operational views
        # like "show active projects" or "list all planned initiatives", allowing administrators
        # to focus on projects in specific lifecycle stages.
        if status is not None:
            query = query.filter(ProjectModel.status == status)
        
        # Order by creation timestamp descending so the most recently created projects appear
        # first. This ordering makes sense for dashboards and activity feeds where users want
        # to see what's new before scrolling through older projects.
        query = query.order_by(ProjectModel.created_at.desc())
        
        # Apply pagination to efficiently handle large project portfolios without loading
        # everything into memory. The offset/limit pattern is standard in REST APIs and maps
        # directly to SQL OFFSET and LIMIT clauses.
        query = query.offset(offset).limit(limit)
        
        # Execute the query and materialize results as a list of ORM objects. FastAPI will
        # automatically serialize these to Pydantic Project schemas using orm_mode.
        projects = query.all()
        
        return projects
        
    except SQLAlchemyError as e:
        # If something goes wrong with the database query, catch it and translate to an HTTP
        # 500 error with a user-friendly message. We don't expose raw database errors for
        # security reasons.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error while fetching projects: {str(e)}"
        )


@router.get("/{project_id}", response_model=Project)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
) -> ProjectModel:
    """
    Retrieve a single project record by its primary key ID.
    
    This endpoint fetches the complete details of one specific project, which is useful when
    drilling down from a list view to examine the full context of a particular initiative
    including all metadata, timeline information, and descriptive fields that might be truncated
    in list views or summary displays.
    
    Args:
        project_id: The primary key ID of the project to retrieve
        db: Database session injected by FastAPI's dependency system
    
    Returns:
        The Project object with the specified ID, containing all fields including full
        description and metadata that might be abbreviated in list views.
    
    Raises:
        HTTPException: 404 error if no project exists with the given ID
        HTTPException: 500 error if a database query fails for unexpected reasons
    """
    try:
        # Query for the project using the primary key. The filter on the primary key is highly
        # efficient due to the automatic index, and first() returns None if not found.
        project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
        
        # If the project doesn't exist, return a 404 Not Found error with a clear message.
        # This is the standard HTTP response for "the resource you asked for doesn't exist".
        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found"
            )
        
        return project
        
    except HTTPException:
        # Re-raise HTTPExceptions that we explicitly created so they propagate correctly to
        # FastAPI's error handling with the right status codes and messages.
        raise
        
    except SQLAlchemyError as e:
        # For unexpected database errors, provide a 500 error with details that help debugging
        # while avoiding exposure of sensitive internal implementation details.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error while fetching project: {str(e)}"
        )


@router.post("/", response_model=Project, status_code=status.HTTP_201_CREATED)
def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
) -> ProjectModel:
    """
    Create a new project record in the system.
    
    This endpoint creates a new project with the provided details including its relationship
    to a subsidy (optional), timeline, ownership, and status. Projects represent the concrete
    initiatives or programs that subsidies enable, so creating a project is typically one of
    the first operational steps after a subsidy has been approved and allocated.
    
    The metadata field can store additional JSON-stringified attributes for program-specific
    needs without requiring schema migrations. For production PostgreSQL deployments, consider
    migrating the metadata field to JSONB type if you need to query or index specific metadata
    attributes efficiently, as JSONB supports native JSON operations and GIN indexing.
    
    Schema changes should always be applied via Alembic migrations rather than modifying models
    directly in production, ensuring proper version control and rollback capabilities.
    
    Args:
        project_data: The project details including name and optional fields like subsidy_id,
                     description, owner, timeline, and status
        db: Database session injected by FastAPI's dependency system
    
    Returns:
        The newly created Project object with its auto-generated ID and timestamps
    
    Raises:
        HTTPException: 400 error if the input data is invalid or violates database constraints
        HTTPException: 500 error if an unexpected database error occurs during creation
    """
    try:
        # Create a new ORM instance from the Pydantic input model. We use **project_data.dict()
        # to unpack the validated fields into keyword arguments for the constructor. Pydantic
        # has already validated required fields and type constraints before we reach this point.
        new_project = ProjectModel(**project_data.dict())
        
        # Add the new instance to the session's pending changes. This doesn't execute SQL yet,
        # just marks the object to be inserted when we commit.
        db.add(new_project)
        
        # Commit the transaction to persist the new project to the database. This is when the
        # actual INSERT statement executes, and the database assigns the auto-generated ID and
        # sets the created_at and updated_at timestamps using server defaults.
        db.commit()
        
        # Refresh the object to load database-generated values (id, created_at, updated_at)
        # back into the Python object. This ensures the returned object has all fields populated
        # correctly, including values that were set by database defaults.
        db.refresh(new_project)
        
        return new_project
        
    except SQLAlchemyError as e:
        # If anything goes wrong during the database operation (constraint violations, foreign
        # key errors, connection issues, etc.), rollback the transaction to undo any partial
        # changes and maintain database consistency.
        db.rollback()
        
        # Check if this looks like a validation/constraint error versus a system error. For
        # constraint errors we return 400 Bad Request; for system errors we return 500.
        error_message = str(e).lower()
        if "constraint" in error_message or "foreign key" in error_message or "null" in error_message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid project data: {str(e)}"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error while creating project: {str(e)}"
            )


@router.patch("/{project_id}", response_model=Project)
def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    db: Session = Depends(get_db),
) -> ProjectModel:
    """
    Partially update an existing project record.
    
    This endpoint allows updating specific fields of a project without requiring all fields to
    be provided. Only the fields included in the request body will be modified; unspecified
    fields retain their current values. This is useful for incremental updates like changing a
    project's status, extending its timeline, or updating ownership as organizational structures
    evolve.
    
    The partial update pattern is particularly valuable for projects because they often undergo
    many small changes throughout their lifecycle (status transitions, timeline adjustments,
    metadata additions) without needing to send the entire project payload each time. This
    reduces bandwidth and simplifies client code.
    
    Args:
        project_id: The primary key ID of the project to update
        project_update: The fields to update (all optional)
        db: Database session injected by FastAPI's dependency system
    
    Returns:
        The updated Project object with all current field values
    
    Raises:
        HTTPException: 404 error if the project doesn't exist
        HTTPException: 400 error if the update data is invalid
        HTTPException: 500 error if an unexpected database error occurs
    """
    try:
        # Fetch the existing project record. We need the full object so we can update only
        # the fields that were provided in the request.
        project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
        
        # If the project doesn't exist, return 404 before attempting any updates.
        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found"
            )
        
        # Extract only the fields that were actually provided in the request. The exclude_unset
        # parameter ensures we only get fields that the client explicitly set, not defaults from
        # the Pydantic model. This enables true partial updates where only specified fields change.
        update_data = project_update.dict(exclude_unset=True)
        
        # Apply each update by setting the corresponding attribute on the ORM object. This
        # approach works well for partial updates where we only modify the fields that were
        # provided in the request, leaving everything else unchanged.
        for field, value in update_data.items():
            setattr(project, field, value)
        
        # Commit the transaction to persist the updates. The updated_at timestamp should be
        # automatically refreshed by the database's onupdate trigger configured in the model.
        db.commit()
        
        # Refresh to ensure we have the latest values including any database-generated fields
        # like updated_at that may have changed during the commit.
        db.refresh(project)
        
        return project
        
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
                detail=f"Database error while updating project: {str(e)}"
            )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
) -> Response:
    """
    Delete a project record from the system.
    
    This endpoint performs a hard delete, permanently removing the project record from the
    database. For production systems, especially those dealing with government subsidies and
    financial tracking, you should strongly consider implementing soft deletion instead (e.g.,
    an is_deleted flag or status='archived') to maintain a complete audit trail of all projects
    that ever existed, even if they were later cancelled or superseded.
    
    Hard deletion is appropriate for correcting data entry mistakes during development or
    removing test data, but should be used very cautiously in production environments where
    regulatory compliance and audit requirements may mandate maintaining historical records of
    all projects and their relationships to subsidies and disbursements.
    
    Args:
        project_id: The primary key ID of the project to delete
        db: Database session injected by FastAPI's dependency system
    
    Returns:
        Empty response with 204 No Content status code on success
    
    Raises:
        HTTPException: 404 error if the project doesn't exist
        HTTPException: 500 error if an unexpected database error occurs
    """
    try:
        # Fetch the project to be deleted. We need to verify it exists before attempting
        # deletion, otherwise we'd return success even when deleting a non-existent record
        # which could mask bugs in client code.
        project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
        
        # If the project doesn't exist, return 404. It's important to distinguish between
        # "successfully deleted" and "there was nothing to delete" for client applications.
        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found"
            )
        
        # Delete the record and commit the transaction. This permanently removes the row from
        # the database table. For production systems tracking government subsidies and financial
        # programs, strongly consider implementing soft deletion (is_deleted flag or archived
        # status) instead to preserve the complete historical record for audit and compliance.
        db.delete(project)
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
            detail=f"Database error while deleting project: {str(e)}"
        )