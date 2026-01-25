"""
BhashaAI Backend - Schemas Package

Exports all Pydantic schemas.
"""

from app.schemas.institution import (
    InstitutionCreate,
    InstitutionResponse,
    InstitutionUpdate,
)
from app.schemas.response import APIResponse
from app.schemas.user import (
    AuthResponse,
    PasswordChange,
    RoleResponse,
    TokenRefresh,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
)

__all__ = [
    # Response
    "APIResponse",
    # User/Auth
    "UserCreate",
    "UserLogin",
    "UserUpdate",
    "UserResponse",
    "TokenResponse",
    "TokenRefresh",
    "AuthResponse",
    "PasswordChange",
    "RoleResponse",
    # Institution
    "InstitutionCreate",
    "InstitutionUpdate",
    "InstitutionResponse",
]
