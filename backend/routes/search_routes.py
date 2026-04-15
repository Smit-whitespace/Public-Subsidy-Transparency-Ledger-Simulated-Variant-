"""
backend/routes/search_routes.py

Generic search and autocomplete endpoints for the subsidy management system.

This module provides V1 search functionality powered by direct PostgreSQL queries using SQLAlchemy.
The search is simple but functional, using ILIKE pattern matching for text fields and supporting
multi-entity queries across subsidies, projects, disbursements, and audit records.

IMPORTANT: This is a V1 implementation suitable for small to medium datasets. For production systems
with large data volumes or complex search requirements, consider migrating to a dedicated search
engine like Elasticsearch with event-driven indexing via Kafka or similar message bus. The current
ILIKE-based approach doesn't scale well beyond ~100k records and doesn't support advanced features
like relevance scoring, fuzzy matching, or faceted search.

The endpoints are designed to support frontend search UIs and autocomplete fields, providing both
broad multi-entity search and focused field-specific suggestions. All queries are carefully sanitized
to prevent SQL injection, with explicit whitelists for sortable fields and suggestion targets.

Test the search endpoint:
    curl "http://localhost:8000/api/search?q=water&limit=10"
Test the autocomplete endpoint:
    curl "http://localhost:8000/api/search/suggest?field=subsidy_title&q=edu&limit=5"
"""

from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.models.audit import AuditRecord as AuditRecordModel
from backend.models.disbursement import Disbursement as DisbursementModel
from backend.models.project import Project as ProjectModel
from backend.models.subsidy import Subsidy as SubsidyModel
from backend.schemas.audit import AuditRecord
from backend.schemas.disbursement import Disbursement
from backend.schemas.project import Project
from backend.schemas.subsidy import Subsidy


router = APIRouter( tags=["search"])


# Whitelists for safe sorting and field suggestions to prevent SQL injection.
# Only fields in these dictionaries can be used for sorting or autocomplete queries.
SORTABLE_FIELDS = {
    "subsidy": ["created_at", "updated_at", "amount", "title"],
    "project": ["created_at", "updated_at", "name", "start_date"],
    "disbursement": ["date", "amount", "created_at"],
    "audit": ["created_at"],
}

SUGGESTION_FIELDS = {
    "subsidy_title": (SubsidyModel, "title"),
    "subsidy_recipient": (SubsidyModel, "recipient"),
    "project_name": (ProjectModel, "name"),
    "project_owner": (ProjectModel, "owner"),
    "disbursement_reference": (DisbursementModel, "reference"),
}


def _search_subsidies(
    db: Session,
    query_term: Optional[str],
    limit: int,
    offset: int,
    sort_by: Optional[str],
    order: str,
) -> List[Dict[str, Any]]:
    """
    Search subsidies by title, recipient, and description.
    
    This helper function builds a query that searches across the main text fields of subsidies
    using case-insensitive ILIKE pattern matching. For V1 we use simple ILIKE which works well
    for small datasets but should be replaced with PostgreSQL full-text search or Elasticsearch
    for production scale.
    
    Args:
        db: Database session
        query_term: Optional search term to match against text fields
        limit: Maximum results to return
        offset: Pagination offset
        sort_by: Optional sort field from the whitelist
        order: Sort direction (asc or desc)
    
    Returns:
        List of subsidy dictionaries ready for JSON serialization
    """
    query = db.query(SubsidyModel)
    
    # Apply text search filters if a query term was provided. We use ILIKE for case-insensitive
    # matching with wildcards, which is simple but not performant at scale. The or_() combines
    # multiple conditions so a match on any field will include the record.
    if query_term:
        search_pattern = f"%{query_term}%"
        query = query.filter(
            or_(
                SubsidyModel.title.ilike(search_pattern),
                SubsidyModel.recipient.ilike(search_pattern),
                SubsidyModel.description.ilike(search_pattern),
            )
        )
    
    # Apply sorting if a valid sort field was specified and it's in the whitelist. We validate
    # against the whitelist to prevent SQL injection from untrusted sort_by parameters.
    if sort_by and sort_by in SORTABLE_FIELDS["subsidy"]:
        sort_column = getattr(SubsidyModel, sort_by)
        if order == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())
    else:
        # Default sort by created_at descending to show newest first
        query = query.order_by(SubsidyModel.created_at.desc())
    
    # Apply pagination and execute the query
    results = query.offset(offset).limit(limit).all()
    
    # Convert ORM objects to dictionaries for JSON serialization. We use the to_dict() method
    # defined on the model which handles Decimal and datetime conversions properly.
    return [subsidy.to_dict() for subsidy in results]


def _search_projects(
    db: Session,
    query_term: Optional[str],
    limit: int,
    offset: int,
    sort_by: Optional[str],
    order: str,
) -> List[Dict[str, Any]]:
    """
    Search projects by name, owner, and description.
    
    Similar to subsidy search, this uses ILIKE pattern matching across project text fields.
    Projects are searchable by their name, owner (department/organization), and description,
    which covers the most common ways users need to find project records.
    
    Args:
        db: Database session
        query_term: Optional search term to match against text fields
        limit: Maximum results to return
        offset: Pagination offset
        sort_by: Optional sort field from the whitelist
        order: Sort direction (asc or desc)
    
    Returns:
        List of project dictionaries ready for JSON serialization
    """
    query = db.query(ProjectModel)
    
    # Apply text search filters across project text fields
    if query_term:
        search_pattern = f"%{query_term}%"
        query = query.filter(
            or_(
                ProjectModel.name.ilike(search_pattern),
                ProjectModel.owner.ilike(search_pattern),
                ProjectModel.description.ilike(search_pattern),
            )
        )
    
    # Apply safe sorting from whitelist
    if sort_by and sort_by in SORTABLE_FIELDS["project"]:
        sort_column = getattr(ProjectModel, sort_by)
        if order == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(ProjectModel.created_at.desc())
    
    results = query.offset(offset).limit(limit).all()
    return [project.to_dict() for project in results]


def _search_disbursements(
    db: Session,
    query_term: Optional[str],
    limit: int,
    offset: int,
    sort_by: Optional[str],
    order: str,
) -> List[Dict[str, Any]]:
    """
    Search disbursements by reference and optionally by amount if query is numeric.
    
    Disbursements are primarily identified by their external reference codes, so we search that
    field. If the query term looks like a number, we also check if it matches the disbursement
    amount, which is useful when users remember "that $5000 payment" but not the reference code.
    
    Args:
        db: Database session
        query_term: Optional search term to match against reference or amount
        limit: Maximum results to return
        offset: Pagination offset
        sort_by: Optional sort field from the whitelist
        order: Sort direction (asc or desc)
    
    Returns:
        List of disbursement dictionaries ready for JSON serialization
    """
    query = db.query(DisbursementModel)
    
    # Apply search filters for disbursements
    if query_term:
        search_pattern = f"%{query_term}%"
        filters = [DisbursementModel.reference.ilike(search_pattern)]
        
        # If the query term looks like a number, also search by amount. We try to parse it
        # as a Decimal for exact matching, but fail gracefully if it's not a valid number.
        try:
            amount_value = Decimal(query_term)
            filters.append(DisbursementModel.amount == amount_value)
        except (InvalidOperation, ValueError):
            # Query term isn't a valid number, so skip the amount filter
            pass
        
        query = query.filter(or_(*filters))
    
    # Apply safe sorting from whitelist
    if sort_by and sort_by in SORTABLE_FIELDS["disbursement"]:
        sort_column = getattr(DisbursementModel, sort_by)
        if order == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(DisbursementModel.date.desc())
    
    results = query.offset(offset).limit(limit).all()
    return [disbursement.to_dict() for disbursement in results]


def _search_audits(
    db: Session,
    query_term: Optional[str],
    limit: int,
    offset: int,
    sort_by: Optional[str],
    order: str,
) -> List[Dict[str, Any]]:
    """
    Search audit records by entity, action, and details.
    
    Audit records are searchable by the entity type they reference (e.g., "subsidy"), the
    action that was performed (e.g., "approve"), and the details field which may contain
    additional context about what changed. This enables queries like "show me all approval
    actions" or "find audits mentioning user #42".
    
    Args:
        db: Database session
        query_term: Optional search term to match against audit fields
        limit: Maximum results to return
        offset: Pagination offset
        sort_by: Optional sort field from the whitelist
        order: Sort direction (asc or desc)
    
    Returns:
        List of audit record dictionaries ready for JSON serialization
    """
    query = db.query(AuditRecordModel)
    
    # Apply search filters for audit records
    if query_term:
        search_pattern = f"%{query_term}%"
        query = query.filter(
            or_(
                AuditRecordModel.entity.ilike(search_pattern),
                AuditRecordModel.action.ilike(search_pattern),
                AuditRecordModel.details.ilike(search_pattern),
            )
        )
    
    # Apply safe sorting from whitelist
    if sort_by and sort_by in SORTABLE_FIELDS["audit"]:
        sort_column = getattr(AuditRecordModel, sort_by)
        if order == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(AuditRecordModel.created_at.desc())
    
    results = query.offset(offset).limit(limit).all()
    return [audit.to_dict() for audit in results]


@router.get("/")
def search_entities(
    q: Optional[str] = Query(None, description="Free-text search query"),
    entity: Optional[str] = Query(None, description="Entity type to search: subsidy, project, disbursement, audit"),
    limit: int = Query(20, ge=1, le=200, description="Maximum results per entity"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    sort_by: Optional[str] = Query(None, description="Field to sort by (entity-specific)"),
    order: str = Query("desc", regex="^(asc|desc)$", description="Sort order: asc or desc"),
    db: Session = Depends(get_db),
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Generic multi-entity search across subsidies, projects, disbursements, and audits.
    
    This endpoint provides a unified search interface that can query one or all entity types
    in a single request. It's designed to power search bars and multi-faceted search UIs where
    users want to find records across the entire system without knowing which entity type they're
    looking for in advance.
    
    The search uses case-insensitive ILIKE pattern matching, which is simple and works well for
    V1 but should be replaced with PostgreSQL full-text search (using tsvector/tsquery) or a
    dedicated search engine like Elasticsearch for production deployments with large datasets.
    
    TODO: For V2, replace with event-driven Elasticsearch indexing. Set up a Kafka topic that
    receives events when entities are created/updated, and have a consumer service update the
    Elasticsearch index. This will provide better performance, relevance scoring, and advanced
    features like fuzzy matching and faceted search.
    
    Args:
        q: The search query term to match against entity text fields
        entity: Optional entity type filter (subsidy, project, disbursement, audit). If not
               provided, searches all entity types and returns grouped results.
        limit: Maximum number of results to return per entity type
        offset: Number of results to skip for pagination
        sort_by: Optional field name to sort by (must be in the entity's whitelist)
        order: Sort direction, either "asc" or "desc"
        db: Database session injected by FastAPI's dependency system
    
    Returns:
        A dictionary mapping entity type names to lists of matching records. The structure is:
        {
            "subsidies": [list of subsidy dicts],
            "projects": [list of project dicts],
            "disbursements": [list of disbursement dicts],
            "audits": [list of audit dicts]
        }
        If entity parameter is provided, only that entity's results are populated; others will
        be empty lists.
    
    Raises:
        HTTPException: 400 error if entity parameter is invalid
        HTTPException: 500 error if a database query fails
    """
    try:
        # Normalize entity parameter to lowercase for case-insensitive matching
        entity_filter = entity.lower() if entity else None
        
        # Validate entity parameter if provided
        if entity_filter and entity_filter not in ["subsidy", "project", "disbursement", "audit"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid entity type: {entity}. Must be one of: subsidy, project, disbursement, audit"
            )
        
        # Initialize result structure with all entity types
        results = {
            "subsidies": [],
            "projects": [],
            "disbursements": [],
            "audits": [],
        }
        
        # Search each entity type if no filter is specified, or just the specified entity.
        # This allows both broad "search everything" queries and focused single-entity searches.
        if not entity_filter or entity_filter == "subsidy":
            results["subsidies"] = _search_subsidies(db, q, limit, offset, sort_by, order)
        
        if not entity_filter or entity_filter == "project":
            results["projects"] = _search_projects(db, q, limit, offset, sort_by, order)
        
        if not entity_filter or entity_filter == "disbursement":
            results["disbursements"] = _search_disbursements(db, q, limit, offset, sort_by, order)
        
        if not entity_filter or entity_filter == "audit":
            results["audits"] = _search_audits(db, q, limit, offset, sort_by, order)
        
        return results
        
    except HTTPException:
        # Re-raise HTTPExceptions that we explicitly created so they propagate correctly
        raise
        
    except SQLAlchemyError as e:
        # Database errors during search should return 500 with a safe message
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error during search: {str(e)}"
        )


@router.get("/suggest")
def suggest_values(
    field: str = Query(..., description="Field to get suggestions for (e.g., subsidy_title, project_name)"),
    q: str = Query(..., description="Query prefix to match"),
    limit: int = Query(10, ge=1, le=50, description="Maximum suggestions to return"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Autocomplete suggestions for specific fields.
    
    This endpoint provides lightweight autocomplete functionality for frontend input fields.
    It returns distinct values from a specified field that match the query prefix, which is
    useful for helping users find existing values without typing the full text or making typos.
    
    Common use cases include autocompleting subsidy titles, recipient names, project owners, or
    disbursement reference codes based on what the user has typed so far. The suggestions come
    from actual values in the database, so users can see what options exist.
    
    The field parameter must be from a whitelist to prevent SQL injection. We only support
    suggestion fields that make sense for autocomplete - typically short text fields that users
    might want to search by or filter on.
    
    Pytest testing tip: Create a test using an in-memory SQLite database, seed it with a few
    rows containing known values, then test that suggest returns the expected prefixes.
    
    Args:
        field: The field to get suggestions for, must be in SUGGESTION_FIELDS whitelist
        q: The query prefix to match (e.g., "edu" to find values starting with "edu")
        limit: Maximum number of suggestions to return
        db: Database session injected by FastAPI's dependency system
    
    Returns:
        A dictionary with the field name and a list of suggestion strings:
        {
            "field": "subsidy_title",
            "suggestions": ["Education Grant 2024", "Educational Infrastructure", ...]
        }
    
    Raises:
        HTTPException: 400 error if field is not in the whitelist
        HTTPException: 500 error if a database query fails
    """
    try:
        # Validate that the field is in our whitelist to prevent SQL injection. Only fields
        # in SUGGESTION_FIELDS can be queried for autocomplete.
        if field not in SUGGESTION_FIELDS:
            valid_fields = ", ".join(SUGGESTION_FIELDS.keys())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid field: {field}. Valid fields are: {valid_fields}"
            )
        
        # Get the model class and column name from the whitelist
        model_class, column_name = SUGGESTION_FIELDS[field]
        column = getattr(model_class, column_name)
        
        # Build a query that gets distinct values matching the prefix. We use ILIKE for
        # case-insensitive prefix matching with the pattern "prefix%". The distinct() ensures
        # we don't return duplicate suggestions if multiple records have the same value.
        query = (
            db.query(column)
            .filter(column.ilike(f"{q}%"))
            .distinct()
            .limit(limit)
        )
        
        # Execute the query and extract the string values from the result rows
        results = query.all()
        suggestions = [row[0] for row in results if row[0]]  # Filter out None values
        
        return {
            "field": field,
            "suggestions": suggestions,
        }
        
    except HTTPException:
        # Re-raise HTTPExceptions that we explicitly created so they propagate correctly
        raise
        
    except SQLAlchemyError as e:
        # Database errors during suggestion lookup should return 500 with a safe message
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error during suggestion lookup: {str(e)}"
        )