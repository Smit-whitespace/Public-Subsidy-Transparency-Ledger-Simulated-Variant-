"""
backend/test/test_projects.py

Unit tests for project service: CRUD operations, filtering, counting, and duration summary calculations.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database.connection import Base
from backend.services.project_service import (
    create_project,
    get_project_by_id,
    list_projects,
    update_project,
    delete_project,
    count_projects,
    active_projects_duration_summary,
)
from backend.schemas.project import ProjectCreate, ProjectUpdate


@pytest.fixture
def db_session():
    """
    Create an in-memory SQLite database for isolated testing.
    
    Yields:
        SQLAlchemy Session instance with all tables created
    """
    # Create in-memory SQLite engine
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )
    
    # Create session factory
    SessionLocal = sessionmaker(bind=engine)
    
    # Create all tables from Base metadata
    Base.metadata.create_all(bind=engine)
    
    # Create and yield session
    session = SessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def test_create_and_get_project(db_session) -> None:
    """
    Test creating and retrieving a project record.
    
    Verifies that:
    - Project can be created successfully
    - Fields are stored correctly
    - Record can be retrieved by ID
    """
    # Create project
    project_in = ProjectCreate(
        name="Test Project",
        subsidy_id=None,
        owner="dept-1",
        status="planned"
    )
    
    p = create_project(db_session, project_in)
    
    # Assert project was created
    assert p.id is not None
    assert p.name == "Test Project"
    assert p.owner == "dept-1"
    assert p.status == "planned"
    
    # Retrieve by ID
    fetched = get_project_by_id(db_session, p.id)
    assert fetched is not None
    assert fetched.id == p.id
    assert fetched.name == p.name


def test_list_projects_filters_and_pagination(db_session) -> None:
    """
    Test listing projects with filters and pagination.
    
    Verifies:
    - Filtering by owner works
    - Filtering by status works
    - Pagination respects limit
    - Results are ordered by created_at descending
    """
    # Create multiple projects with different owners and statuses
    p1 = create_project(db_session, ProjectCreate(
        name="Project Alpha", owner="dept-1", status="planned"
    ))
    p2 = create_project(db_session, ProjectCreate(
        name="Project Beta", owner="dept-1", status="active"
    ))
    p3 = create_project(db_session, ProjectCreate(
        name="Project Gamma", owner="dept-2", status="planned"
    ))
    p4 = create_project(db_session, ProjectCreate(
        name="Project Delta", owner="dept-1", status="planned"
    ))
    
    # Test filtering by owner
    results = list_projects(db_session, owner="dept-1", limit=10, offset=0)
    assert len(results) == 3
    assert all(p.owner == "dept-1" for p in results)
    
    # Test filtering by status with limit
    results = list_projects(db_session, status="planned", limit=2, offset=0)
    assert len(results) == 2
    assert all(p.status == "planned" for p in results)
    
    # Verify ordering by created_at descending (most recent first)
    all_results = list_projects(db_session, limit=10, offset=0)
    if len(all_results) >= 2:
        assert all_results[0].created_at >= all_results[1].created_at


def test_update_project_changes_fields(db_session) -> None:
    """
    Test updating project fields.
    
    Verifies that name, status, and owner can be updated successfully.
    """
    # Create initial project
    project_in = ProjectCreate(
        name="Original Name",
        owner="original-owner",
        status="planned"
    )
    p = create_project(db_session, project_in)
    
    # Update fields
    changes = ProjectUpdate(
        name="Updated Name",
        owner="new-owner",
        status="active"
    )
    
    updated = update_project(db_session, p.id, changes)
    
    # Assert updates were applied
    assert updated.id == p.id
    assert updated.name == "Updated Name"
    assert updated.owner == "new-owner"
    assert updated.status == "active"
    
    # Verify persistence
    fetched = get_project_by_id(db_session, p.id)
    assert fetched.name == "Updated Name"
    assert fetched.owner == "new-owner"
    assert fetched.status == "active"


def test_delete_project(db_session) -> None:
    """
    Test deleting a project record.
    
    Verifies that:
    - Project can be deleted
    - Deleted record no longer exists in database
    """
    # Create project
    project_in = ProjectCreate(
        name="To Delete",
        owner="dept-1",
        status="planned"
    )
    p = create_project(db_session, project_in)
    project_id = p.id
    
    # Verify it exists
    assert get_project_by_id(db_session, project_id) is not None
    
    # Delete project
    delete_project(db_session, project_id)
    
    # Verify it no longer exists
    assert get_project_by_id(db_session, project_id) is None


def test_count_projects_and_filters(db_session) -> None:
    """
    Test counting projects with and without filters.
    
    Verifies:
    - Total count is correct
    - Filtered counts work correctly
    """
    # Create projects with different owners
    create_project(db_session, ProjectCreate(
        name="Project 1", owner="dept-1", status="planned"
    ))
    create_project(db_session, ProjectCreate(
        name="Project 2", owner="dept-1", status="active"
    ))
    create_project(db_session, ProjectCreate(
        name="Project 3", owner="dept-2", status="planned"
    ))
    
    # Test total count
    total = count_projects(db_session)
    assert total == 3
    
    # Test count with owner filter
    dept1_count = count_projects(db_session, owner="dept-1")
    assert dept1_count == 2
    
    # Test count with status filter
    planned_count = count_projects(db_session, status="planned")
    assert planned_count == 2


def test_active_projects_duration_summary(db_session) -> None:
    """
    Test calculating duration summary for active projects.
    
    Verifies:
    - Active count is correct
    - Average duration is calculated correctly for projects with both dates
    - Projects without end_date are counted as active but don't affect avg duration
    - Owner filtering works
    """
    now = datetime.utcnow()
    
    # Create active project with both dates (10 day duration)
    p1 = create_project(db_session, ProjectCreate(
        name="Active with dates",
        owner="engineering",
        status="active",
        start_date=now - timedelta(days=10),
        end_date=now
    ))
    
    # Create active project without end_date
    p2 = create_project(db_session, ProjectCreate(
        name="Active no end",
        owner="engineering",
        status="active",
        start_date=now - timedelta(days=5)
    ))
    
    # Create non-active project with both dates (shouldn't count as active)
    p3 = create_project(db_session, ProjectCreate(
        name="Completed",
        owner="engineering",
        status="completed",
        start_date=now - timedelta(days=20),
        end_date=now - timedelta(days=10)
    ))
    
    # Create another active project with both dates (20 day duration)
    p4 = create_project(db_session, ProjectCreate(
        name="Active long",
        owner="engineering",
        status="active",
        start_date=now - timedelta(days=20),
        end_date=now
    ))
    
    # Test summary without owner filter
    summary = active_projects_duration_summary(db_session)
    
    # Should have 3 active projects (p1, p2, p4)
    assert summary["active_count"] == 3
    
    # Average duration should be (10 + 20) / 2 = 15 days
    # Only p1 and p4 have both dates; p2 has no end_date
    assert summary["avg_duration_days"] is not None
    assert abs(summary["avg_duration_days"] - 15.0) < 0.1
    
    # Test summary with owner filter
    summary_filtered = active_projects_duration_summary(db_session, owner="engineering")
    assert summary_filtered["owner"] == "engineering"
    assert summary_filtered["active_count"] == 3


def test_update_nonexistent_project_raises(db_session) -> None:
    """
    Test that updating a non-existent project raises ValueError.
    """
    changes = ProjectUpdate(name="Should Fail")
    
    with pytest.raises(ValueError, match="Project not found"):
        update_project(db_session, 99999, changes)


def test_delete_nonexistent_project_raises(db_session) -> None:
    """
    Test that deleting a non-existent project raises ValueError.
    """
    with pytest.raises(ValueError, match="Project not found"):
        delete_project(db_session, 99999)


# Run tests: pytest -q backend/test/test_projects.py