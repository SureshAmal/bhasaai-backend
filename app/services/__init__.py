"""
BhashaAI Backend - Services Package

Exports all business logic services.
"""

from app.services.auth_service import AuthService

__all__ = [
    "AuthService",
]
