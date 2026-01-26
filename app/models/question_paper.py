"""
BhashaAI Backend - Question Paper Models

SQLAlchemy models for question papers and questions.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import (
    DifficultyLevel,
    PaperStatus,
    QuestionType,
)

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.institution import Institution
    from app.models.user import User


class QuestionPaper(Base):
    """
    Question paper model.
    
    Represents a generated or manually created question paper
    containing multiple questions.
    
    Attributes:
        id: UUID primary key
        user_id: Paper creator
        institution_id: Associated institution
        title: Paper title
        subject: Subject name
        grade_level: Target grade
        total_marks: Maximum marks
        duration_minutes: Exam duration
        language: Paper language
        difficulty_distribution: % by difficulty
        question_type_distribution: Count by type
        instructions: Exam instructions
        status: draft, published, archived
    """
    
    __tablename__ = "question_papers"
    
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
        comment="Paper creator"
    )
    institution_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="SET NULL"),
        nullable=True,
    )
    document_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
        comment="Source document (if RAG generated)"
    )
    
    # Paper details
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Paper title"
    )
    title_gujarati: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Title in Gujarati"
    )
    subject: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Subject name"
    )
    grade_level: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Target grade (e.g., 10, 12, UG)"
    )
    
    # Marks and duration
    total_marks: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=100,
        comment="Maximum marks"
    )
    duration_minutes: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Exam duration in minutes"
    )
    
    # Language
    language: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="gu",
        comment="Paper language (gu, en, gu-en)"
    )
    
    # Distribution settings
    difficulty_distribution: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default='{"easy": 30, "medium": 50, "hard": 20}',
        comment="% distribution by difficulty"
    )
    question_type_distribution: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
        comment="Count by question type"
    )
    
    # Content
    instructions: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Exam instructions"
    )
    instructions_gujarati: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Instructions in Gujarati"
    )
    
    # Status
    status: Mapped[PaperStatus] = mapped_column(
        Enum(PaperStatus, name="paper_status"),
        nullable=False,
        default=PaperStatus.DRAFT,
    )
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
    institution: Mapped[Optional["Institution"]] = relationship("Institution", lazy="selectin")
    document: Mapped[Optional["Document"]] = relationship("Document", lazy="selectin")
    questions: Mapped[list["Question"]] = relationship(
        "Question",
        back_populates="paper",
        lazy="selectin",
        order_by="Question.question_number"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_question_papers_user", "user_id"),
        Index("idx_question_papers_status", "status"),
        Index("idx_question_papers_subject", "subject"),
        Index("idx_question_papers_created", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<QuestionPaper(id={self.id}, title={self.title}, status={self.status})>"


class Question(Base):
    """
    Question model.
    
    Represents a single question within a question paper.
    
    Attributes:
        id: UUID primary key
        paper_id: Parent question paper
        question_number: Order in paper
        question_text: Question content
        question_text_gujarati: Gujarati version
        question_type: MCQ, SHORT_ANSWER, etc.
        marks: Question marks
        difficulty: easy, medium, hard
        answer: Expected answer
        options: MCQ options (for MCQ type)
        explanation: Answer explanation
        bloom_level: Bloom's taxonomy level
        topic: Related topic/chapter
    """
    
    __tablename__ = "questions"
    
    # Primary key
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.uuid_generate_v4(),
        nullable=False,
    )
    
    # Foreign key
    paper_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("question_papers.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Question details
    question_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Order in paper"
    )
    question_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Question content"
    )
    question_text_gujarati: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Gujarati version"
    )
    
    # Type and marks
    question_type: Mapped[QuestionType] = mapped_column(
        Enum(QuestionType, name="question_type"),
        nullable=False,
        default=QuestionType.SHORT_ANSWER,
    )
    marks: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=1.0,
        comment="Question marks"
    )
    difficulty: Mapped[DifficultyLevel] = mapped_column(
        Enum(DifficultyLevel, name="difficulty_level"),
        nullable=False,
        default=DifficultyLevel.MEDIUM,
    )
    
    # Answer
    answer: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Expected answer"
    )
    answer_gujarati: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Answer in Gujarati"
    )
    options: Mapped[Optional[list[str]]] = mapped_column(
        ARRAY(String),
        nullable=True,
        comment="MCQ options"
    )
    correct_option: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Correct MCQ option index (0-based)"
    )
    
    # Metadata
    explanation: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Answer explanation"
    )
    bloom_level: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Bloom's taxonomy level"
    )
    topic: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Related topic/chapter"
    )
    keywords: Mapped[Optional[list[str]]] = mapped_column(
        ARRAY(String),
        nullable=True,
        comment="Answer keywords for matching"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    # Relationship
    paper: Mapped["QuestionPaper"] = relationship(
        "QuestionPaper",
        back_populates="questions"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_questions_paper", "paper_id"),
        Index("idx_questions_type", "question_type"),
        Index("idx_questions_difficulty", "difficulty"),
    )
    
    def __repr__(self) -> str:
        return f"<Question(id={self.id}, number={self.question_number}, type={self.question_type})>"
