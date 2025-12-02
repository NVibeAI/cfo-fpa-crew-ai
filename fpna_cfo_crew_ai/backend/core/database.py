"""
Database Configuration and Connection Management

This module provides database connection management, session handling, and
initialization utilities for the FP&A CFO Crew AI application.

Key Components:
- SQLAlchemy engine with connection pooling
- Session factory for database operations
- FastAPI dependency for request-scoped sessions
- Context manager for standalone scripts
- Database initialization and health checks

Database Support:
- SQLite: Development and testing (default)
- PostgreSQL: Production deployments

Connection Pooling:
Connection pooling is crucial for performance and resource management:
- Reuses existing connections instead of creating new ones for each request
- Limits the number of concurrent database connections
- Automatically handles connection failures and retries
- Reduces connection overhead and improves response times

For this application:
- Base pool size: 5 connections (always available)
- Max overflow: 10 additional connections (created on demand)
- Total max connections: 15 (5 base + 10 overflow)
"""

import os
import logging
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

# Configure logging
logger = logging.getLogger(__name__)

# Base class for all database models
# All models should inherit from this Base class
Base = declarative_base()

# Database URL from environment variable
# Defaults to SQLite for development
# Format examples:
#   SQLite: sqlite:///./fpna_cfo.db
#   PostgreSQL: postgresql://user:password@localhost:5432/fpna_cfo
#   PostgreSQL (with SSL): postgresql://user:password@host:5432/dbname?sslmode=require
DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "sqlite:///./fpna_cfo.db"
)

# Determine if we're using SQLite or PostgreSQL
IS_SQLITE: bool = DATABASE_URL.startswith("sqlite")

# Connection pool configuration
# These settings optimize for both development and production:
# - Base pool size: 5 connections always available
# - Max overflow: 10 additional connections created on demand
# - Pool pre-ping: Verifies connections are alive before use (prevents stale connections)
POOL_CONFIG = {
    "poolclass": QueuePool,
    "pool_size": 5,  # Base number of connections to maintain
    "max_overflow": 10,  # Additional connections allowed beyond pool_size
    "pool_pre_ping": True,  # Verify connections before using them
    "pool_recycle": 3600,  # Recycle connections after 1 hour (PostgreSQL)
}

# SQLite-specific configuration
# SQLite doesn't support connection pooling in the same way as PostgreSQL
# We use NullPool for SQLite to avoid connection issues
if IS_SQLITE:
    POOL_CONFIG = {
        "poolclass": None,  # No pooling for SQLite
        "connect_args": {"check_same_thread": False},  # Allow multi-threaded access
    }

# Create SQLAlchemy engine
# The engine manages the connection pool and provides database connectivity
# pool_pre_ping=True ensures connections are tested before use, preventing
# errors from stale or closed connections
engine: Engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL query logging (useful for debugging)
    **POOL_CONFIG
)

# Session factory configuration
# sessionmaker creates a factory for producing Session objects
# 
# Configuration options:
# - autocommit=False: Changes require explicit commit() (recommended for data integrity)
# - autoflush=False: Don't automatically flush pending changes (gives more control)
# - bind=engine: Use the configured engine for all sessions
#
# When to use autocommit=False:
# - Allows transaction management (commit/rollback)
# - Better error handling (can rollback on errors)
# - Supports multiple operations in a single transaction
#
# When to use autoflush=False:
# - Prevents premature database writes
# - Allows batching multiple changes before flushing
# - More predictable behavior in complex operations
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency for database sessions.
    
    This function provides a request-scoped database session for FastAPI endpoints.
    It automatically handles session lifecycle:
    - Creates a new session at the start of the request
    - Yields the session to the endpoint
    - Closes the session after the request completes
    - Rolls back any uncommitted changes if an exception occurs
    
    Usage in FastAPI:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    
    The session is automatically closed by FastAPI's dependency system,
    even if an exception occurs in the endpoint.
    
    Yields:
        Session: SQLAlchemy database session
    """
    db: Session = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager for database sessions in standalone scripts.
    
    This function provides a context-managed database session for use outside
    of FastAPI (e.g., CLI scripts, background jobs, tests).
    
    When to use get_db_context() vs get_db():
    - get_db(): Use in FastAPI endpoints (automatic lifecycle management)
    - get_db_context(): Use in standalone scripts, CLI tools, or tests
    
    The context manager ensures:
    - Session is properly closed after use
    - Uncommitted changes are rolled back on exceptions
    - Resources are cleaned up even if errors occur
    
    Usage:
        with get_db_context() as db:
            user = User(name="John")
            db.add(user)
            db.commit()
    
    Yields:
        Session: SQLAlchemy database session
    """
    db: Session = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize the database by creating all tables.
    
    This function creates all database tables defined in models that inherit
    from Base. It should be called:
    - On application startup (for new deployments)
    - After adding new models
    - In database migration scripts
    
    Note: This uses create_all() which only creates tables that don't exist.
    It does NOT modify existing tables. For schema changes, use Alembic migrations.
    
    Raises:
        Exception: If table creation fails
    """
    try:
        logger.info("Initializing database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


def check_connection() -> bool:
    """
    Verify database connectivity by executing a simple query.
    
    This function tests if the database is accessible and responsive.
    It's useful for:
    - Health checks in monitoring systems
    - Startup validation
    - Connection troubleshooting
    
    Returns:
        bool: True if connection is successful, False otherwise
    """
    try:
        with engine.connect() as conn:
            # Execute a simple query to test connectivity
            # For SQLite: SELECT 1
            # For PostgreSQL: SELECT 1
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        logger.info("Database connection check: SUCCESS")
        return True
    except Exception as e:
        logger.error(f"Database connection check: FAILED - {e}")
        return False


def get_database_info() -> dict:
    """
    Get information about the current database configuration.
    
    Returns:
        dict: Database configuration information including:
            - database_type: SQLite or PostgreSQL
            - database_url: Connection string (with password masked)
            - pool_size: Connection pool size
            - max_overflow: Maximum overflow connections
    """
    # Mask password in URL for logging
    masked_url = DATABASE_URL
    if "@" in DATABASE_URL and "://" in DATABASE_URL:
        parts = DATABASE_URL.split("@")
        if len(parts) == 2:
            protocol_and_user = parts[0]
            if ":" in protocol_and_user:
                protocol, user_pass = protocol_and_user.rsplit(":", 1)
                user, _ = user_pass.rsplit(":", 1) if ":" in user_pass else (user_pass, "")
                masked_url = f"{protocol}:{user}:***@{parts[1]}"
    
    info = {
        "database_type": "SQLite" if IS_SQLITE else "PostgreSQL",
        "database_url": masked_url,
        "pool_size": POOL_CONFIG.get("pool_size", "N/A"),
        "max_overflow": POOL_CONFIG.get("max_overflow", "N/A"),
        "pool_pre_ping": POOL_CONFIG.get("pool_pre_ping", False),
    }
    return info


# Main block for testing and initialization
if __name__ == "__main__":
    """
    Test database connection and initialization.
    
    Run this script directly to:
    1. Test database connectivity
    2. Initialize database tables
    3. Display database configuration
    
    Usage:
        python -m backend.core.database
    """
    import sys
    
    # Configure logging for testing
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("Database Configuration Test")
    print("=" * 60)
    print()
    
    # Display database information
    db_info = get_database_info()
    print("Database Configuration:")
    for key, value in db_info.items():
        print(f"  {key}: {value}")
    print()
    
    # Test connection
    print("Testing database connection...")
    if check_connection():
        print("✓ Database connection: SUCCESS")
    else:
        print("✗ Database connection: FAILED")
        sys.exit(1)
    print()
    
    # Initialize database
    print("Initializing database tables...")
    try:
        init_db()
        print("✓ Database initialization: SUCCESS")
    except Exception as e:
        print(f"✗ Database initialization: FAILED - {e}")
        sys.exit(1)
    print()
    
    # Test session creation
    print("Testing session creation...")
    try:
        with get_db_context() as db:
            # Execute a simple query
            result = db.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            if row and row[0] == 1:
                print("✓ Session creation: SUCCESS")
            else:
                print("✗ Session creation: FAILED - Unexpected result")
                sys.exit(1)
    except Exception as e:
        print(f"✗ Session creation: FAILED - {e}")
        sys.exit(1)
    print()
    
    print("=" * 60)
    print("All database tests passed!")
    print("=" * 60)


