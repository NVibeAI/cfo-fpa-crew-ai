"""
Main FastAPI Application

This is the entry point for the FP&A CFO Crew AI backend API.
It sets up the FastAPI application, configures middleware, registers routers,
and handles startup/shutdown events.

Why FastAPI?
============
FastAPI was chosen for this project because:
1. High Performance: One of the fastest Python frameworks (comparable to Node.js)
2. Automatic API Documentation: Generates OpenAPI/Swagger docs automatically
3. Type Safety: Built on Pydantic for request/response validation
4. Modern Python: Uses Python 3.6+ type hints
5. Easy to Use: Simple, intuitive API design
6. Production Ready: Used by major companies (Uber, Netflix, etc.)
7. Async Support: Native async/await support for high concurrency
8. Standards Based: Based on OpenAPI, JSON Schema, OAuth2

CORS (Cross-Origin Resource Sharing):
======================================
CORS is a security feature that controls which websites can make requests
to your API from a browser. When your frontend (Streamlit, React) runs on
a different origin (protocol + domain + port) than your API, the browser
blocks requests unless CORS is properly configured.

Example:
- API: http://localhost:8000
- Frontend: http://localhost:8501 (Streamlit)
- Browser blocks requests unless CORS allows localhost:8501

In production, restrict CORS to specific domains for security:
- Development: Allow localhost origins
- Production: Only allow your actual frontend domain (e.g., https://app.example.com)
"""

import os
import logging
from typing import Dict, Any

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from backend.core.database import check_connection, init_db, get_database_info
from backend.api import auth

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# FASTAPI APPLICATION INSTANCE
# ============================================================================

# Create FastAPI application with metadata
# This metadata appears in:
# - Swagger UI (/docs)
# - ReDoc (/redoc)
# - OpenAPI schema (/openapi.json)
app = FastAPI(
    title="FP&A CFO Crew AI API",
    description="""
    Backend API for AI-powered Financial Planning & Analysis.
    
    This API provides:
    - User authentication and authorization
    - AI agent orchestration
    - Financial data analysis
    - Report generation
    - What-if scenario modeling
    
    ## Authentication
    
    Most endpoints require authentication. Use the `/auth/login` endpoint
    to obtain JWT tokens, then include them in the Authorization header:
    
    ```
    Authorization: Bearer <access_token>
    ```
    
    ## Documentation
    
    - **Swagger UI**: Interactive API documentation at `/docs`
    - **ReDoc**: Alternative documentation at `/redoc`
    - **OpenAPI Schema**: Machine-readable schema at `/openapi.json`
    """,
    version="1.0.0",
    docs_url="/docs",  # Swagger UI endpoint
    redoc_url="/redoc",  # ReDoc endpoint
    openapi_url="/openapi.json"  # OpenAPI schema endpoint
)


# ============================================================================
# CORS CONFIGURATION
# ============================================================================

# CORS (Cross-Origin Resource Sharing) allows browsers to make requests
# from one origin (frontend) to another (API). This is essential for
# web applications where frontend and backend run on different ports/domains.

# Get allowed origins from environment or use defaults
# In production, set CORS_ORIGINS environment variable to restrict origins
cors_origins_env = os.getenv("CORS_ORIGINS", "")
if cors_origins_env:
    # Parse comma-separated origins from environment
    allowed_origins = [origin.strip() for origin in cors_origins_env.split(",")]
else:
    # Default origins for development
    allowed_origins = [
        "http://localhost:8501",  # Streamlit default port
        "http://localhost:3000",  # React default port
        "http://localhost:8000",  # API itself
        "http://127.0.0.1:8501",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ]

# Add CORS middleware
# This must be added before other middleware and routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # List of allowed origins
    allow_credentials=True,  # Allow cookies and authentication headers
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Production CORS Security Note:
# =============================
# In production, restrict CORS to specific domains:
#   allow_origins=["https://app.example.com", "https://dashboard.example.com"]
# This prevents unauthorized websites from making requests to your API.
# Never use ["*"] in production!


# ============================================================================
# STARTUP AND SHUTDOWN EVENTS
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """
    Execute startup tasks when the application starts.
    
    Startup events are useful for:
    - Database initialization
    - Connection pool setup
    - Loading configuration
    - Pre-warming caches
    - Health checks
    
    This runs once when the server starts, before handling any requests.
    """
    logger.info("=" * 70)
    logger.info("Starting FP&A CFO Crew AI API Server")
    logger.info("=" * 70)
    
    try:
        # Check database connection
        logger.info("Checking database connection...")
        if check_connection():
            logger.info("✓ Database connection: SUCCESS")
            
            # Display database information
            db_info = get_database_info()
            logger.info(f"  Database Type: {db_info['database_type']}")
            logger.info(f"  Pool Size: {db_info['pool_size']}")
        else:
            logger.error("✗ Database connection: FAILED")
            logger.warning("Server will start but database operations may fail")
        
        # Initialize database tables
        logger.info("Initializing database tables...")
        init_db()
        logger.info("✓ Database tables initialized")
        
        logger.info("=" * 70)
        logger.info("Server startup completed successfully!")
        logger.info("=" * 70)
        logger.info("")
        logger.info("API Documentation:")
        logger.info("  - Swagger UI: http://localhost:8000/docs")
        logger.info("  - ReDoc: http://localhost:8000/redoc")
        logger.info("  - OpenAPI Schema: http://localhost:8000/openapi.json")
        logger.info("")
        
    except Exception as e:
        logger.error(f"Startup error: {e}")
        logger.warning("Server will continue but some features may not work")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Execute cleanup tasks when the application shuts down.
    
    Shutdown events are useful for:
    - Closing database connections
    - Saving state
    - Cleaning up resources
    - Sending notifications
    
    This runs once when the server is shutting down, after all requests complete.
    """
    logger.info("=" * 70)
    logger.info("Shutting down FP&A CFO Crew AI API Server")
    logger.info("=" * 70)
    
    # Database connections are automatically closed by SQLAlchemy
    # Add any additional cleanup here (close file handles, etc.)
    
    logger.info("Server shutdown complete")


# ============================================================================
# ROUTER REGISTRATION
# ============================================================================

# Register API routers
# Routers organize endpoints into logical groups
# Each router can have its own prefix, tags, and dependencies

# Authentication router
# Handles: registration, login, token refresh, user profile, admin operations
app.include_router(auth.router)

# Future routers (to be implemented):
# ===================================
# from backend.api import agents
# app.include_router(agents.router, prefix="/api/v1")
#
# from backend.api import reports
# app.include_router(reports.router, prefix="/api/v1")
#
# from backend.api import tools
# app.include_router(tools.router, prefix="/api/v1")
#
# from backend.api import workflows
# app.include_router(workflows.router, prefix="/api/v1")


# ============================================================================
# ROOT ENDPOINTS
# ============================================================================

@app.get("/", tags=["root"])
async def root() -> Dict[str, Any]:
    """
    Root endpoint - API information and metadata.
    
    Returns basic information about the API, including:
    - API name and version
    - Status
    - Documentation URLs
    - Available endpoints
    
    This is useful for:
    - API discovery
    - Health monitoring
    - Quick status checks
    """
    return {
        "name": "FP&A CFO Crew AI API",
        "version": "1.0.0",
        "status": "running",
        "description": "Backend API for AI-powered Financial Planning & Analysis",
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_schema": "/openapi.json"
        },
        "endpoints": {
            "authentication": "/auth",
            "health": "/health",
            "root": "/"
        },
        "message": "Welcome to FP&A CFO Crew AI API. Visit /docs for interactive documentation."
    }


@app.get("/health", tags=["health"])
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint for monitoring and load balancers.
    
    Health checks are critical for:
    - Load balancers: Determine if server is healthy
    - Monitoring systems: Alert on failures
    - Kubernetes: Liveness and readiness probes
    - CI/CD pipelines: Verify deployment success
    
    Returns:
    - 200 OK: Server is healthy
    - 503 Service Unavailable: Server is unhealthy
    
    The endpoint checks:
    - Database connectivity
    - Server responsiveness
    
    In production, you may want to add more checks:
    - Redis connectivity
    - External API availability
    - Disk space
    - Memory usage
    """
    health_status = {
        "status": "healthy",
        "database": "connected",
        "timestamp": None
    }
    
    # Check database connection
    db_healthy = check_connection()
    
    if not db_healthy:
        health_status["status"] = "unhealthy"
        health_status["database"] = "disconnected"
        
        # Return 503 Service Unavailable if unhealthy
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=health_status
        )
    
    # Import datetime here to avoid circular imports
    from datetime import datetime
    health_status["timestamp"] = datetime.utcnow().isoformat()
    
    return health_status


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """
    Custom 404 Not Found handler.
    
    Provides a more informative error message when a route is not found.
    This is useful for API consumers to understand what went wrong.
    """
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": "Not Found",
            "message": f"The requested endpoint '{request.url.path}' was not found.",
            "path": request.url.path,
            "method": request.method,
            "suggestion": "Check the API documentation at /docs for available endpoints."
        }
    )


@app.exception_handler(500)
async def internal_server_error_handler(request: Request, exc):
    """
    Custom 500 Internal Server Error handler.
    
    Provides error information while protecting sensitive details.
    In production, don't expose stack traces or internal errors to clients.
    """
    logger.error(f"Internal server error: {exc}", exc_info=True)
    
    # In development, show more details
    # In production, show generic message
    debug_mode = os.getenv("DEBUG", "false").lower() == "true"
    
    error_response = {
        "error": "Internal Server Error",
        "message": "An unexpected error occurred. Please try again later.",
        "path": request.url.path,
        "method": request.method
    }
    
    # Only include detailed error in debug mode
    if debug_mode:
        error_response["detail"] = str(exc)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    """
    Custom validation error handler.
    
    Provides detailed validation error messages for Pydantic validation failures.
    This helps API consumers understand what's wrong with their request.
    """
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "message": "Request validation failed. Please check your input.",
            "details": exc.errors(),
            "path": request.url.path
        }
    )


# ============================================================================
# MAIN EXECUTION BLOCK
# ============================================================================

if __name__ == "__main__":
    """
    Run the FastAPI application using Uvicorn.
    
    This block executes when running the file directly:
        python -m backend.main
    
    Uvicorn is an ASGI server that runs FastAPI applications.
    It provides:
    - High performance async server
    - Hot reload for development
    - Production-ready features
    
    Configuration:
    - host="0.0.0.0": Listen on all network interfaces (accessible from other machines)
    - port=8000: Default API port
    - reload=True: Auto-reload on code changes (development only)
    - log_level="info": Logging verbosity
    
    For production, use:
    - reload=False (disable auto-reload)
    - workers=4 (multiple worker processes)
    - Use a process manager (systemd, supervisor, etc.)
    """
    import uvicorn
    
    # Get configuration from environment or use defaults
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    reload = os.getenv("ENVIRONMENT", "development") == "development"
    
    print("=" * 70)
    print("FP&A CFO Crew AI API Server")
    print("=" * 70)
    print(f"Starting server on http://{host}:{port}")
    print(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"Reload: {reload}")
    print("")
    print("API Endpoints:")
    print(f"  - API: http://{host}:{port}")
    print(f"  - Swagger UI: http://{host}:{port}/docs")
    print(f"  - ReDoc: http://{host}:{port}/redoc")
    print(f"  - Health Check: http://{host}:{port}/health")
    print("")
    print("Authentication:")
    print(f"  - Register: http://{host}:{port}/auth/register")
    print(f"  - Login: http://{host}:{port}/auth/login")
    print("")
    print("Press CTRL+C to stop the server")
    print("=" * 70)
    print("")
    
    # Run the server
    uvicorn.run(
        "backend.main:app",  # Module path to FastAPI app
        host=host,
        port=port,
        reload=reload,  # Auto-reload on code changes (development)
        log_level="info"
    )


