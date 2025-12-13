"""
backend/utils/response.py

Helpers for consistent API JSON responses: success wrappers, error envelopes, pagination helpers and converters.
"""

from __future__ import annotations
from typing import Any, Optional, Dict, Iterable, List, Tuple
from datetime import datetime
from fastapi.responses import JSONResponse
from pydantic import BaseModel


def _now_iso() -> str:
    """
    Return current UTC timestamp as ISO8601 string with Z suffix.
    
    Returns:
        ISO8601 timestamp string (e.g., "2025-01-15T10:30:45.123456Z")
    """
    return datetime.utcnow().isoformat() + "Z"


def _serialize(obj: Any) -> Any:
    """
    Convert objects into JSON-serializable shapes.
    
    Handles Pydantic models, objects with to_dict() methods, and iterables.
    Falls back to string conversion on serialization errors.
    
    Args:
        obj: Object to serialize
    
    Returns:
        JSON-serializable representation of obj
    """
    # Handle None
    if obj is None:
        return None
    
    # Handle Pydantic BaseModel
    if isinstance(obj, BaseModel):
        try:
            return obj.dict(by_alias=False, exclude_none=True)
        except Exception:
            return str(obj)
    
    # Handle objects with to_dict method
    if hasattr(obj, "to_dict") and callable(getattr(obj, "to_dict")):
        try:
            return obj.to_dict()
        except Exception:
            return str(obj)
    
    # Handle iterables (lists, tuples) - recursively serialize items
    if isinstance(obj, (list, tuple)):
        try:
            return [_serialize(item) for item in obj]
        except Exception:
            return str(obj)
    
    # Handle dicts - recursively serialize values
    if isinstance(obj, dict):
        try:
            return {key: _serialize(value) for key, value in obj.items()}
        except Exception:
            return str(obj)
    
    # Return as-is for primitives and other types
    return obj


def success_response(
    data: Any = None,
    status_code: int = 200,
    meta: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """
    Build a standardized success response envelope.
    
    Returns JSON response with consistent structure:
    {
        "status": "ok",
        "timestamp": "<ISO8601>",
        "data": <serialized data>,
        "meta": <optional metadata>
    }
    
    Args:
        data: Response payload (will be serialized)
        status_code: HTTP status code (default 200)
        meta: Optional metadata dict
    
    Returns:
        JSONResponse with success envelope
    """
    envelope = {
        "status": "ok",
        "timestamp": _now_iso(),
        "data": _serialize(data)
    }
    
    # Include meta if provided
    if meta is not None:
        envelope["meta"] = _serialize(meta)
    
    return JSONResponse(content=envelope, status_code=status_code)


def error_response(
    message: str,
    *,
    status_code: int = 400,
    code: Optional[str] = None,
    details: Optional[Any] = None
) -> JSONResponse:
    """
    Build a standardized error response envelope.
    
    Returns JSON response with consistent structure:
    {
        "status": "error",
        "timestamp": "<ISO8601>",
        "error": {
            "message": "<human message>",
            "code": "<optional machine code>",
            "details": <optional serialized details>
        }
    }
    
    Args:
        message: Human-readable error message
        status_code: HTTP status code (default 400)
        code: Optional machine-readable error code
        details: Optional error details (will be serialized)
    
    Returns:
        JSONResponse with error envelope
    """
    error_obj = {"message": message}
    
    if code is not None:
        error_obj["code"] = code
    
    if details is not None:
        error_obj["details"] = _serialize(details)
    
    envelope = {
        "status": "error",
        "timestamp": _now_iso(),
        "error": error_obj
    }
    
    return JSONResponse(content=envelope, status_code=status_code)


def paginated_response(
    items: Iterable[Any],
    total: int,
    limit: int,
    offset: int,
    *,
    status_code: int = 200,
    meta: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """
    Build a standardized paginated response envelope.
    
    Returns JSON response with pagination metadata:
    {
        "status": "ok",
        "timestamp": "<ISO8601>",
        "data": [<serialized items>],
        "meta": {
            "limit": <limit>,
            "offset": <offset>,
            "total": <total count>,
            "returned": <actual items returned>,
            ... any additional meta keys
        }
    }
    
    Args:
        items: Iterable of items to serialize
        total: Total number of matching items
        limit: Page size limit
        offset: Pagination offset
        status_code: HTTP status code (default 200)
        meta: Optional additional metadata to merge
    
    Returns:
        JSONResponse with paginated envelope
    """
    # Convert to list and serialize
    items_list = list(items)
    serialized_items = _serialize(items_list)
    
    # Build pagination metadata
    pagination_meta = {
        "limit": limit,
        "offset": offset,
        "total": total,
        "returned": len(items_list)
    }
    
    # Merge with user-supplied meta if provided
    if meta is not None:
        pagination_meta.update(_serialize(meta))
    
    envelope = {
        "status": "ok",
        "timestamp": _now_iso(),
        "data": serialized_items,
        "meta": pagination_meta
    }
    
    return JSONResponse(content=envelope, status_code=status_code)


def make_api_response(
    payload: Any = None,
    *,
    success: bool = True,
    status_code: int = 200,
    message: Optional[str] = None,
    code: Optional[str] = None,
    details: Optional[Any] = None,
    meta: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """
    High-level wrapper to build either success or error response.
    
    Routes to success_response or error_response based on success flag.
    Useful for unified response building in route handlers.
    
    Args:
        payload: Data payload for success responses
        success: If True, build success response; if False, build error response
        status_code: HTTP status code
        message: Error message (used only if success=False)
        code: Error code (used only if success=False)
        details: Error details (used only if success=False)
        meta: Metadata (used only if success=True)
    
    Returns:
        JSONResponse with appropriate envelope
    """
    if success:
        return success_response(
            data=payload,
            status_code=status_code,
            meta=meta
        )
    else:
        return error_response(
            message=message or "error",
            status_code=status_code,
            code=code,
            details=details
        )


def http_exception_payload(exc: Exception) -> Dict[str, Any]:
    """
    Extract safe payload from exception for logging or error envelopes.
    
    Creates minimal exception info without stack traces or sensitive data.
    Useful for converting caught exceptions into error response details.
    
    Args:
        exc: Exception instance
    
    Returns:
        Dict with exception type and message
    
    Example:
        try:
            risky_operation()
        except Exception as e:
            return error_response(
                "Operation failed",
                details=http_exception_payload(e)
            )
    """
    return {
        "type": exc.__class__.__name__,
        "message": str(exc)
    }


__all__ = [
    "success_response",
    "error_response",
    "paginated_response",
    "make_api_response",
    "http_exception_payload"
]

# Test hint: assert success_response({"a":1}).body decodes to the expected envelope and status_code, and that Pydantic models serialize correctly via _serialize.