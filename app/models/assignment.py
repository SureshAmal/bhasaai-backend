"""
BhashaAI Backend - Assignment Models

SQLAlchemy models for assignment management, solutions, and help sessions.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import (
    AssignmentMode,
    DifficultyLevel,
    InputType,
    ProcessingStatus,
)

if TYPE_CHECKING:
    from app.models.user import User


class Assignment(Base):
    """
    Assignment model.
    
    Represents a student's submission for solving or help.
    
    Attributes:
        id: UUID primary key
        user_id: Student submitting the assignment
        question_text: Extracted or entered question text
        question_image_url: URL if image input
        input_type: text, image, pdf
        subject: Subject classification
        grade_level: Target grade
        mode: solve or help
        status: status of processing (pending, completed, etc)
        language: Language of the content (gu, en)
        extra_metadata: Additional metadata
        is_active: Soft delete flag
    """
    
    __tablename__ = "assignments"
    
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
        comment="Student ID"
    )
    
    # Content
    question_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Question content"
    )
    question_image_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="URL if image input"
    )
    input_type: Mapped[InputType] = mapped_column(
        Enum(InputType, name="input_type"),
        nullable=False,
        default=InputType.TEXT,
    )
    subject: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Subject classification"
    )
    grade_level: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )
    
    # Configuration
    mode: Mapped[AssignmentMode] = mapped_column(
        Enum(AssignmentMode, name="assignment_mode"),
        nullable=False,
        default=AssignmentMode.SOLVE,
        comment="solve or help"
    )
    status: Mapped[ProcessingStatus] = mapped_column(
        Enum(ProcessingStatus, name="processing_status"),
        nullable=False,
        default=ProcessingStatus.PENDING,
    )
    language: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="gu",
        comment="gu, en, gu-en"
    )
    
    # Metadata
    extra_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
        comment="Additional metadata"
    )
    
    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True
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
    solution: Mapped[Optional["AssignmentSolution"]] = relationship(
        "AssignmentSolution",
        back_populates="assignment",
        uselist=False,
        lazy="selectin",
        cascade="all, delete-orphan"
    )
    help_session: Mapped[Optional["HelpSession"]] = relationship(
        "HelpSession",
        back_populates="assignment",
        uselist=False,
        lazy="selectin",
        cascade="all, delete-orphan"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_assignments_user", "user_id"),
        Index("idx_assignments_created", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<Assignment(id={self.id}, subject={self.subject}, mode={self.mode})>"


class AssignmentSolution(Base):
    """
    Assignment Solution model.
    
    Stores the AI-generated solution for 'solve' mode.
    """
    
    __tablename__ = "assignment_solutions"
    
    # Primary key
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.uuid_generate_v4(),
        nullable=False,
    )
    
    # Foreign key
    assignment_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assignments.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    
    # Solution Content
    steps: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        comment="Ordered list of solution steps"
    )
    final_answer: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Final answer text"
    )
    explanation: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Overall explanation"
    )
    difficulty: Mapped[DifficultyLevel] = mapped_column(
        Enum(DifficultyLevel, name="difficulty_level"),
        nullable=False,
        default=DifficultyLevel.MEDIUM,
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    # Relationship
    assignment: Mapped["Assignment"] = relationship(
        "Assignment",
        back_populates="solution"
    )
    
    def __repr__(self) -> str:
        return f"<AssignmentSolution(id={self.id}, assignment_id={self.assignment_id})>"


class HelpSession(Base):
    """
    Help Session model.
    
    Stores state for Socratic help mode sessions.
    """
    
    __tablename__ = "help_sessions"
    
    # Primary key
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.uuid_generate_v4(),
        nullable=False,
    )
    
    # Foreign key
    assignment_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assignments.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    
    # State
    current_hint_level: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Current hint level (0-5)"
    )
    is_completed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    
    # History
    interactions: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default="[]",
        comment="History of interactions (question, hint, response)"
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
    
    # Relationship
    assignment: Mapped["Assignment"] = relationship(
        "Assignment",
        back_populates="help_session"
    )
    
    def __repr__(self) -> str:
        return f"<HelpSession(id={self.id}, level={self.current_hint_level})>"
