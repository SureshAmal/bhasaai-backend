"""
BhashaAI Backend - Worksheet Models

SQLAlchemy models for gamified worksheets.
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
from app.models.enums import DifficultyLevel

if TYPE_CHECKING:
    from app.models.user import User

import enum

class WorksheetStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

class AttemptStatus(str, enum.Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"

class Worksheet(Base):
    """
    Worksheet model.
    
    Represents a gamified worksheet with step-by-step problems.
    """
    
    __tablename__ = "worksheets"
    
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
        comment="Creator"
    )
    
    # Content
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    topic: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(100), nullable=False)
    grade_level: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    difficulty: Mapped[DifficultyLevel] = mapped_column(
        Enum(DifficultyLevel, name="difficulty_level"),
        nullable=False,
        default=DifficultyLevel.MEDIUM,
    )
    
    status: Mapped[WorksheetStatus] = mapped_column(
        Enum(WorksheetStatus, name="worksheet_status"),
        nullable=False,
        default=WorksheetStatus.DRAFT,
    )
    
    # Metadata
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
    questions: Mapped[list["WorksheetQuestion"]] = relationship(
        "WorksheetQuestion",
        back_populates="worksheet",
        lazy="selectin",
        order_by="WorksheetQuestion.order"
    )

class WorksheetQuestion(Base):
    """
    Question within a worksheet.
    Contains detailed steps for solving.
    """
    
    __tablename__ = "worksheet_questions"
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.uuid_generate_v4(),
        nullable=False,
    )
    
    worksheet_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("worksheets.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    content: Mapped[str] = mapped_column(Text, nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Steps stored as JSON list:
    # [{ "step_text": "...", "answer_key": "...", "hint": "..." }]
    steps: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        default=list
    )
    
    correct_answer: Mapped[str] = mapped_column(Text, nullable=False)
    
    worksheet: Mapped["Worksheet"] = relationship("Worksheet", back_populates="questions")

class WorksheetAttempt(Base):
    """
    User's attempt at solving a worksheet.
    Tracks progress through questions and steps.
    """
    
    __tablename__ = "worksheet_attempts"
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.uuid_generate_v4(),
        nullable=False,
    )
    
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    worksheet_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("worksheets.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Progress
    current_question_index: Mapped[int] = mapped_column(Integer, default=0)
    current_step_index: Mapped[int] = mapped_column(Integer, default=0)
    score: Mapped[int] = mapped_column(Integer, default=0)
    
    status: Mapped[AttemptStatus] = mapped_column(
        Enum(AttemptStatus, name="attempt_status"),
        nullable=False,
        default=AttemptStatus.IN_PROGRESS,
    )
    
    # Detailed log of answers: { question_id: { step_index: "user_answer" } }
    progress_data: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

