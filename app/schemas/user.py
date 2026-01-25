"""
BhashaAI Backend - User Schemas

Pydantic schemas for user-related operations.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.enums import LanguagePreference


# =============================================================================
# Request Schemas
# =============================================================================


class UserCreate(BaseModel):
    """
    Schema for user registration.
    
    Attributes:
        email: Valid email address
        password: Password (min 8 chars)
        full_name: User's full name
        full_name_gujarati: Name in Gujarati (optional)
        phone: Phone number (optional)
        language_preference: Preferred language (default: Gujarati)
        grade_level: For students (optional)
        institution_id: Associated institution (optional)
    """
    
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="Password (min 8 characters)"
    )
    full_name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Full name in English"
    )
    full_name_gujarati: Optional[str] = Field(
        None,
        max_length=255,
        description="Full name in Gujarati"
    )
    phone: Optional[str] = Field(
        None,
        max_length=20,
        description="Phone number"
    )
    language_preference: LanguagePreference = Field(
        default=LanguagePreference.GUJARATI,
        description="Preferred language for AI responses"
    )
    grade_level: Optional[str] = Field(
        None,
        max_length=20,
        description="Student's grade level"
    )
    institution_id: Optional[UUID] = Field(
        None,
        description="Associated institution ID"
    )
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserLogin(BaseModel):
    """
    Schema for user login.
    
    Attributes:
        email: User's email address
        password: User's password
    """
    
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., description="Password")


class UserUpdate(BaseModel):
    """
    Schema for updating user profile.
    
    All fields are optional - only provided fields will be updated.
    """
    
    full_name: Optional[str] = Field(None, max_length=255)
    full_name_gujarati: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    language_preference: Optional[LanguagePreference] = None
    grade_level: Optional[str] = Field(None, max_length=20)
    profile_image_url: Optional[str] = Field(None, max_length=500)


class PasswordChange(BaseModel):
    """Schema for password change."""
    
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="New password"
    )
    
    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Validate new password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class TokenRefresh(BaseModel):
    """Schema for token refresh request."""
    
    refresh_token: str = Field(..., description="JWT refresh token")


# =============================================================================
# Response Schemas
# =============================================================================


class RoleResponse(BaseModel):
    """Role information in responses."""
    
    id: UUID
    name: str
    display_name: Optional[str] = None
    display_name_gujarati: Optional[str] = None
    permissions: dict[str, Any] = Field(default_factory=dict)
    
    model_config = {"from_attributes": True}


class InstitutionBrief(BaseModel):
    """Brief institution info for user responses."""
    
    id: UUID
    name: str
    name_gujarati: Optional[str] = None
    type: str
    
    model_config = {"from_attributes": True}


class UserResponse(BaseModel):
    """
    User response schema.
    
    Used for returning user data in API responses.
    """
    
    id: UUID
    email: str
    full_name: str
    full_name_gujarati: Optional[str] = None
    phone: Optional[str] = None
    profile_image_url: Optional[str] = None
    language_preference: LanguagePreference
    grade_level: Optional[str] = None
    subjects: Optional[list[str]] = None
    is_active: bool
    is_email_verified: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime
    
    # Related data
    role: Optional[RoleResponse] = None
    institution: Optional[InstitutionBrief] = None
    
    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """
    Token response after successful authentication.
    
    Attributes:
        access_token: JWT access token (short-lived)
        refresh_token: JWT refresh token (long-lived)
        token_type: Always "bearer"
        expires_in: Access token TTL in seconds
    """
    
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Token expiry in seconds")


class AuthResponse(BaseModel):
    """
    Response after login/registration.
    
    Includes user info and tokens.
    """
    
    user: UserResponse
    tokens: TokenResponse
