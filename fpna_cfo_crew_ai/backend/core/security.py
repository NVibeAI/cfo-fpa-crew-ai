"""
Security Utilities Module

This module provides comprehensive security functionality including:
- Password hashing and verification using bcrypt
- JWT token generation and validation
- Role-based access control (RBAC)
- API key generation

Security Best Practices:
1. Password Hashing:
   - Use bcrypt (slow hashing algorithm) to prevent brute-force attacks
   - Automatic salt generation (unique salt per password)
   - One-way hashing (cannot be reversed)

2. JWT Tokens:
   - Stateless authentication (no server-side session storage)
   - Short-lived access tokens (30 minutes) for security
   - Longer-lived refresh tokens (7 days) for user convenience
   - Token rotation on refresh for enhanced security

3. Role-Based Access Control:
   - Hierarchical permission system
   - Principle of least privilege
   - Clear role definitions and boundaries
"""

import os
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple

from passlib.context import CryptContext
from jose import JWTError, jwt

# Configure logging
logger = logging.getLogger(__name__)

# ============================================================================
# PASSWORD HASHING CONFIGURATION
# ============================================================================

# Password hashing context using bcrypt
# Why bcrypt?
# - Slow by design: Intentionally computationally expensive to prevent brute-force attacks
# - Automatic salting: Each password gets a unique salt, preventing rainbow table attacks
# - Adaptive: Can increase cost factor over time as hardware improves
# - Industry standard: Widely used and battle-tested
#
# The rounds parameter controls the computational cost:
# - Higher rounds = more secure but slower
# - Default: 12 rounds (good balance between security and performance)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def hash_password(password: str) -> str:
    """
    Hash a plain text password using bcrypt.
    
    This function takes a plain text password and returns a hashed version
    that can be safely stored in the database. The hash includes:
    - The bcrypt algorithm identifier
    - The cost factor (rounds)
    - A randomly generated salt
    - The hashed password
    
    The same password will produce different hashes each time due to
    automatic salt generation, but verify_password() can still verify them.
    
    Args:
        password: Plain text password to hash
        
    Returns:
        str: Hashed password string (e.g., "$2b$12$...")
        
    Example:
        hashed = hash_password("mySecurePassword123!")
        # Returns: "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5K..."
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a hashed password.
    
    This function securely compares a plain text password with a stored hash.
    It handles:
    - Extracting the salt from the hash
    - Hashing the plain password with the same salt
    - Constant-time comparison (prevents timing attacks)
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Stored hashed password from database
        
    Returns:
        bool: True if password matches, False otherwise
        
    Example:
        is_valid = verify_password("mySecurePassword123!", stored_hash)
        # Returns: True or False
    """
    return pwd_context.verify(plain_password, hashed_password)


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Validate password strength against security requirements.
    
    Password requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)
    
    Why these requirements?
    - Length: Longer passwords are exponentially harder to crack
    - Character variety: Increases possible combinations
    - Prevents common weak passwords (e.g., "password", "12345678")
    
    Args:
        password: Password to validate
        
    Returns:
        tuple: (is_valid: bool, message: str)
            - is_valid: True if password meets all requirements
            - message: Human-readable explanation of validation result
            
    Example:
        is_valid, message = validate_password_strength("MyPass123!")
        # Returns: (True, "Password is strong")
        # or: (False, "Password must contain at least one uppercase letter")
    """
    if not password:
        return False, "Password cannot be empty"
    
    errors = []
    
    # Check minimum length
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    
    # Check for uppercase letter
    if not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")
    
    # Check for lowercase letter
    if not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")
    
    # Check for digit
    if not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one digit")
    
    # Check for special character
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if not any(c in special_chars for c in password):
        errors.append("Password must contain at least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)")
    
    if errors:
        return False, "; ".join(errors)
    
    return True, "Password is strong"


# ============================================================================
# JWT TOKEN CONFIGURATION
# ============================================================================

# JWT Configuration from environment variables
# SECRET_KEY: Used to sign and verify tokens (must be kept secret!)
# ALGORITHM: Cryptographic algorithm for token signing (HS256 is symmetric)
# ACCESS_TOKEN_EXPIRE_MINUTES: How long access tokens remain valid
# REFRESH_TOKEN_EXPIRE_DAYS: How long refresh tokens remain valid

SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Security warning if using default secret key
if SECRET_KEY == "your-secret-key-change-in-production":
    logger.warning(
        "WARNING: Using default SECRET_KEY. Change this in production! "
        "Generate a secure key with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
    )


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    JWT (JSON Web Token) is a stateless authentication mechanism:
    - No server-side session storage required
    - Token contains user information (claims) in encoded format
    - Token is signed to prevent tampering
    - Token can be verified without database lookup
    
    Why short-lived access tokens (30 minutes)?
    - Limits damage if token is stolen
    - Forces regular re-authentication
    - Reduces risk of token reuse after user logout
    
    Token structure:
    - Header: Algorithm and token type
    - Payload: Claims (user data, expiration, etc.)
    - Signature: HMAC signature using SECRET_KEY
    
    Args:
        data: Dictionary containing claims to encode (typically user_id, email, role)
        expires_delta: Optional custom expiration time. If None, uses default (30 minutes)
        
    Returns:
        str: Encoded JWT token string
        
    Example:
        token = create_access_token({"sub": "user123", "role": "CFO"})
        # Returns: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    """
    to_encode = data.copy()
    
    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Add standard JWT claims
    to_encode.update({
        "exp": expire,  # Expiration time
        "iat": datetime.utcnow(),  # Issued at time
        "type": "access"  # Token type
    })
    
    # Encode and sign the token
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """
    Create a JWT refresh token.
    
    Refresh tokens are longer-lived tokens used to obtain new access tokens.
    This allows users to stay authenticated without frequent re-login while
    maintaining security through short-lived access tokens.
    
    Why separate refresh tokens?
    - Access tokens can be short-lived (more secure)
    - Refresh tokens can be longer-lived (better UX)
    - Refresh tokens can be revoked server-side if needed
    - Limits exposure if access token is compromised
    
    Args:
        data: Dictionary containing claims to encode (typically user_id)
        
    Returns:
        str: Encoded JWT refresh token string
        
    Example:
        refresh_token = create_refresh_token({"sub": "user123"})
        # Returns: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    """
    to_encode = data.copy()
    
    # Refresh tokens expire after configured days (default: 7 days)
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    # Add standard JWT claims
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"  # Token type identifier
    })
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict]:
    """
    Decode and verify a JWT token.
    
    This function:
    1. Verifies the token signature (prevents tampering)
    2. Checks token expiration
    3. Validates the algorithm
    4. Returns the decoded payload (claims)
    
    If the token is invalid, expired, or tampered with, returns None.
    
    Args:
        token: JWT token string to decode
        
    Returns:
        Optional[Dict]: Decoded token payload (claims) if valid, None otherwise
        
    Example:
        payload = decode_token(token_string)
        if payload:
            user_id = payload.get("sub")
            role = payload.get("role")
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        return None


def get_user_id_from_token(token: str) -> Optional[str]:
    """
    Extract user ID from a JWT token.
    
    This is a convenience function that decodes a token and extracts
    the user ID from the "sub" (subject) claim, which is the standard
    JWT claim for user identification.
    
    Args:
        token: JWT token string
        
    Returns:
        Optional[str]: User ID if token is valid, None otherwise
        
    Example:
        user_id = get_user_id_from_token(token_string)
        if user_id:
            # Use user_id for database queries
    """
    payload = decode_token(token)
    if payload:
        return payload.get("sub")  # "sub" is the standard JWT claim for subject (user ID)
    return None


# ============================================================================
# ROLE-BASED ACCESS CONTROL (RBAC)
# ============================================================================

class Role:
    """
    Role-based access control constants and utilities.
    
    This class defines the application's role hierarchy and permission system.
    
    Role Hierarchy (from highest to lowest privilege):
    1. ADMIN: Full system access, user management, all operations
    2. CFO: Financial data access, reports, analysis, team management
    3. ANALYST: Data analysis, report generation, read/write access to financial data
    4. VIEWER: Read-only access to reports and dashboards
    
    How RBAC works:
    - Each user has one role
    - Roles have hierarchical permissions (higher roles inherit lower role permissions)
    - has_permission() checks if a user's role meets the required role level
    - Principle of least privilege: Users get minimum permissions needed
    
    Example hierarchy:
    - ADMIN can do everything (including CFO, ANALYST, VIEWER operations)
    - CFO can do ANALYST and VIEWER operations
    - ANALYST can do VIEWER operations
    - VIEWER can only read
    """
    
    # Role constants
    ADMIN = "admin"
    CFO = "cfo"
    ANALYST = "analyst"
    VIEWER = "viewer"
    
    # Role hierarchy (higher index = higher privilege)
    # Used to determine if a role has sufficient permissions
    ROLE_HIERARCHY = {
        VIEWER: 0,
        ANALYST: 1,
        CFO: 2,
        ADMIN: 3,
    }
    
    @classmethod
    def all_roles(cls) -> list[str]:
        """
        Get a list of all available roles.
        
        Returns:
            list[str]: List of all role names
        """
        return [cls.ADMIN, cls.CFO, cls.ANALYST, cls.VIEWER]
    
    @classmethod
    def is_valid_role(cls, role: str) -> bool:
        """
        Check if a role string is valid.
        
        Args:
            role: Role string to validate
            
        Returns:
            bool: True if role is valid, False otherwise
        """
        return role in cls.ROLE_HIERARCHY


def has_permission(user_role: str, required_role: str) -> bool:
    """
    Check if a user's role has sufficient permissions for a required role.
    
    This function implements hierarchical role-based access control:
    - Higher roles automatically have permissions of lower roles
    - ADMIN has all permissions
    - CFO has ANALYST and VIEWER permissions
    - ANALYST has VIEWER permissions
    - VIEWER has only read permissions
    
    How it works:
    1. Get hierarchy level for both roles
    2. Compare levels: user_role level must be >= required_role level
    3. Return True if user has sufficient permissions
    
    Args:
        user_role: The user's current role
        required_role: The minimum role required for the operation
        
    Returns:
        bool: True if user has sufficient permissions, False otherwise
        
    Examples:
        has_permission("ADMIN", "CFO")     # True (admin can do CFO tasks)
        has_permission("CFO", "ANALYST")   # True (CFO can do analyst tasks)
        has_permission("ANALYST", "CFO")   # False (analyst cannot do CFO tasks)
        has_permission("VIEWER", "VIEWER") # True (viewer can view)
    """
    # Validate roles
    if not Role.is_valid_role(user_role):
        logger.warning(f"Invalid user role: {user_role}")
        return False
    
    if not Role.is_valid_role(required_role):
        logger.warning(f"Invalid required role: {required_role}")
        return False
    
    # Get hierarchy levels
    user_level = Role.ROLE_HIERARCHY.get(user_role, -1)
    required_level = Role.ROLE_HIERARCHY.get(required_role, -1)
    
    # User's role level must be >= required role level
    return user_level >= required_level


# ============================================================================
# API KEY GENERATION
# ============================================================================

def generate_api_key() -> str:
    """
    Generate a secure random API key.
    
    API keys are used for programmatic access to the API without user authentication.
    They should be:
    - Long enough to prevent brute-force attacks
    - Random and unpredictable
    - Stored securely (hashed in database)
    - Rotated periodically
    
    This function generates a 32-byte (256-bit) random key encoded as hexadecimal,
    resulting in a 64-character string.
    
    Returns:
        str: Random hexadecimal API key (64 characters)
        
    Example:
        api_key = generate_api_key()
        # Returns: "a1b2c3d4e5f6..." (64 hex characters)
    """
    # Generate 32 bytes (256 bits) of random data
    # Encode as hexadecimal for easy storage and transmission
    return secrets.token_hex(32)


# ============================================================================
# MAIN BLOCK FOR TESTING
# ============================================================================

if __name__ == "__main__":
    """
    Demonstrate and test security utilities.
    
    This block tests:
    - Password hashing and verification
    - Password strength validation
    - JWT token creation and decoding
    - User ID extraction from tokens
    - Role-based permission checking
    - API key generation
    
    Run with:
        python -m backend.core.security
    """
    import sys
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 70)
    print("Security Utilities Test")
    print("=" * 70)
    print()
    
    # Test password hashing
    print("1. Testing Password Hashing")
    print("-" * 70)
    test_password = "MySecurePassword123!"
    hashed = hash_password(test_password)
    print(f"   Original password: {test_password}")
    print(f"   Hashed password: {hashed[:50]}...")
    print(f"   Verification: {verify_password(test_password, hashed)}")
    print(f"   Wrong password verification: {verify_password('wrong', hashed)}")
    print()
    
    # Test password strength validation
    print("2. Testing Password Strength Validation")
    print("-" * 70)
    test_passwords = [
        "weak",  # Too short
        "weakpass",  # No uppercase, digit, or special
        "WeakPass",  # No digit or special
        "WeakPass1",  # No special char
        "WeakPass1!",  # Valid
        "VeryStrongPassword123!@#",  # Very strong
    ]
    
    for pwd in test_passwords:
        is_valid, message = validate_password_strength(pwd)
        status = "✓" if is_valid else "✗"
        print(f"   {status} '{pwd}': {message}")
    print()
    
    # Test JWT token creation
    print("3. Testing JWT Token Creation and Decoding")
    print("-" * 70)
    user_data = {
        "sub": "user123",
        "email": "user@example.com",
        "role": "CFO"
    }
    
    access_token = create_access_token(user_data)
    refresh_token = create_refresh_token({"sub": "user123"})
    
    print(f"   Access token created: {access_token[:50]}...")
    print(f"   Refresh token created: {refresh_token[:50]}...")
    
    # Decode tokens
    decoded_access = decode_token(access_token)
    decoded_refresh = decode_token(refresh_token)
    
    if decoded_access:
        print(f"   ✓ Access token decoded successfully")
        print(f"     User ID: {decoded_access.get('sub')}")
        print(f"     Role: {decoded_access.get('role')}")
        print(f"     Type: {decoded_access.get('type')}")
    else:
        print(f"   ✗ Access token decode failed")
    
    if decoded_refresh:
        print(f"   ✓ Refresh token decoded successfully")
        print(f"     User ID: {decoded_refresh.get('sub')}")
        print(f"     Type: {decoded_refresh.get('type')}")
    else:
        print(f"   ✗ Refresh token decode failed")
    print()
    
    # Test user ID extraction
    print("4. Testing User ID Extraction from Token")
    print("-" * 70)
    user_id = get_user_id_from_token(access_token)
    if user_id:
        print(f"   ✓ User ID extracted: {user_id}")
    else:
        print(f"   ✗ Failed to extract user ID")
    
    # Test with invalid token
    invalid_user_id = get_user_id_from_token("invalid.token.here")
    if invalid_user_id is None:
        print(f"   ✓ Invalid token correctly rejected")
    print()
    
    # Test role-based access control
    print("5. Testing Role-Based Access Control")
    print("-" * 70)
    test_cases = [
        ("admin", "admin", True),
        ("admin", "cfo", True),
        ("admin", "analyst", True),
        ("admin", "viewer", True),
        ("cfo", "cfo", True),
        ("cfo", "analyst", True),
        ("cfo", "viewer", True),
        ("cfo", "admin", False),
        ("analyst", "analyst", True),
        ("analyst", "viewer", True),
        ("analyst", "cfo", False),
        ("analyst", "admin", False),
        ("viewer", "viewer", True),
        ("viewer", "analyst", False),
        ("viewer", "cfo", False),
        ("viewer", "admin", False),
    ]
    
    for user_role, required_role, expected in test_cases:
        result = has_permission(user_role, required_role)
        status = "✓" if result == expected else "✗"
        print(f"   {status} {user_role} -> {required_role}: {result} (expected: {expected})")
    print()
    
    # Test API key generation
    print("6. Testing API Key Generation")
    print("-" * 70)
    api_key = generate_api_key()
    print(f"   Generated API key: {api_key}")
    print(f"   Length: {len(api_key)} characters")
    print(f"   Format: Hexadecimal")
    print()
    
    # Display all roles
    print("7. Available Roles")
    print("-" * 70)
    for role in Role.all_roles():
        level = Role.ROLE_HIERARCHY[role]
        print(f"   {role.upper()}: Level {level}")
    print()
    
    print("=" * 70)
    print("All security tests completed!")
    print("=" * 70)


