"""
BhashaAI Backend - Institution Schemas

Pydantic schemas for institution-related operations.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import InstitutionType, SubscriptionPlan


class InstitutionCreate(BaseModel):
    """
    Schema for creating an institution.
    """
    
    name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Institution name in English"
    )
    name_gujarati: Optional[str] = Field(
        None,
        max_length=255,
        description="Institution name in Gujarati"
    )
    type: InstitutionType = Field(
        ...,
        description="Type of institution"
    )
    address: Optional[str] = Field(None, description="Full address")
    city: Optional[str] = Field(None, max_length=100)
    state: str = Field(default="Gujarat", max_length=100)
    pincode: Optional[str] = Field(None, max_length=10)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = Field(None)


class InstitutionUpdate(BaseModel):
    """
    Schema for updating an institution.
    All fields optional.
    """
    
    name: Optional[str] = Field(None, max_length=255)
    name_gujarati: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    pincode: Optional[str] = Field(None, max_length=10)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    logo_url: Optional[str] = Field(None, max_length=500)


class InstitutionResponse(BaseModel):
    """
    Institution response schema.
    """
    
    id: UUID
    name: str
    name_gujarati: Optional[str] = None
    type: InstitutionType
    address: Optional[str] = None
    city: Optional[str] = None
    state: str
    pincode: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    logo_url: Optional[str] = None
    is_active: bool
    subscription_plan: SubscriptionPlan
    subscription_expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}
