"""
backend/services/search_service.py

Search service helpers: safe DB-backed search & suggestion helpers for subsidies, projects, disbursements, and audits. Designed for V1 (Postgres ILIKE) with clear extension points for ElasticSearch later.
"""

from typing import List, Optional, Dict, Any, Tuple
from decimal import Decimal, InvalidOperation
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from sqlalchemy.exc import SQLAlchemyError

from backend.models.subsidy import Subsidy as SubsidyModel
from backend.models.project import Project as ProjectModel
from backend.models.disbursement import Disbursement as DisbursementModel
from backend.models.audit import AuditRecord as AuditRecordModel


# Default and maximum limits for search results
DEFAULT_LIMIT = 20
MAX_LIMIT = 200

# Whitelist of sortable fields per entity to prevent SQL injection
SORT_WHITELIST = {
    "subsidy": {"created_at", "recipient", "amount"},
    "project": {"created_at", "name", "owner"},
    "disbursement": {"date", "amount", "reference"},
    "audit": {"created_at", "entity", "action"}
}


def _parse_decimal_maybe(value: str) -> Optional[Decimal]:
    """
    Attempt to parse string to Decimal defensively.
    
    Args:
        value: String to parse
    
    Returns:
        Decimal if parsing succeeds, None otherwise
    """
    try:
        return Decimal(value)
    except (InvalidOperation, ValueError, TypeError):
        return None


def _safe_sort_params(entity: str, sort_by: Optional[str], order: str) -> Tuple[Optional[Any], str]:
    """
    Validate and map sort parameters to actual SQLAlchemy column objects.
    
    Protects against SQL injection by mapping string field names to model attributes.
    
    Args:
        entity: Entity type (subsidy, project, disbursement, audit)
        sort_by: Field name to sort by (must be in whitelist)
        order: Sort direction (asc or desc)
    
    Returns:
        Tuple of (column_object, normalized_order) or (None, "desc") if invalid
    """
    # Normalize order
    normalized_order = order.lower() if order and order.lower() in ["asc", "desc"] else "desc"
    
    # Check entity exists in whitelist
    if entity not in SORT_WHITELIST:
        return (None, normalized_order)
    
    # Check sort_by is in whitelist for this entity
    if not sort_by or sort_by not in SORT_WHITELIST[entity]:
        return (None, normalized_order)
    
    # Map entity and field to actual SQLAlchemy column
    model_map = {
        "subsidy": SubsidyModel,
        "project": ProjectModel,
        "disbursement": DisbursementModel,
        "audit": AuditRecordModel
    }
    
    model = model_map.get(entity)
    if not model:
        return (None, normalized_order)
    
    # Get the column attribute safely
    column = getattr(model, sort_by, None)
    if column is None:
        return (None, normalized_order)
    
    return (column, normalized_order)


def _row_to_dict(obj: Any) -> Dict[str, Any]:
    """
    Convert ORM object to dictionary representation.
    
    Tries obj.to_dict() if available; otherwise constructs minimal dict
    with id and primary display field.
    
    Args:
        obj: SQLAlchemy ORM object
    
    Returns:
        Dict representation of the object
    """
    # Try to_dict method if exists
    to_dict_method = getattr(obj, "to_dict", None)
    if callable(to_dict_method):
        return to_dict_method()
    
    # Fallback: construct minimal dict based on object type
    result = {"id": getattr(obj, "id", None)}
    
    # Add primary display field based on what's available
    for field in ["title", "name", "reference", "action", "recipient", "owner"]:
        value = getattr(obj, field, None)
        if value is not None:
            result[field] = value
            break
    
    # Add created_at or date if available
    for date_field in ["created_at", "date"]:
        date_value = getattr(obj, date_field, None)
        if date_value is not None:
            result[date_field] = date_value.isoformat() if hasattr(date_value, "isoformat") else str(date_value)
            break
    
    return result


def search_entities(
    db: Session,
    q: Optional[str] = None,
    entity: Optional[str] = None,
    limit: int = DEFAULT_LIMIT,
    offset: int = 0,
    sort_by: Optional[str] = None,
    order: str = "desc"
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Multi-entity search across subsidies, projects, disbursements, and audits.
    
    Applies safe ILIKE queries on whitelisted text fields and returns results
    grouped by entity type.
    
    Args:
        db: SQLAlchemy session
        q: Search query string (optional)
        entity: Restrict to specific entity type (optional)
        limit: Maximum results per entity (1 to MAX_LIMIT)
        offset: Pagination offset (>= 0)
        sort_by: Field to sort by (must be whitelisted)
        order: Sort direction (asc or desc)
    
    Returns:
        Dict with keys: subsidies, projects, disbursements, audits
        Each key maps to list of result dicts
    
    Raises:
        ValueError: If limit or offset are invalid
        RuntimeError: If database operation fails
    """
    if limit < 1 or limit > MAX_LIMIT:
        raise ValueError(f"limit must be between 1 and {MAX_LIMIT}, got {limit}")
    if offset < 0:
        raise ValueError(f"offset must be >= 0, got {offset}")
    
    # Normalize entity filter
    entity_filter = entity.lower() if entity else None
    
    # Initialize result structure
    results = {
        "subsidies": [],
        "projects": [],
        "disbursements": [],
        "audits": []
    }
    
    # Build search term for ILIKE queries
    search_term = f"%{q}%" if q else None
    
    try:
        # Search Subsidies
        if entity_filter is None or entity_filter == "subsidy":
            subsidy_query = db.query(SubsidyModel)
            
            if search_term:
                subsidy_query = subsidy_query.filter(
                    or_(
                        SubsidyModel.title.ilike(search_term),
                        SubsidyModel.recipient.ilike(search_term),
                        SubsidyModel.description.ilike(search_term)
                    )
                )
            
            # Apply safe sorting
            sort_col, sort_order = _safe_sort_params("subsidy", sort_by, order)
            if sort_col is not None:
                subsidy_query = subsidy_query.order_by(sort_col.desc() if sort_order == "desc" else sort_col.asc())
            else:
                subsidy_query = subsidy_query.order_by(SubsidyModel.created_at.desc())
            
            subsidy_query = subsidy_query.limit(limit).offset(offset)
            results["subsidies"] = [_row_to_dict(row) for row in subsidy_query.all()]
        
        # Search Projects
        if entity_filter is None or entity_filter == "project":
            project_query = db.query(ProjectModel)
            
            if search_term:
                project_query = project_query.filter(
                    or_(
                        ProjectModel.name.ilike(search_term),
                        ProjectModel.owner.ilike(search_term),
                        ProjectModel.description.ilike(search_term)
                    )
                )
            
            # Apply safe sorting
            sort_col, sort_order = _safe_sort_params("project", sort_by, order)
            if sort_col is not None:
                project_query = project_query.order_by(sort_col.desc() if sort_order == "desc" else sort_col.asc())
            else:
                project_query = project_query.order_by(ProjectModel.created_at.desc())
            
            project_query = project_query.limit(limit).offset(offset)
            results["projects"] = [_row_to_dict(row) for row in project_query.all()]
        
        # Search Disbursements
        if entity_filter is None or entity_filter == "disbursement":
            disbursement_query = db.query(DisbursementModel)
            
            if search_term:
                # Try parsing as decimal for amount search
                decimal_value = _parse_decimal_maybe(q) if q else None
                
                filters = [DisbursementModel.reference.ilike(search_term)]
                if decimal_value is not None:
                    filters.append(DisbursementModel.amount == decimal_value)
                
                disbursement_query = disbursement_query.filter(or_(*filters))
            
            # Apply safe sorting
            sort_col, sort_order = _safe_sort_params("disbursement", sort_by, order)
            if sort_col is not None:
                disbursement_query = disbursement_query.order_by(sort_col.desc() if sort_order == "desc" else sort_col.asc())
            else:
                disbursement_query = disbursement_query.order_by(DisbursementModel.date.desc())
            
            disbursement_query = disbursement_query.limit(limit).offset(offset)
            results["disbursements"] = [_row_to_dict(row) for row in disbursement_query.all()]
        
        # Search Audit Records
        if entity_filter is None or entity_filter == "audit":
            audit_query = db.query(AuditRecordModel)
            
            if search_term:
                audit_query = audit_query.filter(
                    or_(
                        AuditRecordModel.entity.ilike(search_term),
                        AuditRecordModel.action.ilike(search_term),
                        AuditRecordModel.details.ilike(search_term)
                    )
                )
            
            # Apply safe sorting
            sort_col, sort_order = _safe_sort_params("audit", sort_by, order)
            if sort_col is not None:
                audit_query = audit_query.order_by(sort_col.desc() if sort_order == "desc" else sort_col.asc())
            else:
                audit_query = audit_query.order_by(AuditRecordModel.created_at.desc())
            
            audit_query = audit_query.limit(limit).offset(offset)
            results["audits"] = [_row_to_dict(row) for row in audit_query.all()]
        
        return results
        
    except SQLAlchemyError as e:
        raise RuntimeError("DB error during search")


def suggest_field(db: Session, field: str, q: str, limit: int = 10) -> List[str]:
    """
    Provide prefix autocomplete suggestions for whitelisted fields.
    
    Args:
        db: SQLAlchemy session
        field: Field name to suggest from (e.g., 'subsidy_title', 'project_name')
        q: Query prefix
        limit: Maximum suggestions to return (1 to 50)
    
    Returns:
        List of unique suggestion strings
    
    Raises:
        ValueError: If field is not whitelisted or limit is invalid
        RuntimeError: If database operation fails
    """
    if limit < 1 or limit > 50:
        raise ValueError(f"limit must be between 1 and 50, got {limit}")
    
    # Whitelist mapping: field name -> (model, column_name)
    field_whitelist = {
        "subsidy_title": (SubsidyModel, "title"),
        "recipient": (SubsidyModel, "recipient"),
        "project_name": (ProjectModel, "name"),
        "project_owner": (ProjectModel, "owner"),
        "reference": (DisbursementModel, "reference")
    }
    
    if field not in field_whitelist:
        raise ValueError(f"Field '{field}' is not whitelisted for suggestions")
    
    model, column_name = field_whitelist[field]
    column = getattr(model, column_name, None)
    
    if column is None:
        raise ValueError(f"Column '{column_name}' not found on model")
    
    try:
        # Build prefix query with ILIKE
        search_pattern = f"{q}%"
        
        query = db.query(column).distinct().filter(
            column.ilike(search_pattern)
        ).limit(limit)
        
        # Extract and return string values
        results = [row[0] for row in query.all() if row[0]]
        return results
        
    except SQLAlchemyError as e:
        raise RuntimeError("DB error during suggest")


__all__ = ["search_entities", "suggest_field"]

# Test hint: seed an in-memory sqlite DB with sample rows and assert search_entities(db, q="term") returns expected dict; mock DB errors to test exception paths.