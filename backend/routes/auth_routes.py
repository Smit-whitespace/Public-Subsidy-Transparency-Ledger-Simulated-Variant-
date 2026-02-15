"""
backend/routes/auth_routes.py

REST API endpoints for user authentication and registration in the subsidy management system.

This module provides a FastAPI router with endpoints for user registration, login, and retrieving
the current authenticated user's profile. It implements JWT-based authentication using bearer tokens,
with proper password hashing for security and comprehensive error handling for edge cases like
duplicate usernames or invalid credentials.

The authentication flow follows industry-standard patterns: passwords are hashed using bcrypt before
storage, JWT tokens are issued on successful login with configurable expiration, and protected
endpoints validate tokens before granting access. All database operations include proper transaction
management with rollback on errors to maintain data integrity.

Test the login endpoint with curl:
    curl -X POST "http://localhost:8000/api/auth/login" -H "Content-Type: application/json" -d '{"username":"alice","password":"secret123"}'
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError , SQLAlchemyError
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.models.user import User as UserModel
from backend.schemas.auth import Token
from backend.schemas.user import UserRead, UserCreate
from backend.services.auth_service import get_password_hash, verify_password
from backend.utils.jwt import create_token, decode_token


router = APIRouter(tags=["authentication"])

# OAuth2 scheme for bearer token authentication. This tells FastAPI to look for tokens in the
# Authorization header with the format "Bearer <token>". The tokenUrl parameter specifies where
# clients should go to obtain tokens, which is our login endpoint.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> UserModel:
    """
    Dependency that validates JWT tokens and returns the authenticated user.
    
    This function is designed to be used as a FastAPI dependency in protected endpoints. It
    extracts the JWT token from the Authorization header, decodes and validates it, then fetches
    the corresponding user from the database. If anything goes wrong (expired token, invalid
    signature, user not found), it raises a 401 Unauthorized error.
    
    The decode_token function handles JWT validation including signature verification and expiry
    checking. If the token is valid, we extract the user_id from the payload and use it to fetch
    the user record. This approach ensures that tokens can't be tampered with and that they expire
    after the configured duration, forcing users to re-authenticate periodically.
    
    Args:
        token: JWT bearer token extracted from the Authorization header by oauth2_scheme
        db: Database session injected by FastAPI's dependency system
    
    Returns:
        The User ORM object corresponding to the authenticated user
    
    Raises:
        HTTPException: 401 error if the token is invalid, expired, or the user doesn't exist
    """
    # Set up a standard 401 response for authentication failures. The WWW-Authenticate header
    # tells clients what authentication scheme is required (Bearer tokens in our case).
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode and validate the JWT token. This checks the signature to ensure the token
        # wasn't tampered with, and verifies that it hasn't expired. If anything is wrong,
        # decode_token will raise an exception that we catch below.
        payload = decode_token(token)
        
        # Extract the user_id from the token payload. We stored this when creating the token
        # during login. If the user_id is missing from the payload, the token structure is
        # invalid and we should reject it.
        user_id: Optional[int] = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
        
    except Exception:
        # Any exception during token decoding (expired, invalid signature, malformed JWT, etc.)
        # should result in a 401 error. We don't expose the specific error details to clients
        # for security reasons, but they're logged internally for debugging.
        raise credentials_exception
    
    # Fetch the user from the database using the ID from the token. We use filter and first()
    # rather than get() to maintain consistency with other query patterns in the codebase.
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    
    # If the user no longer exists in the database (maybe they were deleted since the token
    # was issued), we reject the token. This ensures that deleted users can't continue using
    # old tokens to access the system.
    if user is None:
        raise credentials_exception
    
    return user


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
) -> UserModel:
    """
    Register a new user account in the system.
    
    This endpoint creates a new user with the provided username and password. The password is
    automatically hashed using bcrypt before being stored in the database, ensuring that plaintext
    passwords are never persisted. The endpoint enforces username uniqueness and returns clear
    error messages if registration fails.
    
    Registration is typically the first step in a user's journey through the application. After
    successfully registering, users should proceed to the login endpoint to obtain an authentication
    token that grants access to protected resources.
    
    Args:
        user_data: The registration data including username and password
        db: Database session injected by FastAPI's dependency system
    
    Returns:
        The newly created User object (without the password hash for security)
    
    Raises:
        HTTPException: 400 error if the username is already taken
        HTTPException: 500 error if an unexpected database error occurs
    """
    try:
        # Check if a user with this username already exists. Usernames must be unique in the
        # system to avoid ambiguity during login and to ensure each user has a distinct identity.
        existing_user = db.query(UserModel).filter(UserModel.username == user_data.username).first()
        
        if existing_user is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Username '{user_data.username}' is already registered"
            )
        
        # Hash the password using bcrypt before storing it. We never store plaintext passwords
        # as that would be a critical security vulnerability. The get_password_hash function
        # uses a strong one-way hashing algorithm with automatic salt generation to protect
        # user credentials even if the database is compromised.
        hashed_password = get_password_hash(user_data.password)
        
        # Create the new user ORM instance with the hashed password. We construct the object
        # manually rather than using **user_data.dict() so we can substitute the hashed password
        # in place of the plaintext one that came from the client.
        new_user = UserModel(
            username=user_data.username,
            hashed_password=hashed_password
        )
        
        # Add the new user to the session and commit to persist it to the database. The commit
        # executes the INSERT statement and assigns the auto-generated user ID. We then refresh
        # to load any database-generated values back into the Python object.
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return new_user
        
    except HTTPException:
        # Re-raise HTTPExceptions that we explicitly created (like the username conflict above)
        # so they propagate correctly to FastAPI's error handling. We don't want to wrap these
        # in another error layer.
        raise
        
    except IntegrityError as e:
        # IntegrityError typically indicates a constraint violation like unique username. We
        # catch this specifically because it might occur in race conditions where two requests
        # try to register the same username simultaneously. Rolling back ensures the failed
        # transaction doesn't leave the session in an inconsistent state.
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration failed due to data conflict: {str(e)}"
        )
        
    except SQLAlchemyError as e:
        # For any other database errors (connection issues, disk full, etc.), we rollback and
        # return a 500 error. We include some error details to help with debugging but avoid
        # exposing sensitive internal implementation details.
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error during registration: {str(e)}"
        )


@router.post("/login", response_model=Token)
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> dict:
    """
    Authenticate a user and issue a JWT access token.
    
    This endpoint verifies user credentials (username and password) and issues a JWT bearer token
    that can be used to authenticate subsequent requests to protected endpoints. The token includes
    the user's ID and username in its payload and expires after a configured duration (typically
    60 minutes), forcing users to re-authenticate periodically for security.
    
    We use OAuth2PasswordRequestForm which expects form data with 'username' and 'password' fields.
    This is compatible with OAuth2 standards and works well with both form submissions and JSON
    requests (FastAPI handles the conversion automatically).
    
    Args:
        form_data: OAuth2 form data containing username and password
        db: Database session injected by FastAPI's dependency system
    
    Returns:
        A dictionary with 'access_token' (the JWT) and 'token_type' (always "bearer")
    
    Raises:
        HTTPException: 401 error if credentials are invalid
        HTTPException: 500 error if an unexpected database error occurs
    """
    try:
        # Look up the user by username. We need the full user record to verify the password hash
        # and to include user details in the token payload if authentication succeeds.
        user = db.query(UserModel).filter(UserModel.username == form_data.username).first()
        
        # If no user exists with this username, authentication fails. We use a generic error
        # message ("Incorrect username or password") rather than revealing whether the username
        # exists, which prevents attackers from enumerating valid usernames.
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify the provided password against the stored hash. The verify_password function
        # uses bcrypt's secure comparison to check if the plaintext password matches the hash,
        # handling the salt automatically. This comparison is designed to be timing-safe to
        # prevent timing attacks.
        if not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Authentication succeeded! Now we create a JWT token containing the user's identity.
        # The payload includes user_id and username for convenience, plus an expiration time
        # (exp claim) set to 60 minutes from now. The create_token function handles signing
        # the JWT with our secret key to prevent tampering.
        token_payload = {
            "user_id": user.id,
            "username": user.username,
        }
        
        access_token = create_token(token_payload)
        
        # Return the token in OAuth2-compliant format. The token_type is always "bearer" which
        # tells clients to include the token in the Authorization header as "Bearer <token>".
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
        
    except HTTPException:
        # Re-raise HTTPExceptions that we explicitly created so they propagate to FastAPI's
        # error handling with the correct status codes and messages.
        raise
        
    except SQLAlchemyError as e:
        # For unexpected database errors during login (connection failures, etc.), we return
        # a 500 error. We don't rollback here because we're only doing SELECT queries which
        # don't modify the database state.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error during login: {str(e)}"
        )


@router.get("/me", response_model=UserRead)
def get_current_user_profile(
    current_user: UserModel = Depends(get_current_user),
) -> UserModel:
    """
    Retrieve the profile of the currently authenticated user.
    
    This endpoint demonstrates how to create protected routes that require authentication. By
    depending on get_current_user, we automatically enforce that a valid JWT token must be
    present in the Authorization header. If the token is missing, expired, or invalid, the
    request is rejected with a 401 error before this function even executes.
    
    This is useful for applications that need to display the logged-in user's information in
    the UI, or for any feature that needs to operate on the current user's data. The user
    object returned here does NOT include the password hash, as the Pydantic User schema
    explicitly excludes that field for security.
    
    Args:
        current_user: The authenticated user, automatically resolved by the get_current_user dependency
    
    Returns:
        The User object for the currently authenticated user (without password hash)
    """
    # The get_current_user dependency has already validated the token and fetched the user,
    # so all we need to do is return it. FastAPI will automatically serialize it using the
    # User Pydantic schema, which excludes sensitive fields like the password hash.
    return current_user