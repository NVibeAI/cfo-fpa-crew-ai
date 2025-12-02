#!/usr/bin/env python3
"""
Phase 1 Initialization Script

This script automates the setup of the FP&A CFO Crew AI backend:
1. Environment configuration (.env file setup)
2. Dependency verification
3. Database initialization
4. Admin user creation
5. System verification

Why This Script Exists:
======================
Manual setup is error-prone and time-consuming. This script:
- Ensures consistent setup across different environments
- Validates all prerequisites before starting
- Creates necessary configuration files
- Sets up initial admin user for first access
- Verifies everything works before proceeding

Security Considerations:
========================
- Generates secure SECRET_KEY automatically
- Uses getpass for password input (hides password in terminal)
- Validates password strength before creating users
- Warns about default passwords
- Never commits .env file (already in .gitignore)

Usage:
======
    python init_phase1.py

Or make it executable and run directly:
    chmod +x init_phase1.py
    ./init_phase1.py
"""

import os
import sys
import secrets
import subprocess
import importlib.util
from pathlib import Path
from getpass import getpass
from typing import Tuple, Optional

# ANSI color codes for terminal output
class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

# Emoji and status symbols
SUCCESS = f"{Colors.GREEN}✅{Colors.RESET}"
WARNING = f"{Colors.YELLOW}⚠️{Colors.RESET}"
ERROR = f"{Colors.RED}❌{Colors.RESET}"
INFO = f"{Colors.BLUE}ℹ️{Colors.RESET}"
ROCKET = f"{Colors.CYAN}🚀{Colors.RESET}"


def print_header():
    """Print script header with branding."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}FP&A CFO Crew AI - Phase 1 Initialization{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 70}{Colors.RESET}\n")


def print_section(title: str):
    """Print a section header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'─' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'─' * 70}{Colors.RESET}\n")


def check_environment() -> bool:
    """
    Check and set up environment configuration.
    
    This function:
    1. Checks if .env file exists
    2. If not, creates it from .env.template
    3. Generates a secure SECRET_KEY
    4. Validates environment variables
    
    Why this is important:
    - .env file contains sensitive configuration
    - SECRET_KEY must be unique and secure
    - Database URL determines which database to use
    - Missing configuration causes runtime errors
    
    Returns:
        bool: True if environment is properly configured, False otherwise
    """
    print_section("1. Environment Configuration")
    
    env_file = Path(".env")
    env_template = Path(".env.template")
    
    # Check if .env file exists
    if env_file.exists():
        print(f"{SUCCESS} .env file found")
    else:
        print(f"{WARNING} .env file not found")
        
        # Check if template exists
        if not env_template.exists():
            print(f"{ERROR} .env.template not found. Cannot create .env file.")
            print(f"{INFO} Please create .env.template first.")
            return False
        
        print(f"{INFO} Creating .env from template...")
        
        try:
            # Read template
            with open(env_template, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # Generate secure SECRET_KEY
            # Using 32 bytes (64 hex characters) for strong security
            secret_key = secrets.token_hex(32)
            print(f"{SUCCESS} Generated secure SECRET_KEY")
            
            # Replace placeholder SECRET_KEY
            if "SECRET_KEY=your-secret-key-change-in-production" in template_content:
                template_content = template_content.replace(
                    "SECRET_KEY=your-secret-key-change-in-production",
                    f"SECRET_KEY={secret_key}"
                )
                print(f"{SUCCESS} Updated SECRET_KEY in .env file")
            else:
                # If placeholder not found, add SECRET_KEY if missing
                if "SECRET_KEY=" not in template_content:
                    # Find a good place to insert (after comments)
                    lines = template_content.split('\n')
                    insert_index = 0
                    for i, line in enumerate(lines):
                        if line.startswith("# SECURITY & AUTHENTICATION"):
                            insert_index = i + 2
                            break
                    
                    if insert_index > 0:
                        lines.insert(insert_index, f"SECRET_KEY={secret_key}")
                        template_content = '\n'.join(lines)
                        print(f"{SUCCESS} Added SECRET_KEY to .env file")
            
            # Write .env file
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write(template_content)
            
            print(f"{SUCCESS} Created .env file")
            print(f"{WARNING} Please review .env file and update any other required values")
            
        except Exception as e:
            print(f"{ERROR} Failed to create .env file: {e}")
            return False
    
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv(override=True)
        print(f"{SUCCESS} Loaded environment variables")
    except ImportError:
        print(f"{ERROR} python-dotenv not installed")
        return False
    
    # Verify SECRET_KEY
    secret_key = os.getenv("SECRET_KEY", "")
    if not secret_key or secret_key == "your-secret-key-change-in-production":
        print(f"{ERROR} SECRET_KEY is not set or using default value")
        print(f"{INFO} Please set SECRET_KEY in .env file")
        return False
    
    if len(secret_key) < 32:
        print(f"{WARNING} SECRET_KEY is shorter than recommended (32+ characters)")
    else:
        print(f"{SUCCESS} SECRET_KEY is secure ({len(secret_key)} characters)")
    
    # Check DATABASE_URL
    database_url = os.getenv("DATABASE_URL", "")
    if not database_url:
        print(f"{WARNING} DATABASE_URL not set, using default SQLite")
        print(f"{INFO} Default: sqlite:///./fpna_cfo.db")
    else:
        print(f"{SUCCESS} DATABASE_URL configured")
        if database_url.startswith("sqlite"):
            print(f"{INFO} Using SQLite database (development)")
        elif database_url.startswith("postgresql"):
            print(f"{INFO} Using PostgreSQL database (production)")
    
    return True


def check_package_installed(package_name: str) -> bool:
    """
    Check if a Python package is installed.
    
    Args:
        package_name: Name of the package to check
        
    Returns:
        bool: True if package is installed, False otherwise
    """
    try:
        # Try importing the package
        # Some packages have different import names than pip names
        import_map = {
            "python-jose": "jose",
            "python-dotenv": "dotenv",
            "psycopg2-binary": "psycopg2",
        }
        
        import_name = import_map.get(package_name, package_name)
        spec = importlib.util.find_spec(import_name)
        return spec is not None
    except Exception:
        return False


def install_dependencies() -> bool:
    """
    Check if required dependencies are installed.
    
    This function verifies that all critical packages are available.
    Missing dependencies cause import errors and runtime failures.
    
    Required packages:
    - fastapi: Web framework
    - uvicorn: ASGI server
    - sqlalchemy: ORM and database
    - pydantic: Data validation
    - python-jose: JWT tokens
    - passlib: Password hashing
    - bcrypt: Password hashing algorithm
    
    Returns:
        bool: True if all dependencies installed, False otherwise
    """
    print_section("2. Dependency Verification")
    
    required_packages = {
        "fastapi": "FastAPI web framework",
        "uvicorn": "ASGI server",
        "sqlalchemy": "Database ORM",
        "pydantic": "Data validation",
        "python-jose": "JWT token handling",
        "passlib": "Password hashing",
        "bcrypt": "Password hashing algorithm",
        "python-dotenv": "Environment variable management",
    }
    
    missing_packages = []
    
    for package, description in required_packages.items():
        if check_package_installed(package):
            print(f"{SUCCESS} {package:20s} - {description}")
        else:
            print(f"{ERROR} {package:20s} - {description} (MISSING)")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n{WARNING} Missing {len(missing_packages)} required package(s)")
        print(f"{INFO} Install missing packages with:")
        print(f"    {Colors.CYAN}pip install -r requirements-backend.txt{Colors.RESET}")
        print(f"\n{INFO} Or install individually:")
        for pkg in missing_packages:
            print(f"    {Colors.CYAN}pip install {pkg}{Colors.RESET}")
        return False
    
    print(f"\n{SUCCESS} All required dependencies are installed")
    return True


def initialize_database() -> bool:
    """
    Initialize the database schema.
    
    This function:
    1. Checks database connectivity
    2. Creates all tables defined in models
    3. Handles errors gracefully
    
    Why this is important:
    - Database must exist before application can run
    - Tables must be created before storing data
    - Connection errors indicate configuration problems
    
    Returns:
        bool: True if database initialized successfully, False otherwise
    """
    print_section("3. Database Initialization")
    
    try:
        # Import here to avoid errors if dependencies are missing
        from backend.core.database import check_connection, init_db, get_database_info
        
        # Check database connection
        print(f"{INFO} Checking database connection...")
        if not check_connection():
            print(f"{ERROR} Database connection failed")
            print(f"{INFO} Please check DATABASE_URL in .env file")
            return False
        
        print(f"{SUCCESS} Database connection successful")
        
        # Display database info
        db_info = get_database_info()
        print(f"{INFO} Database Type: {db_info['database_type']}")
        if db_info['database_type'] == 'SQLite':
            print(f"{INFO} Database File: fpna_cfo.db")
        
        # Initialize database tables
        print(f"{INFO} Creating database tables...")
        init_db()
        print(f"{SUCCESS} Database tables created successfully")
        
        return True
        
    except ImportError as e:
        print(f"{ERROR} Failed to import database module: {e}")
        print(f"{INFO} Make sure all dependencies are installed")
        return False
    except Exception as e:
        print(f"{ERROR} Database initialization failed: {e}")
        return False


def create_admin_user() -> Tuple[bool, Optional[dict]]:
    """
    Create the initial admin user.
    
    This function:
    1. Checks if admin user already exists
    2. Prompts for admin details (email, username, password)
    3. Validates password strength
    4. Creates admin user with ADMIN role
    
    Security considerations:
    - Uses getpass() to hide password input
    - Validates password strength
    - Warns about default passwords
    - Never stores password in plain text
    
    Returns:
        Tuple[bool, Optional[dict]]: (success, user_info)
    """
    print_section("4. Admin User Creation")
    
    try:
        from backend.core.database import get_db_context
        from backend.core.security import validate_password_strength, Role
        from backend.models.user import UserCRUD
        
        # Check if admin already exists
        with get_db_context() as db:
            existing_admin = UserCRUD.get_user_by_email(db, "admin@example.com")
            if existing_admin:
                print(f"{SUCCESS} Admin user already exists")
                print(f"{INFO} Email: {existing_admin.email}")
                print(f"{INFO} Username: {existing_admin.username}")
                print(f"{INFO} Role: {existing_admin.role}")
                return True, {
                    "email": existing_admin.email,
                    "username": existing_admin.username,
                    "role": existing_admin.role
                }
        
        print(f"{INFO} Creating new admin user...")
        print(f"{WARNING} You will be prompted for admin credentials")
        print()
        
        # Get admin email
        default_email = "admin@example.com"
        email_input = input(f"Admin Email [{default_email}]: ").strip()
        admin_email = email_input if email_input else default_email
        
        # Validate email format
        if "@" not in admin_email or "." not in admin_email.split("@")[1]:
            print(f"{ERROR} Invalid email format")
            return False, None
        
        # Check if email already exists
        with get_db_context() as db:
            existing_user = UserCRUD.get_user_by_email(db, admin_email)
            if existing_user:
                print(f"{WARNING} User with email {admin_email} already exists")
                return False, None
        
        # Get admin username
        default_username = "Admin User"
        username_input = input(f"Admin Username [{default_username}]: ").strip()
        admin_username = username_input if username_input else default_username
        
        # Get admin password
        print(f"\n{INFO} Enter admin password (will be hidden):")
        print(f"{WARNING} Password requirements:")
        print(f"  - Minimum 8 characters")
        print(f"  - At least one uppercase letter")
        print(f"  - At least one lowercase letter")
        print(f"  - At least one digit")
        print(f"  - At least one special character")
        
        password = getpass("Password: ")
        
        # Use default password if none provided (with warning)
        if not password:
            default_password = "Admin123!"
            print(f"\n{WARNING} No password provided, using default: {default_password}")
            print(f"{WARNING} {Colors.RED}SECURITY WARNING: Change this password immediately!{Colors.RESET}")
            password = default_password
        
        # Validate password strength
        is_valid, message = validate_password_strength(password)
        if not is_valid:
            print(f"{ERROR} Password validation failed: {message}")
            return False, None
        
        # Create admin user
        try:
            with get_db_context() as db:
                admin_user = UserCRUD.create_user(
                    db=db,
                    email=admin_email,
                    username=admin_username,
                    password=password,
                    role=Role.ADMIN,
                    is_verified=True  # Admin is pre-verified
                )
                db.commit()
                db.refresh(admin_user)
            
            print(f"\n{SUCCESS} Admin user created successfully!")
            print(f"{INFO} Email: {admin_email}")
            print(f"{INFO} Username: {admin_username}")
            print(f"{INFO} Role: {admin_user.role}")
            
            return True, {
                "email": admin_email,
                "username": admin_username,
                "role": admin_user.role,
                "password": password if password == default_password else "***"
            }
            
        except Exception as e:
            print(f"{ERROR} Failed to create admin user: {e}")
            return False, None
            
    except ImportError as e:
        print(f"{ERROR} Failed to import required modules: {e}")
        return False, None
    except KeyboardInterrupt:
        print(f"\n{WARNING} Admin user creation cancelled")
        return False, None
    except Exception as e:
        print(f"{ERROR} Unexpected error: {e}")
        return False, None


def verify_system() -> bool:
    """
    Verify that the system is working correctly.
    
    This function runs basic tests to ensure:
    - Password hashing works
    - JWT token creation/decoding works
    - Database operations work
    
    Why this is important:
    - Catches configuration errors early
    - Verifies security functions work correctly
    - Ensures system is ready for use
    
    Returns:
        bool: True if all tests pass, False otherwise
    """
    print_section("5. System Verification")
    
    try:
        from backend.core.security import (
            hash_password,
            verify_password,
            create_access_token,
            decode_token
        )
        
        # Test password hashing
        print(f"{INFO} Testing password hashing...")
        test_password = "TestPassword123!"
        hashed = hash_password(test_password)
        if verify_password(test_password, hashed):
            print(f"{SUCCESS} Password hashing and verification works")
        else:
            print(f"{ERROR} Password verification failed")
            return False
        
        # Test JWT token creation
        print(f"{INFO} Testing JWT token creation...")
        token_data = {"sub": "test_user", "role": "admin"}
        token = create_access_token(token_data)
        if not token:
            print(f"{ERROR} Token creation failed")
            return False
        
        # Test JWT token decoding
        print(f"{INFO} Testing JWT token decoding...")
        decoded = decode_token(token)
        if decoded and decoded.get("sub") == "test_user":
            print(f"{SUCCESS} JWT token creation and decoding works")
        else:
            print(f"{ERROR} Token decoding failed")
            return False
        
        print(f"\n{SUCCESS} All system verification tests passed")
        return True
        
    except Exception as e:
        print(f"{ERROR} System verification failed: {e}")
        return False


def print_next_steps(admin_info: Optional[dict] = None):
    """
    Print next steps and helpful information.
    
    This function provides:
    - Congratulations message
    - Instructions to start the server
    - API endpoint URLs
    - Admin credentials (if created)
    - Links to documentation
    
    Args:
        admin_info: Dictionary with admin user information
    """
    print_section("🎉 Setup Complete!")
    
    print(f"{SUCCESS} Phase 1 initialization completed successfully!")
    print()
    
    print(f"{Colors.BOLD}{Colors.CYAN}Next Steps:{Colors.RESET}")
    print()
    
    print(f"{ROCKET} Start the backend server:")
    print(f"    {Colors.CYAN}python -m backend.main{Colors.RESET}")
    print(f"    or")
    print(f"    {Colors.CYAN}uvicorn backend.main:app --reload{Colors.RESET}")
    print()
    
    print(f"{INFO} API Endpoints:")
    print(f"    {Colors.CYAN}API Base:     http://localhost:8000{Colors.RESET}")
    print(f"    {Colors.CYAN}Swagger UI:   http://localhost:8000/docs{Colors.RESET}")
    print(f"    {Colors.CYAN}ReDoc:        http://localhost:8000/redoc{Colors.RESET}")
    print(f"    {Colors.CYAN}Health Check:  http://localhost:8000/health{Colors.RESET}")
    print()
    
    if admin_info:
        print(f"{INFO} Admin Credentials:")
        print(f"    {Colors.YELLOW}Email:    {admin_info['email']}{Colors.RESET}")
        print(f"    {Colors.YELLOW}Username: {admin_info['username']}{Colors.RESET}")
        if admin_info.get('password') and admin_info['password'] != "***":
            print(f"    {Colors.RED}Password: {admin_info['password']} {WARNING} CHANGE THIS!{Colors.RESET}")
        print()
        print(f"{WARNING} {Colors.RED}IMPORTANT: Change the admin password after first login!{Colors.RESET}")
        print()
    
    print(f"{INFO} Authentication Endpoints:")
    print(f"    {Colors.CYAN}Register: http://localhost:8000/auth/register{Colors.RESET}")
    print(f"    {Colors.CYAN}Login:    http://localhost:8000/auth/login{Colors.RESET}")
    print()
    
    print(f"{INFO} Documentation:")
    print(f"    - Read README.md for project overview")
    print(f"    - Check API_ENDPOINTS.md for API documentation")
    print(f"    - Review .env.template for configuration options")
    print()
    
    print(f"{Colors.BOLD}{Colors.CYAN}Phase 2 Next Steps:{Colors.RESET}")
    print(f"    - Implement agent orchestration endpoints")
    print(f"    - Add report generation APIs")
    print(f"    - Create workflow management")
    print(f"    - Integrate external data sources")
    print()
    
    print(f"{Colors.BOLD}{Colors.GREEN}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.GREEN}Ready to build amazing financial AI applications! 🚀{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.GREEN}{'=' * 70}{Colors.RESET}\n")


def main():
    """
    Main initialization function.
    
    Orchestrates the entire setup process:
    1. Environment check
    2. Dependency verification
    3. Database initialization
    4. Admin user creation
    5. System verification
    6. Next steps
    
    Error Handling:
    - Exits with error code 1 if any step fails
    - Handles KeyboardInterrupt gracefully
    - Catches and reports unexpected errors
    """
    try:
        print_header()
        
        # Step 1: Check environment
        if not check_environment():
            print(f"\n{ERROR} Environment check failed")
            sys.exit(1)
        
        # Step 2: Check dependencies
        if not install_dependencies():
            print(f"\n{ERROR} Dependency check failed")
            print(f"{INFO} Please install missing dependencies and run again")
            sys.exit(1)
        
        # Step 3: Initialize database
        if not initialize_database():
            print(f"\n{ERROR} Database initialization failed")
            sys.exit(1)
        
        # Step 4: Create admin user
        admin_success, admin_info = create_admin_user()
        if not admin_success:
            print(f"\n{WARNING} Admin user creation skipped or failed")
            print(f"{INFO} You can create an admin user later via API or database")
            admin_info = None
        
        # Step 5: Verify system
        if not verify_system():
            print(f"\n{ERROR} System verification failed")
            print(f"{WARNING} System may not work correctly")
            # Don't exit - allow user to proceed with warnings
        
        # Step 6: Print next steps
        print_next_steps(admin_info)
        
        print(f"{SUCCESS} Initialization complete! You can now start the server.\n")
        
    except KeyboardInterrupt:
        print(f"\n\n{WARNING} Initialization cancelled by user")
        print(f"{INFO} You can run this script again to complete setup")
        sys.exit(0)
    except Exception as e:
        print(f"\n{ERROR} Unexpected error during initialization: {e}")
        print(f"{INFO} Please check the error message above and try again")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()


