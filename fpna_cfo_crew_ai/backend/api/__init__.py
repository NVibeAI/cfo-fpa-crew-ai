"""
API endpoints for the application.
"""

from . import auth
from .auth import router as auth_router

__all__ = ['auth', 'auth_router']

