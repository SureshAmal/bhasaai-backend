"""
BhashaAI Backend - Paper Checking Models

SQLAlchemy models for automated paper checking:
- AnswerKey: Teacher's answer key with expected answers, keywords, and marking scheme
- CheckedPaper: Student answer paper with OCR extraction and AI grading results

Database Schema Reference:
    - answer_keys: Stores answer keys linked to question papers
    - checked_papers: Stores evaluated student papers with results
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any, List, Optional
import enum

from sqlalchemy import (
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.question_paper import QuestionPaper
    from app.models.user import User


class CheckedPaperStatus(str, enum.Enum):
    """Status of a checked paper in the grading workflow."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    REVIEWED = "reviewed"
    APPROVED = "approved"


class AnswerKey(Base):
    """
    Answer Key for Paper Checking.
    
    Contains expected answers, keywords, and marking scheme for grading student papers.
    Can be linked to a generated question paper or created independently.
    
    Attributes:
        id: Unique identifier (UUID)
        user_id: Teacher who created the answer key
        paper_id: Optional link to a QuestionPaper
        title: Title of the answer key
        subject: Subject (e.g., 'science', 'math')
        total_marks: Total marks for all questions
        answers: JSON array of answer objects with expected answers and keywords
        marking_scheme: JSON object with grading configuration
        created_at: Timestamp of creation
    
    JSON Structure for 'answers':
        [
            {
                "question_number": 1,
                "type": "mcq",
                "correct_answer": "B",
                "max_marks": 1
            },
            {
                "question_number": 2,
                "type": "short_answer",
                "expected_answer": "...",
                "expected_answer_gujarati": "...",
                "keywords": ["keyword1", "keyword2"],
                "max_marks": 5,
                "partial_marking": true
            }
        ]
    
    JSON Structure for 'marking_scheme':
        {
            "keyword_match_percent": 50,
            "semantic_similarity_threshold": 0.7
        }
    """
    __tablename__ = "answer_keys"
    
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
        comment="Teacher who created this answer key"
    )
    
    paper_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("question_papers.id", ondelete="SET NULL"),
        nullable=True,
        comment="Optional linked question paper"
    )
    
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Answer key title"
    )
    
    subject: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Subject (e.g., science, math)"
    )
    
    total_marks: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Total marks for all questions"
    )
    
    answers: Mapped[List[dict]] = mapped_column(
        JSONB,
        nullable=False,
        comment="Array of answer objects with keywords and variations"
    )
    
    marking_scheme: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=True,
        default={},
        comment="Marking configuration (keyword weight, semantic threshold)"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    question_paper: Mapped[Optional["QuestionPaper"]] = relationship(
        "QuestionPaper",
        foreign_keys=[paper_id]
    )
    checked_papers: Mapped[List["CheckedPaper"]] = relationship(
        "CheckedPaper",
        back_populates="answer_key",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<AnswerKey {self.id}: {self.title}>"


class CheckedPaper(Base):
    """
    Checked Student Paper.
    
    Represents a student's answer paper that has been scanned, OCR processed,
    and graded against an answer key.
    
    Attributes:
        id: Unique identifier (UUID)
        answer_key_id: Reference to the answer key used for grading
        teacher_id: Teacher who submitted this paper for checking
        student_name: Name of the student (optional)
        student_id: Student's ID/roll number (optional)
        scanned_file_path: Path to the uploaded file in storage
        extracted_text: Raw OCR extracted text
        results: JSON array of question-wise evaluation results
        total_marks: Maximum possible marks
        obtained_marks: Marks scored by student
        percentage: Score percentage
        grade: Letter grade (A, B, C, etc.)
        overall_feedback: AI-generated feedback
        overall_feedback_gujarati: Feedback in Gujarati
        status: Processing status
        reviewed_by: Teacher who reviewed (if manually reviewed)
        reviewed_at: Review timestamp
        created_at: Submission timestamp
    
    JSON Structure for 'results':
        [
            {
                "question_number": 1,
                "max_marks": 1,
                "obtained_marks": 1,
                "status": "correct",
                "student_answer": "B",
                "feedback": "Correct answer.",
                "feedback_gujarati": "સાચો જવાબ."
            },
            {
                "question_number": 2,
                "max_marks": 5,
                "obtained_marks": 4,
                "status": "partial",
                "extracted_answer": "...",
                "keyword_matches": ["photosynthesis", "sunlight"],
                "missing_keywords": ["carbon dioxide"],
                "semantic_similarity": 0.78,
                "feedback": "Good answer but missing...",
                "feedback_gujarati": "..."
            }
        ]
    """
    __tablename__ = "checked_papers"
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.uuid_generate_v4(),
        nullable=False,
    )
    
    answer_key_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("answer_keys.id", ondelete="CASCADE"),
        nullable=False,
        comment="Answer key used for grading"
    )
    
    teacher_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="Teacher who submitted this paper"
    )
    
    student_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Student's name"
    )
    
    student_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Student's ID or roll number"
    )
    
    scanned_file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Storage path for scanned paper (MinIO/S3)"
    )
    
    extracted_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="PaddleOCR extracted text from scanned paper"
    )
    
    results: Mapped[List[dict]] = mapped_column(
        JSONB,
        nullable=False,
        default=[],
        comment="Question-wise evaluation results"
    )
    
    total_marks: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Maximum possible marks"
    )
    
    obtained_marks: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
        comment="Marks obtained by student"
    )
    
    percentage: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
        comment="Score percentage"
    )
    
    grade: Mapped[Optional[str]] = mapped_column(
        String(5),
        nullable=True,
        comment="Letter grade (A, B, C, etc.)"
    )
    
    overall_feedback: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="AI-generated overall feedback"
    )
    
    overall_feedback_gujarati: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Overall feedback in Gujarati"
    )
    
    status: Mapped[CheckedPaperStatus] = mapped_column(
        Enum(CheckedPaperStatus, name="checked_paper_status"),
        nullable=False,
        default=CheckedPaperStatus.PENDING,
        comment="Processing status"
    )
    
    reviewed_by: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="Teacher who reviewed this paper"
    )
    
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the paper was reviewed"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    # Relationships
    answer_key: Mapped["AnswerKey"] = relationship(
        "AnswerKey",
        back_populates="checked_papers"
    )
    teacher: Mapped["User"] = relationship("User", foreign_keys=[teacher_id])
    reviewer: Mapped[Optional["User"]] = relationship("User", foreign_keys=[reviewed_by])
    
    def __repr__(self) -> str:
        return f"<CheckedPaper {self.id}: {self.student_name or 'Unknown'} - {self.status.value}>"
    
    def calculate_grade(self) -> str:
        """
        Calculate letter grade based on percentage.
        
        Returns:
            str: Letter grade (A+, A, B+, B, C, D, F)
        """
        if self.percentage >= 90:
            return "A+"
        elif self.percentage >= 80:
            return "A"
        elif self.percentage >= 70:
            return "B+"
        elif self.percentage >= 60:
            return "B"
        elif self.percentage >= 50:
            return "C"
        elif self.percentage >= 40:
            return "D"
        else:
            return "F"


# Keep backward compatibility - these can be deprecated later
# Old models for existing data migration

class SubmissionStatus(str, enum.Enum):
    """Status of a paper submission (DEPRECATED - use CheckedPaperStatus)."""
    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    OCR_PROCESSING = "ocr_processing"
    GRADING = "grading"
    COMPLETED = "completed"
    FAILED = "failed"


class Submission(Base):
    """
    Legacy Submission Model (DEPRECATED).
    
    This model is kept for backward compatibility with existing data.
    New implementations should use CheckedPaper instead.
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
    
    input_file_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    
    student_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    
    extracted_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    overall_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        default=0.0
    )
    
    max_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        default=0.0
    )
    
    summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    answers: Mapped[List["GradedAnswer"]] = relationship(
        "GradedAnswer",
        back_populates="submission",
        cascade="all, delete-orphan",
        lazy="selectin"
    )


class GradedAnswer(Base):
    """
    Legacy Graded Answer Model (DEPRECATED).
    
    This model is kept for backward compatibility.
    New implementations store results as JSONB in CheckedPaper.results.
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
    
    question_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    student_answer_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    
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
    )
    
    confidence_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    
    submission: Mapped["Submission"] = relationship(
        "Submission",
        back_populates="answers"
    )
