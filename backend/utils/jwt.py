"""
backend/utils/jwt.py

JWT helpers: create and decode HS256 JSON Web Tokens using secret from settings. Minimal, testable, and safe for FastAPI integrations.
"""

from __future__ import annotations
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from backend.config import settings


# Default configuration from settings
# SECRET_KEY must be set in settings for production use
# JWT_ALGORITHM defaults to HS256 (symmetric signing)
# ACCESS_TOKEN_EXPIRE_MINUTES defaults to 60 minutes
DEFAULT_ALGORITHM = getattr(settings, "JWT_ALGORITHM", "HS256")
DEFAULT_EXPIRE_MINUTES = getattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", 60)


def _get_jwt_lib() -> Any:
    """
    Import PyJWT library dynamically and return the module.
    
    Raises:
        RuntimeError: If PyJWT is not installed
    
    Returns:
        jwt module from PyJWT library
    """
    try:
        import jwt
        return jwt
    except ImportError:
        raise RuntimeError(
            "PyJWT is required for jwt utilities. "
            "Install 'PyJWT' or configure an alternative."
        )


def create_token(subject: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a signed JWT access token.
    
    The token payload includes all keys from subject plus standard claims:
    - iat (issued at): timestamp when token was created
    - exp (expiration): timestamp when token expires
    
    These standard claims enable automatic expiration validation and audit trails.
    
    Security note: Uses HS256 (HMAC-SHA256) by default for symmetric signing.
    In production, consider using asymmetric algorithms (RS256) with proper
    key management services (KMS) for better key rotation and security.
    
    Args:
        subject: Dict containing claims to include in token (e.g., user_id, username)
        expires_delta: Optional custom expiration timedelta; if None, uses default from settings
    
    Returns:
        Encoded JWT token string
    
    Raises:
        ValueError: If subject is empty or not a dict
        RuntimeError: If PyJWT is not available
    """
    # Validate subject
    if not isinstance(subject, dict):
        raise ValueError("Subject must be a dictionary")
    if not subject:
        raise ValueError("Subject cannot be empty")
    
    # Get PyJWT library
    jwt_lib = _get_jwt_lib()
    
    # Calculate expiration
    if expires_delta is None:
        expires_delta = timedelta(minutes=DEFAULT_EXPIRE_MINUTES)
    
    now = datetime.utcnow()
    expire = now + expires_delta
    
    # Build payload with standard claims
    # iat (issued at): helps track token creation time for audit/debugging
    # exp (expiration): enables automatic expiration validation by PyJWT
    payload = {
        **subject,
        "iat": now,
        "exp": expire
    }
    
    # Sign and encode token
    # WARNING: Never log the token or SECRET_KEY
    encoded_token = jwt_lib.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=DEFAULT_ALGORITHM
    )
    
    return encoded_token


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and verify a JWT token.
    
    Automatically verifies signature and expiration.
    
    Args:
        token: JWT token string to decode
    
    Returns:
        Decoded payload as dictionary
    
    Raises:
        ValueError: If token is invalid, expired, or malformed
        RuntimeError: If PyJWT is not available
    """
    # Get PyJWT library
    jwt_lib = _get_jwt_lib()
    
    try:
        # Decode and verify token
        # PyJWT will automatically verify signature and expiration
        payload = jwt_lib.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[DEFAULT_ALGORITHM]
        )
        
        # Ensure payload is a dict
        if not isinstance(payload, dict):
            raise ValueError("Malformed token: payload is not a dictionary")
        
        return payload
        
    except jwt_lib.ExpiredSignatureError:
        raise ValueError("Token expired")
    except jwt_lib.InvalidTokenError:
        raise ValueError("Invalid token")
    except jwt_lib.DecodeError:
        raise ValueError("Malformed token")
    except Exception as e:
        # Catch any other JWT errors and convert to ValueError
        raise ValueError(f"Token validation failed: {str(e)}")


def create_access_token_for_user(
    user_id: int,
    username: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
    expires_minutes: Optional[int] = None
) -> str:
    """
    Convenience function to create an access token for a user.
    
    Builds subject dict with user_id and username, optionally merged with
    additional claims from extra dict.
    
    Args:
        user_id: User's unique identifier (required)
        username: User's username (optional)
        extra: Additional claims to include in token (optional)
        expires_minutes: Custom expiration in minutes; if None, uses default
    
    Returns:
        Encoded JWT token string
    
    Raises:
        ValueError: If user_id is invalid or subject construction fails
        RuntimeError: If PyJWT is not available
    """
    # Build subject dict
    subject = {"user_id": user_id}
    
    if username is not None:
        subject["username"] = username
    
    # Merge extra claims if provided
    if extra is not None:
        subject.update(extra)
    
    # Calculate expiration delta
    expires_delta = None
    if expires_minutes is not None:
        expires_delta = timedelta(minutes=expires_minutes)
    
    return create_token(subject, expires_delta=expires_delta)


def verify_token_and_get_subject(token: str) -> Dict[str, Any]:
    """
    Decode token and verify it contains required user claims.
    
    Convenience wrapper that ensures the token payload contains a user_id field.
    
    Args:
        token: JWT token string to verify
    
    Returns:
        Decoded and verified payload dict
    
    Raises:
        ValueError: If token is invalid or missing required user_id claim
        RuntimeError: If PyJWT is not available
    """
    payload = decode_token(token)
    
    # Verify user_id is present
    if "user_id" not in payload:
        raise ValueError("Token payload missing user_id")
    
    return payload


__all__ = [
    "create_token",
    "decode_token",
    "create_access_token_for_user",
    "verify_token_and_get_subject"
]

# Test hint: use a temporary secret in settings, call create_access_token_for_user(...), then decode_token(...) and assert returned payload contains user_id and username.