"""
BhashaAI Backend - Question Paper Schemas

Pydantic schemas for question paper generation and management.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class DifficultyDistribution(BaseModel):
    """Distribution of questions by difficulty."""
    
    easy: int = Field(30, ge=0, le=100, description="% of easy questions")
    medium: int = Field(50, ge=0, le=100, description="% of medium questions")
    hard: int = Field(20, ge=0, le=100, description="% of hard questions")
    
    @field_validator("hard")
    @classmethod
    def validate_total(cls, v: int, info) -> int:
        """Ensure percentages sum to 100."""
        easy = info.data.get("easy", 30)
        medium = info.data.get("medium", 50)
        total = easy + medium + v
        if total != 100:
            raise ValueError(f"Difficulty percentages must sum to 100, got {total}")
        return v


class QuestionTypeCount(BaseModel):
    """Count of questions by type."""
    
    mcq: int = Field(0, ge=0, description="Multiple choice questions")
    short_answer: int = Field(0, ge=0, description="Short answer questions")
    long_answer: int = Field(0, ge=0, description="Long answer questions")
    true_false: int = Field(0, ge=0, description="True/False questions")
    fill_blank: int = Field(0, ge=0, description="Fill in the blank questions")


class QuestionBase(BaseModel):
    """Base question schema."""
    
    question_text: str = Field(..., min_length=5)
    question_text_gujarati: Optional[str] = None
    question_type: str = Field("short_answer")
    marks: float = Field(1.0, gt=0)
    difficulty: str = Field("medium")
    answer: Optional[str] = None
    answer_gujarati: Optional[str] = None
    options: Optional[list[str]] = None
    correct_option: Optional[int] = Field(None, ge=0, le=5)
    explanation: Optional[str] = None
    bloom_level: Optional[str] = None
    topic: Optional[str] = None
    keywords: Optional[list[str]] = None


class QuestionCreate(QuestionBase):
    """Schema for creating a question."""
    
    question_number: int = Field(..., ge=1)


class QuestionUpdate(BaseModel):
    """Schema for updating a question."""
    
    question_text: Optional[str] = None
    question_text_gujarati: Optional[str] = None
    marks: Optional[float] = None
    difficulty: Optional[str] = None
    answer: Optional[str] = None
    answer_gujarati: Optional[str] = None
    options: Optional[list[str]] = None
    correct_option: Optional[int] = None
    explanation: Optional[str] = None


class QuestionResponse(QuestionBase):
    """Schema for question response."""
    
    id: UUID
    paper_id: UUID
    question_number: int
    created_at: datetime
    
    model_config = {"from_attributes": True}


# Question Paper Schemas

class QuestionPaperBase(BaseModel):
    """Base question paper schema."""
    
    title: str = Field(..., min_length=3, max_length=255)
    title_gujarati: Optional[str] = Field(None, max_length=255)
    subject: str = Field(..., min_length=2, max_length=100)
    grade_level: Optional[str] = Field(None, max_length=20)
    total_marks: int = Field(100, ge=1, le=1000)
    duration_minutes: Optional[int] = Field(None, ge=15, le=360)
    language: str = Field("gu", pattern="^(gu|en|gu-en)$")
    instructions: Optional[str] = None
    instructions_gujarati: Optional[str] = None


class GeneratePaperRequest(BaseModel):
    """Schema for question paper generation request."""
    
    # Source (one required)
    document_id: Optional[UUID] = Field(None, description="Source document ID")
    topic: Optional[str] = Field(None, max_length=500, description="Topic for generation")
    context: Optional[str] = Field(None, max_length=5000, description="Custom context text")
    
    # Paper details
    title: str = Field(..., min_length=3, max_length=255)
    title_gujarati: Optional[str] = None
    subject: str = Field(..., min_length=2, max_length=100)
    grade_level: Optional[str] = None
    total_marks: int = Field(100, ge=1, le=500)
    duration_minutes: Optional[int] = Field(None, ge=15, le=360)
    language: str = Field("gu", pattern="^(gu|en|gu-en)$")
    
    # Question distribution
    difficulty_distribution: DifficultyDistribution = Field(default_factory=DifficultyDistribution)
    question_types: QuestionTypeCount = Field(default_factory=QuestionTypeCount)
    
    # Options
    include_answers: bool = Field(True, description="Include answer key")
    bloom_taxonomy_levels: Optional[list[str]] = None
    
    @field_validator("topic", "document_id", "context")
    @classmethod
    def at_least_one_source(cls, v, info):
        """At least one source must be provided."""
        # This is validated at the service level
        return v


class QuestionPaperCreate(QuestionPaperBase):
    """Schema for creating a question paper manually."""
    
    document_id: Optional[UUID] = None
    difficulty_distribution: dict[str, Any] = Field(default_factory=lambda: {"easy": 30, "medium": 50, "hard": 20})
    question_type_distribution: dict[str, Any] = Field(default_factory=dict)


class QuestionPaperUpdate(BaseModel):
    """Schema for updating a question paper."""
    
    title: Optional[str] = None
    title_gujarati: Optional[str] = None
    subject: Optional[str] = None
    grade_level: Optional[str] = None
    total_marks: Optional[int] = None
    duration_minutes: Optional[int] = None
    language: Optional[str] = None
    instructions: Optional[str] = None
    instructions_gujarati: Optional[str] = None
    status: Optional[str] = None


class QuestionPaperResponse(QuestionPaperBase):
    """Schema for question paper response."""
    
    id: UUID
    user_id: UUID
    institution_id: Optional[UUID] = None
    document_id: Optional[UUID] = None
    difficulty_distribution: dict[str, Any]
    question_type_distribution: dict[str, Any]
    status: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    # Related
    questions: list[QuestionResponse] = []
    question_count: int = 0
    
    model_config = {"from_attributes": True}
    
    @classmethod
    def from_orm_with_count(cls, paper):
        """Create response with question count."""
        data = paper.__dict__.copy()
        data["question_count"] = len(paper.questions) if paper.questions else 0
        return cls(**data)


class QuestionPaperListResponse(BaseModel):
    """Schema for paginated paper list."""
    
    papers: list[QuestionPaperResponse]
    total: int
    page: int
    per_page: int
    pages: int


class GeneratePaperResponse(BaseModel):
    """Schema for paper generation response."""
    
    success: bool = True
    message: str = "Question paper generated successfully"
    message_gu: str = "પ્રશ્નપત્ર સફળતાપૂર્વક જનરેટ થયું"
    data: QuestionPaperResponse


class ExportPaperRequest(BaseModel):
    """Schema for paper export request."""
    
    format: str = Field("pdf", pattern="^(pdf|docx|md|html)$")
    include_answers: bool = Field(True)
    include_header: bool = Field(True)
    watermark: Optional[str] = None
