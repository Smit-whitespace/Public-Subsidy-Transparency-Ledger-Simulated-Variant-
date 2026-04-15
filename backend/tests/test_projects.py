"""
backend/tests/test_projects.py
"""

import pytest
from datetime import datetime, timezone, timedelta
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
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )

    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def test_create_and_get_project(db_session):
    project = create_project(
        db_session,
        ProjectCreate(
            name="Test Project",
            owner="dept-1",
            status="planned",
            meta_data=None
        )
    )

    assert project.id is not None
    assert project.name == "Test Project"

    fetched = get_project_by_id(db_session, project.id)

    assert fetched is not None
    assert fetched.id == project.id


def test_list_projects_filters_and_pagination(db_session):

    create_project(db_session, ProjectCreate(name="A", owner="d1", status="planned"))
    create_project(db_session, ProjectCreate(name="B", owner="d1", status="active"))
    create_project(db_session, ProjectCreate(name="C", owner="d2", status="planned"))

    results = list_projects(db_session, owner="d1", limit=10, offset=0)

    assert len(results) == 2
    assert all(r.owner == "d1" for r in results)


def test_update_project_changes_fields(db_session):

    project = create_project(
        db_session,
        ProjectCreate(name="Original", owner="dept", status="planned")
    )

    updated = update_project(
        db_session,
        project.id,
        ProjectUpdate(name="Updated", owner="new", status="active")
    )

    assert updated.name == "Updated"
    assert updated.owner == "new"
    assert updated.status == "active"


def test_delete_project(db_session):

    project = create_project(
        db_session,
        ProjectCreate(name="Delete", owner="dept", status="planned")
    )

    delete_project(db_session, project.id)

    assert get_project_by_id(db_session, project.id) is None


def test_count_projects_and_filters(db_session):

    create_project(db_session, ProjectCreate(name="P1", owner="a", status="planned"))
    create_project(db_session, ProjectCreate(name="P2", owner="a", status="active"))
    create_project(db_session, ProjectCreate(name="P3", owner="b", status="planned"))

    assert count_projects(db_session) == 3
    assert count_projects(db_session, owner="a") == 2
    assert count_projects(db_session, status="planned") == 2


def test_active_projects_duration_summary(db_session):

    now = datetime.now(timezone.utc)

    create_project(
        db_session,
        ProjectCreate(
            name="Active",
            owner="eng",
            status="active",
            start_date=now - timedelta(days=10),
            end_date=now
        )
    )

    summary = active_projects_duration_summary(db_session)

    assert summary["active_count"] >= 1


def test_update_nonexistent_project_raises(db_session):

    with pytest.raises(ValueError):
        update_project(db_session, 9999, ProjectUpdate(name="fail"))


def test_delete_nonexistent_project_raises(db_session):

    with pytest.raises(ValueError):
        delete_project(db_session, 9999)