"""
backend/services/project_service.py

Project service: transactional helpers to create, fetch, list, update, delete, and aggregate Project records.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func

from backend.models.project import Project as ProjectModel
from backend.schemas.project import ProjectCreate, ProjectUpdate, Project as ProjectSchema


# Maximum limit for list queries to prevent resource exhaustion
MAX_LIST_LIMIT = 1000


def create_project(db: Session, project_in: ProjectCreate, commit: bool = True) -> ProjectModel:
    """
    Create and persist a new project record.
    
    Args:
        db: SQLAlchemy session
        project_in: Validated ProjectCreate schema
        commit: Whether to commit immediately (default True)
    
    Returns:
        Created ProjectModel instance
    
    Raises:
        RuntimeError: If database operation fails
    """
    try:
        # Create project model with explicit field mapping
        # Assume Pydantic already normalized inputs (name, status, metadata)
        project = ProjectModel(
            name=project_in.name,
            subsidy_id=project_in.subsidy_id,
            description=project_in.description,
            metadata=project_in.metadata,
            owner=project_in.owner,
            start_date=project_in.start_date,
            end_date=project_in.end_date,
            status=project_in.status
        )
        
        db.add(project)
        
        if commit:
            db.commit()
            db.refresh(project)
        
        return project
        
    except SQLAlchemyError as e:
        db.rollback()
        raise RuntimeError("DB error while creating project")


def get_project_by_id(db: Session, project_id: int) -> Optional[ProjectModel]:
    """
    Retrieve a single project record by ID.
    
    Args:
        db: SQLAlchemy session
        project_id: Primary key of project record
    
    Returns:
        ProjectModel if found, None otherwise
    """
    return db.query(ProjectModel).filter_by(id=project_id).first()


def list_projects(
    db: Session,
    *,
    subsidy_id: Optional[int] = None,
    owner: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> List[ProjectModel]:
    """
    List project records with optional filters and pagination.
    
    Args:
        db: SQLAlchemy session
        subsidy_id: Filter by subsidy ID (optional)
        owner: Filter by owner (optional)
        status: Filter by status (optional)
        limit: Maximum number of records to return (must be >= 1 and <= MAX_LIST_LIMIT)
        offset: Number of records to skip (must be >= 0)
    
    Returns:
        List of ProjectModel instances
    
    Raises:
        ValueError: If limit or offset are invalid
        RuntimeError: If database operation fails
    """
    if limit < 1 or limit > MAX_LIST_LIMIT:
        raise ValueError(f"limit must be >= 1 and <= {MAX_LIST_LIMIT}, got {limit}")
    if offset < 0:
        raise ValueError(f"offset must be >= 0, got {offset}")
    
    try:
        query = db.query(ProjectModel)
        
        if subsidy_id is not None:
            query = query.filter(ProjectModel.subsidy_id == subsidy_id)
        
        if owner is not None:
            query = query.filter(ProjectModel.owner == owner)
        
        if status is not None:
            query = query.filter(ProjectModel.status == status)
        
        # Order by created_at descending (most recent first)
        query = query.order_by(ProjectModel.created_at.desc())
        query = query.limit(limit).offset(offset)
        
        return query.all()
        
    except SQLAlchemyError as e:
        raise RuntimeError("DB error while listing projects")


def update_project(
    db: Session,
    project_id: int,
    changes: ProjectUpdate,
    commit: bool = True
) -> ProjectModel:
    """
    Update an existing project record with partial changes.
    
    Args:
        db: SQLAlchemy session
        project_id: Primary key of project to update
        changes: ProjectUpdate schema with fields to update
        commit: Whether to commit immediately (default True)
    
    Returns:
        Updated ProjectModel instance
    
    Raises:
        ValueError: If project not found
        RuntimeError: If database operation fails
    """
    project = get_project_by_id(db, project_id)
    if not project:
        raise ValueError("Project not found")
    
    try:
        update_data = changes.dict(exclude_unset=True)
        
        # Apply updates to model
        # Assume metadata is already normalized by Pydantic validators if provided
        for field, value in update_data.items():
            setattr(project, field, value)
        
        if commit:
            db.commit()
            db.refresh(project)
        
        return project
        
    except SQLAlchemyError as e:
        db.rollback()
        raise RuntimeError("DB error while updating project")


def delete_project(db: Session, project_id: int, commit: bool = True) -> None:
    """
    Delete a project record.
    
    Note: This performs a hard delete. Production systems may prefer soft-delete
    (is_deleted flag) to maintain audit trail and referential integrity.
    
    Args:
        db: SQLAlchemy session
        project_id: Primary key of project to delete
        commit: Whether to commit immediately (default True)
    
    Raises:
        ValueError: If project not found
        RuntimeError: If database operation fails
    """
    project = get_project_by_id(db, project_id)
    if not project:
        raise ValueError("Project not found")
    
    try:
        db.delete(project)
        
        if commit:
            db.commit()
            
    except SQLAlchemyError as e:
        db.rollback()
        raise RuntimeError("DB error while deleting project")


def count_projects(
    db: Session,
    *,
    subsidy_id: Optional[int] = None,
    owner: Optional[str] = None,
    status: Optional[str] = None
) -> int:
    """
    Count project records matching the given filters.
    
    Args:
        db: SQLAlchemy session
        subsidy_id: Filter by subsidy ID (optional)
        owner: Filter by owner (optional)
        status: Filter by status (optional)
    
    Returns:
        Total count of matching records
    """
    query = db.query(func.count(ProjectModel.id))
    
    if subsidy_id is not None:
        query = query.filter(ProjectModel.subsidy_id == subsidy_id)
    
    if owner is not None:
        query = query.filter(ProjectModel.owner == owner)
    
    if status is not None:
        query = query.filter(ProjectModel.status == status)
    
    return query.scalar() or 0


def active_projects_duration_summary(db: Session, *, owner: Optional[str] = None) -> Dict[str, Any]:
    """
    Compute summary statistics for active projects with defined durations.
    
    Returns count of active projects and average duration in days for projects
    that have both start_date and end_date defined.
    
    Args:
        db: SQLAlchemy session
        owner: Filter by owner (optional)
    
    Returns:
        Dict with keys:
        - owner: the owner filter or None
        - active_count: number of active projects (status='active')
        - avg_duration_days: average duration in days, or None if no projects with both dates
    """
    try:
        # Count active projects
        active_query = db.query(func.count(ProjectModel.id)).filter(
            ProjectModel.status == 'active'
        )
        if owner is not None:
            active_query = active_query.filter(ProjectModel.owner == owner)
        
        active_count = active_query.scalar() or 0
        
        # Compute average duration for projects with both start and end dates
        duration_query = db.query(ProjectModel).filter(
            ProjectModel.start_date.isnot(None),
            ProjectModel.end_date.isnot(None)
        )
        if owner is not None:
            duration_query = duration_query.filter(ProjectModel.owner == owner)
        
        projects_with_dates = duration_query.all()
        
        avg_duration_days = None
        if projects_with_dates:
            # Compute average duration in days using Python
            durations = [
                (proj.end_date - proj.start_date).days
                for proj in projects_with_dates
                if proj.end_date and proj.start_date
            ]
            if durations:
                avg_duration_days = sum(durations) / len(durations)
        
        return {
            "owner": owner,
            "active_count": active_count,
            "avg_duration_days": avg_duration_days
        }
        
    except SQLAlchemyError as e:
        raise RuntimeError("DB error while computing project duration summary")


__all__ = [
    "create_project",
    "get_project_by_id",
    "list_projects",
    "update_project",
    "delete_project",
    "count_projects",
    "active_projects_duration_summary"
]

# Test hint: use an in-memory sqlite Session, call create_project(db, ProjectCreate(...)), then assert get_project_by_id returns expected values and count_projects increments.