"""
User Database Model and CRUD Operations

This module defines the User model for the FP&A CFO Crew AI application,
including database schema, model methods, and complete CRUD operations.

Key Concepts:
1. ORM (Object-Relational Mapping):
   - SQLAlchemy maps Python classes to database tables
   - Model instances represent database rows
   - Relationships can be defined between models (foreign keys)

2. Soft Delete:
   - Instead of permanently deleting records, we mark them as inactive
   - Preserves data integrity and audit trails
   - Allows recovery of accidentally deleted users
   - is_active=False means user is deactivated but data remains

3. Password Security:
   - Never store plain text passwords
   - Store bcrypt hashes (one-way encryption)
   - Verify passwords by hashing input and comparing hashes
   - Original password cannot be recovered from hash

4. Role-Based Permissions:
   - Each user has a role (admin, cfo, analyst, viewer)
   - Permission checks use role hierarchy
   - Methods like can_execute_agents() check role permissions
"""

from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Index
from sqlalchemy.orm import Session

from backend.core.database import Base
from backend.core.security import (
    hash_password,
    verify_password,
    generate_api_key,
    Role,
    has_permission
)


class User(Base):
    """
    User model representing application users.
    
    This model stores user authentication and authorization information.
    Each user can authenticate via email/password or API key.
    
    Table Structure:
    - users: Database table name
    - Indexes on email, api_key for fast lookups
    """
    
    __tablename__ = "users"
    
    # Primary key: Unique identifier for each user
    # Auto-incrementing integer, indexed for fast lookups
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Email: Used for user login and identification
    # Unique constraint prevents duplicate accounts
    # Indexed for fast email-based lookups
    # Maximum 255 characters (standard email length limit)
    email = Column(String(255), unique=True, index=True, nullable=False)
    
    # Username: Display name for the user
    # Not necessarily unique (users can have same display names)
    # Maximum 100 characters
    username = Column(String(100), nullable=False)
    
    # Hashed Password: Bcrypt hash of user's password
    # Never store plain text passwords!
    # Bcrypt hashes are ~60 characters, but we allow 255 for future algorithms
    # This is a one-way hash - original password cannot be recovered
    hashed_password = Column(String(255), nullable=False)
    
    # Role: User's permission level
    # Default is "viewer" (lowest privilege)
    # Valid values: admin, cfo, analyst, viewer
    # Role determines what actions user can perform
    role = Column(String(50), nullable=False, default=Role.VIEWER)
    
    # Is Active: Soft delete flag
    # When False, user is deactivated but not deleted
    # Deactivated users cannot log in
    # Useful for: temporary suspensions, account recovery, audit trails
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Is Verified: Email verification status
    # When False, user may have limited access until email is verified
    # Prevents spam accounts and ensures valid email addresses
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Created At: Timestamp when user account was created
    # Automatically set to current UTC time on creation
    # Useful for: account age tracking, audit logs, analytics
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Last Login: Timestamp of last successful login
    # Nullable because new users haven't logged in yet
    # Useful for: security monitoring, inactive account detection
    last_login = Column(DateTime, nullable=True)
    
    # API Key: Unique key for programmatic API access
    # Nullable because not all users need API access
    # Unique constraint prevents key collisions
    # Indexed for fast API key-based authentication
    # Format: 64-character hexadecimal string
    api_key = Column(String(255), unique=True, nullable=True, index=True)
    
    # Database indexes for performance
    # Composite indexes can be added here if needed for complex queries
    __table_args__ = (
        Index('idx_user_email_active', 'email', 'is_active'),  # Fast lookup of active users by email
    )
    
    def __repr__(self) -> str:
        """
        String representation of User instance.
        
        Useful for debugging and logging.
        Does not include sensitive information like password or API key.
        
        Returns:
            str: Human-readable representation
        """
        return f"<User(id={self.id}, email='{self.email}', username='{self.username}', role='{self.role}')>"
    
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """
        Convert User instance to dictionary.
        
        Excludes sensitive information by default (password, API key).
        Useful for API responses and serialization.
        
        Args:
            include_sensitive: If True, includes hashed_password and api_key
            
        Returns:
            dict: User data as dictionary
        """
        data = {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "role": self.role,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }
        
        if include_sensitive:
            data["hashed_password"] = self.hashed_password
            data["api_key"] = self.api_key
        
        return data
    
    @property
    def is_admin(self) -> bool:
        """
        Check if user has admin role.
        
        Returns:
            bool: True if user is admin
        """
        return self.role == Role.ADMIN
    
    @property
    def is_cfo(self) -> bool:
        """
        Check if user has CFO role.
        
        Returns:
            bool: True if user is CFO
        """
        return self.role == Role.CFO
    
    @property
    def is_analyst(self) -> bool:
        """
        Check if user has analyst role.
        
        Returns:
            bool: True if user is analyst
        """
        return self.role == Role.ANALYST
    
    def can_execute_agents(self) -> bool:
        """
        Check if user's role allows executing AI agents.
        
        Agent execution requires analyst-level permissions or higher.
        This includes: CFO, Analyst roles (and Admin by hierarchy).
        
        Returns:
            bool: True if user can execute agents
        """
        return has_permission(self.role, Role.ANALYST)
    
    def can_manage_users(self) -> bool:
        """
        Check if user can manage other users.
        
        Only administrators can manage users (create, update, delete).
        
        Returns:
            bool: True if user is admin
        """
        return self.role == Role.ADMIN
    
    def can_view_all_reports(self) -> bool:
        """
        Check if user can view all financial reports.
        
        CFO and Admin roles can view all reports.
        Analysts and Viewers have limited access.
        
        Returns:
            bool: True if user is admin or CFO
        """
        return has_permission(self.role, Role.CFO)
    
    def verify_password(self, plain_password: str) -> bool:
        """
        Verify a plain text password against the stored hash.
        
        This is a convenience method that uses the security module's
        verify_password function.
        
        Args:
            plain_password: Plain text password to verify
            
        Returns:
            bool: True if password matches
        """
        return verify_password(plain_password, self.hashed_password)


class UserCRUD:
    """
    CRUD (Create, Read, Update, Delete) operations for User model.
    
    This class provides static methods for all user database operations.
    All methods require a database session (db) parameter.
    
    Why static methods?
    - No need to instantiate the class
    - Clear separation of concerns
    - Easy to use in FastAPI dependencies
    - Can be called directly: UserCRUD.create_user(db, ...)
    
    Session Management:
    - All methods expect an active database session
    - Methods do NOT commit transactions (caller must commit)
    - This allows multiple operations in a single transaction
    """
    
    @staticmethod
    def create_user(
        db: Session,
        email: str,
        username: str,
        password: str,
        role: str = Role.VIEWER,
        is_verified: bool = False
    ) -> User:
        """
        Create a new user in the database.
        
        This method:
        1. Hashes the password using bcrypt
        2. Creates a new User instance
        3. Adds it to the session
        4. Returns the created user
        
        Note: Does NOT commit the transaction. Caller must commit.
        
        Args:
            db: Database session
            email: User's email address (must be unique)
            username: User's display name
            password: Plain text password (will be hashed)
            role: User's role (default: viewer)
            is_verified: Email verification status (default: False)
            
        Returns:
            User: Created user instance
            
        Raises:
            IntegrityError: If email already exists
        """
        # Hash the password before storing
        hashed_password = hash_password(password)
        
        # Create user instance
        user = User(
            email=email,
            username=username,
            hashed_password=hashed_password,
            role=role,
            is_verified=is_verified,
            is_active=True
        )
        
        # Add to session
        db.add(user)
        db.flush()  # Flush to get the ID without committing
        
        return user
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """
        Retrieve a user by email address.
        
        Email is unique, so this returns at most one user.
        Used for login and user lookup operations.
        
        Args:
            db: Database session
            email: Email address to search for
            
        Returns:
            Optional[User]: User if found, None otherwise
        """
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """
        Retrieve a user by ID.
        
        ID is the primary key, so this is the fastest lookup method.
        
        Args:
            db: Database session
            user_id: User's ID
            
        Returns:
            Optional[User]: User if found, None otherwise
        """
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_user_by_api_key(db: Session, api_key: str) -> Optional[User]:
        """
        Retrieve a user by API key.
        
        Used for API key-based authentication.
        Only returns active users (is_active=True).
        
        Args:
            db: Database session
            api_key: API key to search for
            
        Returns:
            Optional[User]: Active user if found, None otherwise
        """
        return db.query(User).filter(
            User.api_key == api_key,
            User.is_active == True
        ).first()
    
    @staticmethod
    def get_all_users(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False
    ) -> List[User]:
        """
        Retrieve all users with pagination.
        
        Useful for user management interfaces and admin panels.
        By default, excludes inactive (soft-deleted) users.
        
        Args:
            db: Database session
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            include_inactive: If True, includes deactivated users
            
        Returns:
            List[User]: List of user instances
        """
        query = db.query(User)
        
        # Filter out inactive users unless explicitly requested
        if not include_inactive:
            query = query.filter(User.is_active == True)
        
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def update_user(db: Session, user: User, **kwargs) -> User:
        """
        Update user fields.
        
        This method allows updating any user field by passing keyword arguments.
        Common updates: email, username, role, is_verified, etc.
        
        Note: Does NOT update password. Use a separate method for password changes.
        Note: Does NOT commit the transaction. Caller must commit.
        
        Args:
            db: Database session
            user: User instance to update
            **kwargs: Field names and values to update
            
        Returns:
            User: Updated user instance
            
        Example:
            UserCRUD.update_user(db, user, role=Role.CFO, is_verified=True)
        """
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        db.flush()  # Flush changes to database without committing
        return user
    
    @staticmethod
    def update_last_login(db: Session, user: User) -> None:
        """
        Update user's last login timestamp.
        
        Called after successful authentication to track login activity.
        
        Args:
            db: Database session
            user: User instance to update
        """
        user.last_login = datetime.utcnow()
        db.flush()
    
    @staticmethod
    def generate_api_key_for_user(db: Session, user: User) -> str:
        """
        Generate and assign a new API key for a user.
        
        If user already has an API key, it will be replaced.
        The new key is automatically saved to the database.
        
        Args:
            db: Database session
            user: User instance to generate key for
            
        Returns:
            str: Generated API key (also stored in user.api_key)
        """
        api_key = generate_api_key()
        user.api_key = api_key
        db.flush()
        return api_key
    
    @staticmethod
    def deactivate_user(db: Session, user: User) -> None:
        """
        Soft delete a user by setting is_active=False.
        
        Soft delete preserves the user record in the database but prevents
        login and access. This is safer than hard delete because:
        - Data is preserved for audit trails
        - Can be reactivated if needed
        - Maintains referential integrity with related records
        
        Args:
            db: Database session
            user: User instance to deactivate
        """
        user.is_active = False
        db.flush()
    
    @staticmethod
    def delete_user(db: Session, user: User) -> None:
        """
        Permanently delete a user from the database.
        
        WARNING: This is a hard delete - the user record will be permanently
        removed from the database. Use with extreme caution!
        
        Prefer deactivate_user() for most use cases to preserve data.
        
        Args:
            db: Database session
            user: User instance to delete
        """
        db.delete(user)
        db.flush()
    
    @staticmethod
    def verify_user_email(db: Session, user: User) -> None:
        """
        Mark user's email as verified.
        
        Called after user clicks email verification link.
        
        Args:
            db: Database session
            user: User instance to verify
        """
        user.is_verified = True
        db.flush()
    
    @staticmethod
    def change_password(db: Session, user: User, new_password: str) -> None:
        """
        Change user's password.
        
        Hashes the new password before storing.
        Should be called after verifying the old password.
        
        Args:
            db: Database session
            user: User instance to update
            new_password: New plain text password
        """
        user.hashed_password = hash_password(new_password)
        db.flush()


# ============================================================================
# MAIN BLOCK FOR TESTING
# ============================================================================

if __name__ == "__main__":
    """
    Test User model and CRUD operations.
    
    This block demonstrates:
    - Database initialization
    - User creation
    - User retrieval
    - Permission checking
    - CRUD operations
    
    Run with:
        python -m backend.models.user
    """
    import sys
    from backend.core.database import init_db, get_db_context, check_connection
    
    print("=" * 70)
    print("User Model and CRUD Operations Test")
    print("=" * 70)
    print()
    
    # Check database connection
    print("1. Checking database connection...")
    if not check_connection():
        print("   ✗ Database connection failed")
        sys.exit(1)
    print("   ✓ Database connection successful")
    print()
    
    # Initialize database (create tables)
    print("2. Initializing database tables...")
    try:
        init_db()
        print("   ✓ Database tables initialized")
    except Exception as e:
        print(f"   ✗ Database initialization failed: {e}")
        sys.exit(1)
    print()
    
    # Test user creation
    print("3. Creating test users...")
    try:
        with get_db_context() as db:
            # Create admin user
            admin_user = UserCRUD.create_user(
                db=db,
                email="admin@example.com",
                username="Admin User",
                password="AdminPass123!",
                role=Role.ADMIN,
                is_verified=True
            )
            print(f"   ✓ Created admin user: {admin_user}")
            
            # Create CFO user
            cfo_user = UserCRUD.create_user(
                db=db,
                email="cfo@example.com",
                username="CFO User",
                password="CFOPass123!",
                role=Role.CFO,
                is_verified=True
            )
            print(f"   ✓ Created CFO user: {cfo_user}")
            
            # Create analyst user
            analyst_user = UserCRUD.create_user(
                db=db,
                email="analyst@example.com",
                username="Analyst User",
                password="AnalystPass123!",
                role=Role.ANALYST,
                is_verified=True
            )
            print(f"   ✓ Created analyst user: {analyst_user}")
            
            # Commit all users
            db.commit()
            print("   ✓ All users committed to database")
    except Exception as e:
        print(f"   ✗ User creation failed: {e}")
        sys.exit(1)
    print()
    
    # Test user retrieval
    print("4. Testing user retrieval...")
    try:
        with get_db_context() as db:
            # Retrieve by email
            retrieved_user = UserCRUD.get_user_by_email(db, "admin@example.com")
            if retrieved_user:
                print(f"   ✓ Retrieved user by email: {retrieved_user}")
            else:
                print("   ✗ Failed to retrieve user by email")
            
            # Retrieve by ID
            if retrieved_user:
                user_by_id = UserCRUD.get_user_by_id(db, retrieved_user.id)
                if user_by_id:
                    print(f"   ✓ Retrieved user by ID: {user_by_id}")
            
            # Get all users
            all_users = UserCRUD.get_all_users(db, limit=10)
            print(f"   ✓ Retrieved {len(all_users)} users")
    except Exception as e:
        print(f"   ✗ User retrieval failed: {e}")
    print()
    
    # Test password verification
    print("5. Testing password verification...")
    try:
        with get_db_context() as db:
            user = UserCRUD.get_user_by_email(db, "admin@example.com")
            if user:
                # Test correct password
                if user.verify_password("AdminPass123!"):
                    print("   ✓ Password verification successful")
                else:
                    print("   ✗ Password verification failed")
                
                # Test wrong password
                if not user.verify_password("WrongPassword"):
                    print("   ✓ Wrong password correctly rejected")
    except Exception as e:
        print(f"   ✗ Password verification test failed: {e}")
    print()
    
    # Test permission methods
    print("6. Testing permission methods...")
    try:
        with get_db_context() as db:
            admin = UserCRUD.get_user_by_email(db, "admin@example.com")
            cfo = UserCRUD.get_user_by_email(db, "cfo@example.com")
            analyst = UserCRUD.get_user_by_email(db, "analyst@example.com")
            
            if admin:
                print(f"   Admin user:")
                print(f"     - is_admin: {admin.is_admin}")
                print(f"     - can_execute_agents: {admin.can_execute_agents()}")
                print(f"     - can_manage_users: {admin.can_manage_users()}")
                print(f"     - can_view_all_reports: {admin.can_view_all_reports()}")
            
            if cfo:
                print(f"   CFO user:")
                print(f"     - is_cfo: {cfo.is_cfo}")
                print(f"     - can_execute_agents: {cfo.can_execute_agents()}")
                print(f"     - can_manage_users: {cfo.can_manage_users()}")
                print(f"     - can_view_all_reports: {cfo.can_view_all_reports()}")
            
            if analyst:
                print(f"   Analyst user:")
                print(f"     - is_analyst: {analyst.is_analyst}")
                print(f"     - can_execute_agents: {analyst.can_execute_agents()}")
                print(f"     - can_manage_users: {analyst.can_manage_users()}")
                print(f"     - can_view_all_reports: {analyst.can_view_all_reports()}")
    except Exception as e:
        print(f"   ✗ Permission test failed: {e}")
    print()
    
    # Test CRUD operations
    print("7. Testing CRUD operations...")
    try:
        with get_db_context() as db:
            # Update user
            user = UserCRUD.get_user_by_email(db, "analyst@example.com")
            if user:
                UserCRUD.update_user(db, user, username="Updated Analyst")
                print(f"   ✓ Updated user: {user.username}")
            
            # Generate API key
            if user:
                api_key = UserCRUD.generate_api_key_for_user(db, user)
                print(f"   ✓ Generated API key: {api_key[:20]}...")
                
                # Test API key lookup
                user_by_key = UserCRUD.get_user_by_api_key(db, api_key)
                if user_by_key:
                    print(f"   ✓ Retrieved user by API key: {user_by_key.email}")
            
            # Update last login
            if user:
                UserCRUD.update_last_login(db, user)
                print(f"   ✓ Updated last login: {user.last_login}")
            
            db.commit()
    except Exception as e:
        print(f"   ✗ CRUD operations test failed: {e}")
    print()
    
    # Test to_dict method
    print("8. Testing to_dict method...")
    try:
        with get_db_context() as db:
            user = UserCRUD.get_user_by_email(db, "admin@example.com")
            if user:
                user_dict = user.to_dict()
                print(f"   ✓ User dictionary (without sensitive data):")
                for key, value in user_dict.items():
                    print(f"     {key}: {value}")
    except Exception as e:
        print(f"   ✗ to_dict test failed: {e}")
    print()
    
    print("=" * 70)
    print("All user model tests completed!")
    print("=" * 70)


