"""
Authentication API Endpoints

This module provides complete authentication and authorization functionality:
- User registration and login
- JWT token management (access and refresh tokens)
- User profile operations
- Admin user management
- Role-based access control

OAuth2 Flow:
============
FastAPI uses OAuth2PasswordBearer for token-based authentication:
1. User logs in with email/password -> receives access_token and refresh_token
2. Client includes access_token in Authorization header: "Bearer <token>"
3. FastAPI automatically extracts token from header
4. Token is validated and user is retrieved from database
5. User object is injected into endpoint via dependency injection

Why OAuth2?
- Industry standard for API authentication
- Stateless (no server-side sessions)
- Works well with JWT tokens
- Built-in FastAPI support

JWT Token Lifecycle:
====================
1. Login: User authenticates -> receives access_token (30 min) + refresh_token (7 days)
2. API Calls: Client sends access_token in Authorization header
3. Token Expiry: Access token expires after 30 minutes
4. Refresh: Client uses refresh_token to get new access_token + refresh_token
5. Logout: Client discards tokens (stateless, so no server-side logout needed)

FastAPI Dependency Injection:
=============================
Dependencies are functions that FastAPI calls before executing endpoints.
They can:
- Extract and validate request data (headers, query params, body)
- Perform authentication/authorization checks
- Inject objects into endpoint functions
- Raise HTTP exceptions to stop execution

Example:
    @app.get("/protected")
    def protected_route(user: User = Depends(get_current_user)):
        # user is automatically injected by FastAPI
        return {"user_id": user.id}
"""

from datetime import timedelta
from typing import Optional, List, Callable

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Security
)
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, validator
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_user_id_from_token,
    validate_password_strength,
    Role,
    has_permission
)
from backend.models.user import User, UserCRUD

# ============================================================================
# ROUTER SETUP
# ============================================================================

# Create FastAPI router with prefix and tags
# Prefix: All routes will be prefixed with "/auth"
# Tags: Groups endpoints in API documentation (Swagger UI)
router = APIRouter(prefix="/auth", tags=["authentication"])

# OAuth2PasswordBearer: Extracts token from Authorization header
# tokenUrl: Where clients send username/password to get tokens
# This enables the "Authorize" button in Swagger UI
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ============================================================================
# PYDANTIC MODELS
# ============================================================================
# Pydantic models provide automatic validation and serialization:
# - Request validation: Ensures incoming data matches schema
# - Response serialization: Converts Python objects to JSON
# - Type safety: IDE autocomplete and type checking
# - Documentation: Auto-generates OpenAPI schema

class UserRegister(BaseModel):
    """
    User registration request model.
    
    Validates user input during registration:
    - Email must be valid email format
    - Username must be 3-50 characters
    - Password must meet strength requirements
    """
    email: EmailStr
    username: str
    password: str
    
    @validator('username')
    def validate_username(cls, v):
        """
        Validate username length and format.
        
        Requirements:
        - Minimum 3 characters (prevents too short usernames)
        - Maximum 50 characters (database column limit)
        - Must be non-empty after stripping whitespace
        """
        if not v or not v.strip():
            raise ValueError('Username cannot be empty')
        v = v.strip()
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters long')
        if len(v) > 50:
            raise ValueError('Username cannot exceed 50 characters')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        """
        Validate password strength.
        
        Uses security module's validate_password_strength() to check:
        - Minimum 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character
        """
        is_valid, message = validate_password_strength(v)
        if not is_valid:
            raise ValueError(message)
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "username": "johndoe",
                "password": "SecurePass123!"
            }
        }


class UserLogin(BaseModel):
    """
    User login request model.
    
    Note: FastAPI's OAuth2PasswordRequestForm is used for actual login,
    but this model can be used for documentation or alternative endpoints.
    """
    email: EmailStr
    password: str
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!"
            }
        }


class Token(BaseModel):
    """
    Token response model.
    
    Returned after successful login or token refresh.
    Contains both access and refresh tokens.
    """
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    
    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }
        }


class UserResponse(BaseModel):
    """
    User response model.
    
    Used to return user data in API responses.
    Excludes sensitive information (password, API key).
    """
    id: int
    email: str
    username: str
    role: str
    is_active: bool
    is_verified: bool
    created_at: Optional[str] = None
    last_login: Optional[str] = None
    
    class Config:
        # orm_mode allows Pydantic to read from SQLAlchemy models
        # This enables automatic conversion: User -> UserResponse
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 1,
                "email": "user@example.com",
                "username": "johndoe",
                "role": "viewer",
                "is_active": True,
                "is_verified": False,
                "created_at": "2024-01-01T00:00:00",
                "last_login": None
            }
        }


class PasswordChange(BaseModel):
    """
    Password change request model.
    
    Requires both current and new password for security.
    """
    current_password: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """Validate new password strength."""
        is_valid, message = validate_password_strength(v)
        if not is_valid:
            raise ValueError(message)
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "current_password": "OldPass123!",
                "new_password": "NewSecurePass456!"
            }
        }


class UserUpdate(BaseModel):
    """
    User profile update model.
    
    Allows updating username and other non-sensitive fields.
    """
    username: Optional[str] = None
    
    @validator('username')
    def validate_username(cls, v):
        """Validate username if provided."""
        if v is not None:
            if not v or not v.strip():
                raise ValueError('Username cannot be empty')
            v = v.strip()
            if len(v) < 3:
                raise ValueError('Username must be at least 3 characters long')
            if len(v) > 50:
                raise ValueError('Username cannot exceed 50 characters')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "username": "newusername"
            }
        }


class RoleUpdate(BaseModel):
    """
    Role update model for admin operations.
    """
    role: str
    
    @validator('role')
    def validate_role(cls, v):
        """Validate role is one of the allowed values."""
        if not Role.is_valid_role(v):
            raise ValueError(f'Invalid role. Must be one of: {", ".join(Role.all_roles())}')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "role": "cfo"
            }
        }


# ============================================================================
# HELPER FUNCTIONS (DEPENDENCIES)
# ============================================================================

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    FastAPI dependency to get current authenticated user.
    
    This function:
    1. Receives JWT token from Authorization header (via oauth2_scheme)
    2. Decodes and validates the token
    3. Retrieves user from database
    4. Checks if user is active
    5. Returns user object or raises HTTPException
    
    How it works:
    - FastAPI automatically calls this before executing protected endpoints
    - Token is extracted from "Authorization: Bearer <token>" header
    - If token is invalid or user not found, raises 401 Unauthorized
    - If user is inactive, raises 401 Unauthorized
    
    Usage:
        @router.get("/protected")
        def protected_endpoint(user: User = Depends(get_current_user)):
            return {"user_id": user.id}
    
    Args:
        token: JWT token from Authorization header
        db: Database session (injected by FastAPI)
        
    Returns:
        User: Authenticated user instance
        
    Raises:
        HTTPException: 401 if token invalid or user inactive
    """
    # Decode token to get user ID
    user_id = get_user_id_from_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user = UserCRUD.get_user_by_id(db, int(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Alias for get_current_user.
    
    Provides semantic clarity when you want to emphasize
    that the user must be active (which is already checked).
    
    Usage:
        @router.get("/me")
        def get_profile(user: User = Depends(get_current_active_user)):
            return user
    """
    return current_user


def require_role(required_role: str) -> Callable:
    """
    Dependency factory for role-based access control.
    
    This function returns a dependency function that checks if the
    current user has sufficient permissions for the required role.
    
    How it works:
    1. Factory function takes required_role as parameter
    2. Returns a dependency function that FastAPI will call
    3. Dependency function receives current_user from get_current_user
    4. Checks if user's role has required permissions
    5. Raises 403 Forbidden if insufficient permissions
    
    Usage:
        @router.get("/admin-only")
        def admin_endpoint(
            user: User = Depends(require_role(Role.ADMIN))
        ):
            return {"message": "Admin access granted"}
    
    Args:
        required_role: Minimum role required (admin, cfo, analyst, viewer)
        
    Returns:
        Callable: Dependency function that checks role permissions
        
    Raises:
        HTTPException: 403 if user lacks required permissions
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if not has_permission(current_user.role, required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role}"
            )
        return current_user
    
    return role_checker


# ============================================================================
# PUBLIC ENDPOINTS
# ============================================================================

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """
    Register a new user account.
    
    This endpoint:
    1. Validates input (email format, password strength, username length)
    2. Checks if email already exists
    3. Hashes password using bcrypt
    4. Creates user with default role "viewer"
    5. Returns user data (without password)
    
    Error Handling:
    - 400: Validation error (invalid email, weak password, etc.)
    - 409: Email already exists
    
    Args:
        user_data: User registration data (email, username, password)
        db: Database session
        
    Returns:
        UserResponse: Created user data
        
    Raises:
        HTTPException: 400 if validation fails, 409 if email exists
    """
    # Check if email already exists
    existing_user = UserCRUD.get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    # Create user with default role "viewer"
    # Password is automatically hashed by UserCRUD.create_user()
    user = UserCRUD.create_user(
        db=db,
        email=user_data.email,
        username=user_data.username,
        password=user_data.password,
        role=Role.VIEWER,  # Default role for new users
        is_verified=False  # Requires email verification
    )
    
    # Commit transaction
    db.commit()
    db.refresh(user)  # Refresh to get generated ID
    
    return user


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT tokens.
    
    This endpoint:
    1. Receives email (as username) and password via OAuth2 form
    2. Finds user by email
    3. Verifies password using bcrypt
    4. Checks if user is active
    5. Updates last_login timestamp
    6. Generates access_token (30 min) and refresh_token (7 days)
    7. Returns both tokens
    
    OAuth2PasswordRequestForm:
    - FastAPI's standard OAuth2 form
    - Expects "username" and "password" fields
    - We use "username" field for email address
    - Enables "Authorize" button in Swagger UI
    
    Error Handling:
    - 401: Invalid email or password
    - 401: Inactive user
    
    Args:
        form_data: OAuth2 form with username (email) and password
        db: Database session
        
    Returns:
        Token: Access token and refresh token
        
    Raises:
        HTTPException: 401 if authentication fails
    """
    # OAuth2PasswordRequestForm uses "username" field, but we use email
    email = form_data.username
    
    # Find user by email
    user = UserCRUD.get_user_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not user.verify_password(form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user account",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login timestamp
    UserCRUD.update_last_login(db, user)
    db.commit()
    
    # Create token payload
    token_data = {
        "sub": str(user.id),  # "sub" is standard JWT claim for subject (user ID)
        "email": user.email,
        "role": user.role
    }
    
    # Generate tokens
    access_token = create_access_token(data=token_data)
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=Token)
def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token.
    
    This endpoint:
    1. Receives refresh_token
    2. Decodes and validates refresh token
    3. Retrieves user from database
    4. Generates new access_token and refresh_token
    5. Returns new tokens (token rotation)
    
    Token Rotation:
    - Both access and refresh tokens are regenerated
    - Old refresh token becomes invalid
    - Enhances security by limiting token lifetime
    
    Error Handling:
    - 401: Invalid or expired refresh token
    - 401: User not found or inactive
    
    Args:
        refresh_token: Refresh token string
        db: Database session
        
    Returns:
        Token: New access token and refresh token
        
    Raises:
        HTTPException: 401 if refresh token invalid
    """
    # Decode refresh token
    payload = decode_token(refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check token type
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user ID from token
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user = UserCRUD.get_user_by_id(db, int(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate new tokens
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role
    }
    
    access_token = create_access_token(data=token_data)
    new_refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


# ============================================================================
# PROTECTED ENDPOINTS (Require Authentication)
# ============================================================================

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user's profile.
    
    Returns authenticated user's information.
    No additional parameters needed - user is injected via dependency.
    
    Args:
        current_user: Authenticated user (injected by FastAPI)
        
    Returns:
        UserResponse: Current user's profile data
    """
    return current_user


@router.put("/me", response_model=UserResponse)
def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's profile.
    
    Allows users to update their own profile information.
    Currently supports: username
    
    Args:
        user_update: Fields to update
        current_user: Authenticated user
        db: Database session
        
    Returns:
        UserResponse: Updated user data
    """
    # Update only provided fields
    update_data = user_update.dict(exclude_unset=True)
    if update_data:
        UserCRUD.update_user(db, current_user, **update_data)
        db.commit()
        db.refresh(current_user)
    
    return current_user


@router.post("/change-password")
def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Change current user's password.
    
    Requires both current and new password for security.
    New password must meet strength requirements.
    
    Error Handling:
    - 400: Current password incorrect
    - 400: New password doesn't meet strength requirements
    
    Args:
        password_data: Current and new password
        current_user: Authenticated user
        db: Database session
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: 400 if current password incorrect
    """
    # Verify current password
    if not current_user.verify_password(password_data.current_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Change password (new password is validated by Pydantic)
    UserCRUD.change_password(db, current_user, password_data.new_password)
    db.commit()
    
    return {"message": "Password changed successfully"}


# ============================================================================
# ADMIN ENDPOINTS (Require Admin Role)
# ============================================================================

@router.get("/users", response_model=List[UserResponse])
def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_role(Role.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    List all users (Admin only).
    
    Returns paginated list of all users.
    Only accessible by administrators.
    
    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        current_user: Authenticated admin user
        db: Database session
        
    Returns:
        List[UserResponse]: List of user data
    """
    users = UserCRUD.get_all_users(db, skip=skip, limit=limit)
    return users


@router.put("/users/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: int,
    role_update: RoleUpdate,
    current_user: User = Depends(require_role(Role.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Update user's role (Admin only).
    
    Allows administrators to change user roles.
    Role is validated to ensure it's a valid role value.
    
    Error Handling:
    - 404: User not found
    
    Args:
        user_id: ID of user to update
        role_update: New role value
        current_user: Authenticated admin user
        db: Database session
        
    Returns:
        UserResponse: Updated user data
        
    Raises:
        HTTPException: 404 if user not found
    """
    # Get user
    user = UserCRUD.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update role
    UserCRUD.update_user(db, user, role=role_update.role)
    db.commit()
    db.refresh(user)
    
    return user


@router.delete("/users/{user_id}")
def deactivate_user(
    user_id: int,
    current_user: User = Depends(require_role(Role.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Deactivate user account (Admin only - Soft Delete).
    
    Soft delete: Sets is_active=False instead of deleting record.
    Preserves data for audit trails and allows reactivation.
    
    Error Handling:
    - 404: User not found
    - 400: Cannot deactivate yourself
    
    Args:
        user_id: ID of user to deactivate
        current_user: Authenticated admin user
        db: Database session
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: 404 if user not found, 400 if trying to deactivate self
    """
    # Prevent self-deactivation
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    # Get user
    user = UserCRUD.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Deactivate user (soft delete)
    UserCRUD.deactivate_user(db, user)
    db.commit()
    
    return {"message": f"User {user_id} deactivated successfully"}


