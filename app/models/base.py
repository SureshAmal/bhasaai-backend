"""
BhashaAI Backend - SQLAlchemy Base Model

Provides the declarative base and common mixins for all models.
"""

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models.
    
    Provides common functionality for all database models.
    """
    
    def to_dict(self) -> dict[str, Any]:
        """
        Convert model instance to dictionary.
        
        Returns:
            dict: Model attributes as dictionary
        """
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            # Handle UUID serialization
            if hasattr(value, 'hex'):
                value = str(value)
            # Handle datetime serialization
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result
    
    def __repr__(self) -> str:
        """String representation of the model."""
        class_name = self.__class__.__name__
        pk = getattr(self, 'id', None)
        return f"<{class_name}(id={pk})>"


class UUIDMixin:
    """
    Mixin that adds a UUID primary key.
    
    Uses PostgreSQL's uuid_generate_v4() for server-side generation.
    """
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=func.uuid_generate_v4(),
        nullable=False,
    )


class TimestampMixin:
    """
    Mixin that adds created_at and updated_at timestamps.
    
    Automatically sets timestamps on insert and update.
    """
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class BaseModel(Base, UUIDMixin, TimestampMixin):
    """
    Abstract base model with UUID and timestamps.
    
    Inherit from this for models that need both UUID pk and timestamps.
    """
    
    __abstract__ = True
