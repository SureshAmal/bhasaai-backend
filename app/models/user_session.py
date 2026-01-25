"""
BhashaAI Backend - User Session Model

SQLAlchemy model for the user_sessions table.
Handles JWT refresh tokens and session tracking.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class UserSession(Base):
    """
    User session model for JWT refresh tokens.
    
    Tracks active sessions and allows multiple devices per user.
    Refresh tokens are rotated on each use for security.
    
    Attributes:
        id: UUID primary key
        user_id: FK to user
        refresh_token: JWT refresh token
        device_info: Device/browser info as JSON
        ip_address: Client IP (IPv4/IPv6)
        user_agent: Browser user agent string
        is_active: Session valid status
        expires_at: Token expiration time
        last_activity_at: Last activity timestamp
        created_at: Session creation time
    """
    
    __tablename__ = "user_sessions"
    
    # Primary key
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.uuid_generate_v4(),
        nullable=False,
    )
    
    # Foreign key
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="Session owner"
    )
    
    # Token
    refresh_token: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        index=True,
        comment="JWT refresh token"
    )
    
    # Device tracking
    device_info: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
        comment="Device/browser info"
    )
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
        comment="Client IP (IPv4/IPv6)"
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Browser user agent"
    )
    
    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Token expiration time"
    )
    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="sessions",
        lazy="selectin"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_user_sessions_user", "user_id"),
        Index("idx_user_sessions_active", "is_active"),
        Index("idx_user_sessions_expires", "expires_at"),
    )
    
    def is_valid(self) -> bool:
        """
        Check if session is still valid.
        
        Returns:
            bool: True if session is active and not expired
        """
        if not self.is_active:
            return False
        return datetime.now(self.expires_at.tzinfo) < self.expires_at
    
    def invalidate(self) -> None:
        """Invalidate this session."""
        self.is_active = False
    
    def __repr__(self) -> str:
        return f"<UserSession(user_id={self.user_id}, active={self.is_active})>"
