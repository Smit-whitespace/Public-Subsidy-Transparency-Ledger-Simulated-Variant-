"""
backend/tests/test_subsidies.py
"""

import pytest
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database.connection import Base
from backend.services.subsidy_service import (
    normalize_amount,
    create_subsidy,
    get_subsidy_by_id,
    update_subsidy,
    delete_subsidy,
)
from backend.schemas.subsidy import SubsidyCreate, SubsidyUpdate


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


def test_normalize_amount():

    assert normalize_amount("1000.5") == Decimal("1000.50")
    assert normalize_amount(1000.567) == Decimal("1000.57")
    assert normalize_amount(Decimal("999")) == Decimal("999.00")


def test_create_and_get_subsidy(db_session):

    subsidy = create_subsidy(
        db_session,
        SubsidyCreate(
            title="Grant A",
            recipient="Dept X",
            sector="general",
            total_allocation="50000.00",
            currency="INR",
            status="active",
            is_active=True
        )
    )

    assert subsidy.id is not None
    assert subsidy.total_allocation == Decimal("50000.00")

    fetched = get_subsidy_by_id(db_session, subsidy.id)

    assert fetched.id == subsidy.id


def test_update_subsidy(db_session):

    subsidy = create_subsidy(
        db_session,
        SubsidyCreate(
            title="Initial",
            recipient="Dept",
            sector="general",
            total_allocation="1000",
            currency="INR",
            status="active",
            is_active=True
        )
    )

    updated = update_subsidy(
        db_session,
        subsidy.id,
        SubsidyUpdate(total_allocation="2500")
    )

    assert updated.total_allocation == Decimal("2500.00")


def test_delete_subsidy(db_session):

    subsidy = create_subsidy(
        db_session,
        SubsidyCreate(
            title="Delete",
            recipient="Dept",
            sector="general",
            total_allocation="100",
            currency="INR",
            status="active",
            is_active=True
        )
    )

    delete_subsidy(db_session, subsidy.id)

    assert get_subsidy_by_id(db_session, subsidy.id) is None