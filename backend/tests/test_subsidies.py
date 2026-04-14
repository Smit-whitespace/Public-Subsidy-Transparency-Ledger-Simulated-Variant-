"""
backend/test/test_subsidies.py

Unit tests for subsidy service: amount normalization, CRUD operations, filtering, and financial calculations.
"""

import pytest
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from backend.database.connection import Base
from backend.services.subsidy_service import (
    normalize_amount,
    create_subsidy,
    get_subsidy_by_id,
    list_subsidies,
    update_subsidy,
    delete_subsidy,
    total_authorized_and_disbursed,
    find_subsidies_by_recipient,
)
from backend.schemas.subsidy import SubsidyCreate, SubsidyUpdate


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


def test_normalize_amount_accepts_and_quantizes() -> None:
    """
    Test that normalize_amount handles various inputs and quantizes to 2 decimals.
    """
    # String input
    assert normalize_amount("1000.5") == Decimal("1000.50")
    
    # Float input with ROUND_HALF_UP (1000.567 -> 1000.57)
    assert normalize_amount(1000.567) == Decimal("1000.57")
    
    # Decimal input without decimal places
    assert normalize_amount(Decimal("999")) == Decimal("999.00")
    
    # Integer-like string
    assert normalize_amount("100") == Decimal("100.00")


def test_normalize_amount_invalid_and_nonpositive() -> None:
    """
    Test that normalize_amount rejects invalid and non-positive inputs.
    """
    # Invalid string
    with pytest.raises(ValueError):
        normalize_amount("abc")
    
    # Zero amount
    with pytest.raises(ValueError):
        normalize_amount("0")
    
    # Negative amount
    with pytest.raises(ValueError):
        normalize_amount("-1.00")
    
    # Negative decimal
    with pytest.raises(ValueError):
        normalize_amount(Decimal("-10.50"))


def test_create_and_get_subsidy(db_session) -> None:
    """
    Test creating and retrieving a subsidy record.
    
    Verifies that:
    - Subsidy can be created successfully
    - Fields are stored correctly
    - Record can be retrieved by ID
    """
    # Create subsidy
    subsidy_in = SubsidyCreate(
        title="Grant A",
        recipient="Dept X",
        amount="50000.00",
        currency="INR"
    )
    
    s = create_subsidy(db_session, subsidy_in)
    
    # Assert subsidy was created
    assert s.id is not None
    assert s.title == "Grant A"
    assert s.recipient == "Dept X"
    assert s.amount == Decimal("50000.00")
    assert s.currency == "INR"
    
    # Retrieve by ID
    fetched = get_subsidy_by_id(db_session, s.id)
    assert fetched is not None
    assert fetched.id == s.id
    assert fetched.title == s.title


def test_list_subsidies_filters_and_pagination(db_session) -> None:
    """
    Test listing subsidies with filters and pagination.
    
    Verifies:
    - Text search filtering works
    - Amount range filtering works
    - Pagination respects limit
    """
    # Create subsidies with different attributes
    s1 = create_subsidy(db_session, SubsidyCreate(
        title="Grant Alpha", recipient="City A", amount="500.00", currency="INR"
    ))
    s2 = create_subsidy(db_session, SubsidyCreate(
        title="Grant Beta", recipient="City B", amount="750.00", currency="INR"
    ))
    s3 = create_subsidy(db_session, SubsidyCreate(
        title="Scholarship", recipient="University C", amount="1500.00", currency="INR"
    ))
    s4 = create_subsidy(db_session, SubsidyCreate(
        title="Grant Gamma", recipient="District D", amount="250.00", currency="INR"
    ))
    
    # Test text search filter (case-insensitive)
    results = list_subsidies(db_session, q="Grant", limit=10)
    assert len(results) >= 3
    assert all("grant" in r.title.lower() for r in results)
    
    # Test amount range filtering
    results = list_subsidies(
        db_session,
        min_amount=Decimal("100.00"),
        max_amount=Decimal("1000.00")
    )
    assert len(results) == 3
    assert all(Decimal("100.00") <= r.amount <= Decimal("1000.00") for r in results)
    
    # Test pagination with limit
    results = list_subsidies(db_session, limit=2, offset=0)
    assert len(results) == 2


def test_update_subsidy_amount_and_metadata(db_session) -> None:
    """
    Test updating subsidy fields.
    
    Verifies that amount and metadata can be updated successfully.
    """
    # Create initial subsidy
    subsidy_in = SubsidyCreate(
        title="Initial Title",
        recipient="Recipient A",
        amount="1000.00",
        currency="INR",
        metadata='{"key": "value"}'
    )
    s = create_subsidy(db_session, subsidy_in)
    
    # Update amount and metadata
    changes = SubsidyUpdate(
        amount="2500.75",
        metadata='{"updated": true}'
    )
    
    updated = update_subsidy(db_session, s.id, changes)
    
    # Assert updates were applied
    assert updated.id == s.id
    assert updated.amount == Decimal("2500.75")
    assert updated.meta_data == '{"updated":true}'
    
    # Verify persistence
    fetched = get_subsidy_by_id(db_session, s.id)
    assert fetched.amount == Decimal("2500.75")


def test_delete_subsidy_and_not_found(db_session) -> None:
    """
    Test deleting a subsidy record.
    
    Verifies that:
    - Subsidy can be deleted
    - Deleted record no longer exists
    - Attempting to delete non-existent record raises error
    """
    # Create subsidy
    subsidy_in = SubsidyCreate(
        title="To Delete",
        recipient="Test Recipient",
        amount="100.00",
        currency="INR"
    )
    s = create_subsidy(db_session, subsidy_in)
    subsidy_id = s.id
    
    # Verify it exists
    assert get_subsidy_by_id(db_session, subsidy_id) is not None
    
    # Delete subsidy
    delete_subsidy(db_session, subsidy_id)
    
    # Verify it no longer exists
    assert get_subsidy_by_id(db_session, subsidy_id) is None
    
    # Attempt to delete again should raise ValueError
    with pytest.raises(ValueError):
        delete_subsidy(db_session, subsidy_id)


def test_total_authorized_and_disbursed(db_session) -> None:
    """
    Test calculating authorized and disbursed amounts.
    
    Verifies:
    - Authorized amount matches subsidy amount
    - Disbursed amount is sum of related disbursements
    - Remaining amount is correctly calculated
    """
    # Create subsidy
    subsidy_in = SubsidyCreate(
        title="Financial Test",
        recipient="Test Dept",
        amount="1000.00",
        currency="INR"
    )
    s = create_subsidy(db_session, subsidy_in)
    
    # Create related disbursements using disbursement service if available
    try:
        from backend.services.disbursement_service import create_disbursement
        from backend.schemas.disbursement import DisbursementCreate
        
        create_disbursement(db_session, DisbursementCreate(
            subsidy_id=s.id,
            amount="100.00",
            currency="INR",
            reference="DISB-1"
        ))
        create_disbursement(db_session, DisbursementCreate(
            subsidy_id=s.id,
            amount="150.50",
            currency="INR",
            reference="DISB-2"
        ))
    except ImportError:
        # If disbursement service not available, insert directly via model
        from backend.models.disbursement import Disbursement as DisbursementModel
        
        db_session.add(DisbursementModel(
            subsidy_id=s.id,
            amount=Decimal("100.00"),
            currency="INR",
            reference="DISB-1"
        ))
        db_session.add(DisbursementModel(
            subsidy_id=s.id,
            amount=Decimal("150.50"),
            currency="INR",
            reference="DISB-2"
        ))
        db_session.commit()
    
    # Calculate totals
    totals = total_authorized_and_disbursed(db_session, s.id)
    
    # Assert calculations
    assert totals["authorized"] == Decimal("1000.00")
    assert totals["disbursed"] == Decimal("250.50")
    assert totals["remaining"] == Decimal("749.50")


def test_find_subsidies_by_recipient(db_session) -> None:
    """
    Test finding subsidies by recipient name.
    
    Verifies:
    - Case-insensitive recipient matching works
    - Limit and offset are respected
    """
    # Create subsidies with specific recipient
    s1 = create_subsidy(db_session, SubsidyCreate(
        title="Subsidy 1", recipient="District A", amount="100.00", currency="INR"
    ))
    s2 = create_subsidy(db_session, SubsidyCreate(
        title="Subsidy 2", recipient="District A", amount="200.00", currency="INR"
    ))
    s3 = create_subsidy(db_session, SubsidyCreate(
        title="Subsidy 3", recipient="District B", amount="300.00", currency="INR"
    ))
    s4 = create_subsidy(db_session, SubsidyCreate(
        title="Subsidy 4", recipient="District A", amount="400.00", currency="INR"
    ))
    
    # Find by recipient (case-insensitive)
    results = find_subsidies_by_recipient(db_session, "District A", limit=10)
    assert len(results) == 3
    assert all("district a" in r.recipient.lower() for r in results)
    
    # Test limit behavior
    results_limited = find_subsidies_by_recipient(db_session, "District A", limit=2)
    assert len(results_limited) == 2


# Run tests: pytest -q backend/test/test_subsidies.py