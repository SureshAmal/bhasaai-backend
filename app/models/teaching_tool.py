"""
BhashaAI Backend - Teaching Tool Models

SQLAlchemy models for teaching tools like mind maps, lesson plans, and analogies.
"""

from datetime import datetime
import enum
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
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


class ToolType(str, enum.Enum):
    """Types of teaching tools."""
    MIND_MAP = "mind_map"
    LESSON_PLAN = "lesson_plan"
    ANALOGY = "analogy"


class TeachingTool(Base):
    """
    Teaching Tool model.
    
    Stores generated content for various teaching aids.
    
    Attributes:
        id: UUID primary key
        user_id: Creator ID
        tool_type: Type of tool (mind_map, lesson_plan, etc)
        topic: Main topic
        subject: Subject context
        grade_level: Target grade
        content: JSON content structure (specific to tool type)
        language: Content language
        is_public: Sharing flag
        extra_metadata: Additional metadata
    """
    
    __tablename__ = "teaching_tools"
    
    # Primary key
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.uuid_generate_v4(),
        nullable=False,
    )
    
    # Foreign keys
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="Creator ID"
    )
    
    # Classification
    tool_type: Mapped[ToolType] = mapped_column(
        Enum(ToolType, name="tool_type"),
        nullable=False,
    )
    topic: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    subject: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    grade_level: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )
    
    # Content
    content: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        comment="Tool specific content structure"
    )
    language: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="en",
        comment="gu, en, gu-en"
    )
    
    # Flags
    is_public: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Allow sharing"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True
    )
    
    # Metadata
    extra_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
    )
    
    # Timestamps
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
    
    # Relationships
    user: Mapped["User"] = relationship("User", lazy="selectin")
    
    # Indexes
    __table_args__ = (
        Index("idx_tools_user", "user_id"),
        Index("idx_tools_type", "tool_type"),
        Index("idx_tools_created", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<TeachingTool(id={self.id}, type={self.tool_type}, topic={self.topic})>"
