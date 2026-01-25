"""
BhashaAI Backend - Role Model

SQLAlchemy model for the roles table.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any, List, Optional

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class Role(Base):
    """
    User role model with permissions.
    
    Defines system roles like super_admin, teacher, student, etc.
    Permissions are stored as JSONB for flexible permission checks.
    
    Attributes:
        id: UUID primary key
        name: Unique role identifier (e.g., 'teacher')
        display_name: Human-readable name in English
        display_name_gujarati: Human-readable name in Gujarati
        permissions: JSON object with permission flags
        is_system_role: True for built-in roles (cannot be deleted)
        created_at: Creation timestamp
    
    Default Roles:
        - super_admin: Full system access
        - institution_admin: Manage institution users and content
        - teacher: Create papers, check papers, create materials
        - student: Solve assignments, use help mode, learn Gujarati
        - parent: View student progress
    """
    
    __tablename__ = "roles"
    
    # Primary key
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.uuid_generate_v4(),
        nullable=False,
    )
    
    # Role info
    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        comment="Role identifier (e.g., teacher, student)"
    )
    display_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Display name in English"
    )
    display_name_gujarati: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Display name in Gujarati"
    )
    
    # Permissions as JSONB
    permissions: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
        comment="JSON object with permission flags"
    )
    
    # System role flag
    is_system_role: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="True for built-in roles"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    # Relationships
    users: Mapped[List["User"]] = relationship(
        "User",
        back_populates="role",
        lazy="selectin"
    )
    
    def has_permission(self, permission: str) -> bool:
        """
        Check if role has a specific permission.
        
        Args:
            permission: Permission string to check (e.g., 'create_papers')
        
        Returns:
            bool: True if role has the permission
        """
        # Super admin has all permissions
        if self.permissions.get("all"):
            return True
        return self.permissions.get(permission, False)
    
    def __repr__(self) -> str:
        return f"<Role(name={self.name}, is_system={self.is_system_role})>"
