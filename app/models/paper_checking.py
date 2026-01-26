"""
BhashaAI Backend - Paper Checking Models

SQLAlchemy models for automated paper checking, including:
- AnswerKey: Rubric and expected answers
- Submission: Student answer sheets (images/PDFs)
- GradedAnswer: Individual question results
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any, List, Optional
import enum

from sqlalchemy import (
    DateTime,
    Enum,
    Float,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.question_paper import QuestionPaper


class SubmissionStatus(str, enum.Enum):
    """Status of a paper submission."""
    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    OCR_PROCESSING = "ocr_processing"
    GRADING = "grading"
    COMPLETED = "completed"
    FAILED = "failed"


class AnswerKey(Base):
    """
    Answer Key (Rubric) for a Question Paper.
    
    Defines the standard for grading, including keywords and partial marking rules.
    """
    __tablename__ = "answer_keys"
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.uuid_generate_v4(),
        nullable=False,
    )
    
    question_paper_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("question_papers.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    
    # JSON Structure:
    # {
    #   "question_id": {
    #     "expected_answer": "...",
    #     "keywords": ["k1", "k2"],
    #     "max_marks": 5,
    #     "partial_marking": true
    #   }
    # }
    content: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        comment="Map of question_id to grading criteria"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    # Relationships
    question_paper: Mapped["QuestionPaper"] = relationship("QuestionPaper")


class Submission(Base):
    """
    Student Answer Sheet Submission.
    
    Represents usage of the 'Paper Checking' feature.
    Can be a specific QuestionPaper or a generic submission.
    """
    __tablename__ = "submissions"
    
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
    
    # Optional link to a generated paper
    question_paper_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("question_papers.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    status: Mapped[SubmissionStatus] = mapped_column(
        Enum(SubmissionStatus, name="submission_status"),
        nullable=False,
        default=SubmissionStatus.UPLOADING,
    )
    
    # File Info
    input_file_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="URL of the uploaded answer sheet (PDF/Image)"
    )
    student_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Extracted or provided student name"
    )
    
    # Results
    extracted_text: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        comment="Raw text content from OCR"
    )
    overall_score: Mapped[float] = mapped_column(
        Float,
        nullable=True,
        default=0.0
    )
    max_score: Mapped[float] = mapped_column(
        Float,
        nullable=True,
        default=0.0
    )
    summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Overall performace summary"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    # Relationships
    answers: Mapped[List["GradedAnswer"]] = relationship(
        "GradedAnswer",
        back_populates="submission",
        cascade="all, delete-orphan",
        lazy="selectin"
    )


class GradedAnswer(Base):
    """
    Individual Graded Answer.
    """
    __tablename__ = "graded_answers"
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.uuid_generate_v4(),
        nullable=False,
    )
    
    submission_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("submissions.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    question_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Content
    question_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Snapshot of question text"
    )
    student_answer_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Part of OCR text identified as this answer"
    )
    
    # Evaluation
    marks_obtained: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0
    )
    max_marks: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    feedback: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Specific feedback for this answer"
    )
    confidence_score: Mapped[float] = mapped_column(
        Float,
        nullable=True,
        comment="AI confidence in grading (0-1)"
    )
    
    # Relationships
    submission: Mapped["Submission"] = relationship(
        "Submission",
        back_populates="answers"
    )
