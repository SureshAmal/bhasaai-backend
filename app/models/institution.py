"""
BhashaAI Backend - Institution Model

SQLAlchemy model for the institutions table.
"""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, Enum, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin, TimestampMixin
from app.models.enums import InstitutionType, SubscriptionPlan

if TYPE_CHECKING:
    from app.models.user import User


class Institution(Base, UUIDMixin, TimestampMixin):
    """
    Educational institution model.
    
    Represents schools, colleges, coaching centers registered on the platform.
    
    Attributes:
        id: UUID primary key
        name: Institution name in English
        name_gujarati: Institution name in Gujarati
        type: Type of institution (school, college, coaching, self)
        address: Full address
        city: City name
        state: State name (default: Gujarat)
        pincode: Postal code
        phone: Contact number
        email: Contact email
        logo_url: Logo image URL (MinIO)
        is_active: Whether institution is active
        subscription_plan: Current subscription plan
        subscription_expires_at: When subscription expires
    """
    
    __tablename__ = "institutions"
    
    # Basic info
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Institution name in English"
    )
    name_gujarati: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Institution name in Gujarati"
    )
    type: Mapped[InstitutionType] = mapped_column(
        Enum(InstitutionType, name="institution_type", create_type=True),
        nullable=False,
        comment="school, college, coaching, self"
    )
    
    # Address
    address: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    city: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    state: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="Gujarat"
    )
    pincode: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True
    )
    
    # Contact
    phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    logo_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="MinIO logo URL"
    )
    
    # Status & Subscription
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True
    )
    subscription_plan: Mapped[SubscriptionPlan] = mapped_column(
        Enum(SubscriptionPlan, name="subscription_plan", create_type=True),
        nullable=False,
        default=SubscriptionPlan.FREE
    )
    subscription_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Relationships
    users: Mapped[List["User"]] = relationship(
        "User",
        back_populates="institution",
        lazy="selectin"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_institutions_type", "type"),
        Index("idx_institutions_city", "city"),
        Index("idx_institutions_active", "is_active"),
    )
    
    def is_subscription_active(self) -> bool:
        """Check if subscription is currently active."""
        if self.subscription_plan == SubscriptionPlan.FREE:
            return True
        if self.subscription_expires_at is None:
            return False
        return datetime.now() < self.subscription_expires_at
