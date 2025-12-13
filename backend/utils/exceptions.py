"""
backend/utils/exceptions.py

Application-specific exceptions and helpers to convert them to FastAPI HTTP responses.
"""

from __future__ import annotations
from typing import Optional, Any, Dict
from dataclasses import dataclass, field
from fastapi import HTTPException, Request
from starlette import status
from fastapi import FastAPI


@dataclass
class AppError(Exception):
    """
    Base application error with HTTP status code and optional payload.
    
    Use this as the base for all application-level exceptions.
    Can be converted to HTTPException via to_http_exception() or handled
    automatically by registering exception handlers with register_exception_handlers().
    """
    message: str
    status_code: int = status.HTTP_400_BAD_REQUEST
    payload: Optional[Dict[str, Any]] = None
    
    def __str__(self) -> str:
        """Return the error message."""
        return self.message
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert error to a serializable dictionary.
        
        Returns:
            Dict with 'error' key and optional 'details' key if payload exists
        """
        result = {"error": self.message}
        if self.payload is not None:
            result["details"] = self.payload
        return result


@dataclass
class NotFoundError(AppError):
    """
    Requested resource was not found.
    
    Use when an entity lookup by ID or other identifier fails.
    """
    message: str = "Resource not found"
    status_code: int = status.HTTP_404_NOT_FOUND
    payload: Optional[Dict[str, Any]] = None


@dataclass
class UnauthorizedError(AppError):
    """
    Request lacks valid authentication credentials.
    
    Use when user is not authenticated or token is invalid/missing.
    """
    message: str = "Authentication required"
    status_code: int = status.HTTP_401_UNAUTHORIZED
    payload: Optional[Dict[str, Any]] = None


@dataclass
class ForbiddenError(AppError):
    """
    Authenticated user lacks permission to access resource.
    
    Use when user is authenticated but not authorized for the requested action.
    """
    message: str = "Access forbidden"
    status_code: int = status.HTTP_403_FORBIDDEN
    payload: Optional[Dict[str, Any]] = None


@dataclass
class ConflictError(AppError):
    """
    Request conflicts with current state (e.g., duplicate resource).
    
    Use for constraint violations, duplicate keys, or state conflicts.
    """
    message: str = "Conflict with existing resource"
    status_code: int = status.HTTP_409_CONFLICT
    payload: Optional[Dict[str, Any]] = None


@dataclass
class InternalServerError(AppError):
    """
    Internal server error occurred.
    
    Use for unexpected errors that should not expose implementation details to clients.
    """
    message: str = "Internal server error"
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    payload: Optional[Dict[str, Any]] = None


def to_http_exception(err: AppError) -> HTTPException:
    """
    Convert an AppError into a FastAPI HTTPException with JSON-detail body.
    
    Args:
        err: Application error to convert
    
    Returns:
        HTTPException with appropriate status code and detail dict
    
    Example:
        raise to_http_exception(NotFoundError("User not found"))
    """
    return HTTPException(
        status_code=err.status_code,
        detail=err.to_dict()
    )


async def _app_error_handler(request: Request, exc: AppError) -> HTTPException:
    """
    FastAPI exception handler for AppError and subclasses.
    
    Converts AppError to HTTPException for proper JSON response.
    
    Args:
        request: FastAPI request object (required by handler signature)
        exc: The AppError that was raised
    
    Returns:
        HTTPException with error details
    """
    return to_http_exception(exc)


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register exception handlers for application errors on a FastAPI app.
    
    This allows you to raise AppError subclasses directly in route handlers
    and have them automatically converted to proper HTTP responses.
    
    Usage in main.py:
        from backend.utils.exceptions import register_exception_handlers
        
        app = FastAPI()
        register_exception_handlers(app)
    
    Args:
        app: FastAPI application instance
    """
    # Register handler for AppError and all subclasses
    app.add_exception_handler(AppError, _app_error_handler)


__all__ = [
    "AppError",
    "NotFoundError",
    "UnauthorizedError",
    "ForbiddenError",
    "ConflictError",
    "InternalServerError",
    "to_http_exception",
    "register_exception_handlers"
]