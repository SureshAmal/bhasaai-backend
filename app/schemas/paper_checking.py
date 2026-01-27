"""
BhashaAI Backend - Paper Checking Schemas

Pydantic schemas for paper checking API:
- Answer Key creation and response schemas
- Paper submission and grading result schemas
- Proper field validation matching API specification
"""

from datetime import datetime
from typing import Any, List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.paper_checking import CheckedPaperStatus


# =============================================================================
# Answer Key Schemas
# =============================================================================

class AnswerItem(BaseModel):
    """
    Single answer item in an answer key.
    
    Supports MCQ, short answer, and long answer question types.
    """
    question_number: int = Field(..., ge=1, description="Question number (1-indexed)")
    type: Literal["mcq", "short_answer", "long_answer"] = Field(
        ..., 
        description="Question type"
    )
    correct_answer: Optional[str] = Field(
        None, 
        description="Correct option for MCQ (e.g., 'A', 'B', 'C', 'D')"
    )
    expected_answer: Optional[str] = Field(
        None, 
        description="Expected answer text for short/long answer questions"
    )
    expected_answer_gujarati: Optional[str] = Field(
        None, 
        description="Expected answer in Gujarati"
    )
    keywords: List[str] = Field(
        default_factory=list, 
        description="Keywords for semantic matching"
    )
    max_marks: float = Field(..., gt=0, description="Maximum marks for this question")
    partial_marking: bool = Field(
        True, 
        description="Whether partial marks are allowed"
    )
    acceptable_variations: List[str] = Field(
        default_factory=list,
        description="Alternative acceptable answers"
    )
    
    @field_validator("correct_answer")
    @classmethod
    def validate_mcq_answer(cls, v: Optional[str], info) -> Optional[str]:
        """Validate MCQ answer is provided for MCQ type."""
        if info.data.get("type") == "mcq" and not v:
            raise ValueError("correct_answer is required for MCQ type questions")
        return v
    
    @field_validator("expected_answer")
    @classmethod
    def validate_text_answer(cls, v: Optional[str], info) -> Optional[str]:
        """Validate expected_answer is provided for text-based questions."""
        q_type = info.data.get("type")
        if q_type in ("short_answer", "long_answer") and not v:
            raise ValueError(f"expected_answer is required for {q_type} questions")
        return v


class MarkingScheme(BaseModel):
    """
    Marking scheme configuration for grading.
    
    Controls how keyword matching and semantic similarity affect scores.
    """
    keyword_match_percent: float = Field(
        50.0, 
        ge=0, 
        le=100,
        description="Weight percentage for keyword matching (0-100)"
    )
    semantic_similarity_threshold: float = Field(
        0.7, 
        ge=0, 
        le=1,
        description="Minimum semantic similarity score (0-1)"
    )


class AnswerKeyCreate(BaseModel):
    """
    Request schema for creating an answer key.
    
    Example:
        {
            "title": "Science Quarterly Exam - Answer Key",
            "subject": "science",
            "total_marks": 50,
            "answers": [
                {"question_number": 1, "type": "mcq", "correct_answer": "B", "max_marks": 1},
                {"question_number": 2, "type": "short_answer", "expected_answer": "...", "keywords": [...], "max_marks": 5}
            ]
        }
    """
    paper_id: Optional[UUID] = Field(
        None, 
        description="Optional linked Question Paper ID"
    )
    title: str = Field(
        ..., 
        min_length=1, 
        max_length=255, 
        description="Answer key title"
    )
    subject: Optional[str] = Field(
        None, 
        max_length=100, 
        description="Subject (e.g., 'science', 'math')"
    )
    total_marks: int = Field(
        ..., 
        gt=0, 
        description="Total marks for all questions"
    )
    answers: List[AnswerItem] = Field(
        ..., 
        min_length=1, 
        description="List of answer items"
    )
    marking_scheme: Optional[MarkingScheme] = Field(
        None, 
        description="Marking configuration"
    )
    
    @field_validator("answers")
    @classmethod
    def validate_unique_question_numbers(cls, v: List[AnswerItem]) -> List[AnswerItem]:
        """Ensure question numbers are unique."""
        numbers = [a.question_number for a in v]
        if len(numbers) != len(set(numbers)):
            raise ValueError("Question numbers must be unique")
        return v
    
    @field_validator("answers")
    @classmethod
    def validate_total_marks(cls, v: List[AnswerItem], info) -> List[AnswerItem]:
        """Validate that answer marks sum up correctly."""
        total = info.data.get("total_marks")
        if total:
            answer_total = sum(a.max_marks for a in v)
            if abs(answer_total - total) > 0.01:  # Allow small float differences
                raise ValueError(
                    f"Sum of answer max_marks ({answer_total}) doesn't match total_marks ({total})"
                )
        return v


class AnswerKeyResponse(BaseModel):
    """Response schema for an answer key."""
    id: UUID
    user_id: UUID
    paper_id: Optional[UUID] = None
    title: str
    subject: Optional[str] = None
    total_marks: int
    total_questions: int = Field(
        default=0,
        description="Number of questions in the answer key"
    )
    answers: List[dict] = Field(default_factory=list)
    marking_scheme: Optional[dict] = None
    created_at: datetime
    
    model_config = {"from_attributes": True}
    
    @classmethod
    def from_db(cls, db_obj: Any) -> "AnswerKeyResponse":
        """Create response from database object."""
        return cls(
            id=db_obj.id,
            user_id=db_obj.user_id,
            paper_id=db_obj.paper_id,
            title=db_obj.title,
            subject=db_obj.subject,
            total_marks=db_obj.total_marks,
            total_questions=len(db_obj.answers) if db_obj.answers else 0,
            answers=db_obj.answers or [],
            marking_scheme=db_obj.marking_scheme,
            created_at=db_obj.created_at,
        )


class AnswerKeyListItem(BaseModel):
    """Lightweight response for listing answer keys."""
    id: UUID
    title: str
    subject: Optional[str] = None
    total_marks: int
    total_questions: int
    created_at: datetime
    
    model_config = {"from_attributes": True}


# =============================================================================
# Checked Paper Schemas
# =============================================================================

class CheckPaperSubmit(BaseModel):
    """
    Form data for submitting a paper for checking.
    
    Note: File is sent separately as multipart form data.
    """
    answer_key_id: UUID = Field(
        ..., 
        description="Reference answer key ID"
    )
    student_name: Optional[str] = Field(
        None, 
        max_length=255, 
        description="Student's name"
    )
    student_id: Optional[str] = Field(
        None, 
        max_length=100, 
        description="Student's ID or roll number"
    )


class QuestionResult(BaseModel):
    """Grading result for a single question."""
    question_number: int = Field(..., description="Question number")
    max_marks: float = Field(..., description="Maximum marks")
    obtained_marks: float = Field(..., ge=0, description="Marks obtained")
    status: Literal["correct", "partial", "incorrect"] = Field(
        ..., 
        description="Grading status"
    )
    student_answer: Optional[str] = Field(
        None, 
        description="Student's answer (OCR extracted or MCQ choice)"
    )
    keyword_matches: List[str] = Field(
        default_factory=list, 
        description="Keywords found in student's answer"
    )
    missing_keywords: List[str] = Field(
        default_factory=list, 
        description="Expected keywords not found"
    )
    semantic_similarity: Optional[float] = Field(
        None, 
        ge=0, 
        le=1, 
        description="Semantic similarity score (0-1)"
    )
    feedback: str = Field(..., description="Feedback for this answer")
    feedback_gujarati: Optional[str] = Field(
        None, 
        description="Feedback in Gujarati"
    )


class CheckedPaperResponse(BaseModel):
    """Full response for a checked paper with all results."""
    id: UUID
    answer_key_id: UUID
    student_name: Optional[str] = None
    student_id: Optional[str] = None
    status: str
    total_marks: int
    obtained_marks: float
    percentage: float
    grade: Optional[str] = None
    results: List[QuestionResult] = Field(default_factory=list)
    overall_feedback: Optional[str] = None
    overall_feedback_gujarati: Optional[str] = None
    created_at: datetime
    
    model_config = {"from_attributes": True}
    
    @classmethod
    def from_db(cls, db_obj: Any) -> "CheckedPaperResponse":
        """Create response from database object."""
        return cls(
            id=db_obj.id,
            answer_key_id=db_obj.answer_key_id,
            student_name=db_obj.student_name,
            student_id=db_obj.student_id,
            status=db_obj.status.value if hasattr(db_obj.status, 'value') else str(db_obj.status),
            total_marks=db_obj.total_marks,
            obtained_marks=db_obj.obtained_marks,
            percentage=db_obj.percentage,
            grade=db_obj.grade,
            results=[QuestionResult(**r) for r in (db_obj.results or [])],
            overall_feedback=db_obj.overall_feedback,
            overall_feedback_gujarati=db_obj.overall_feedback_gujarati,
            created_at=db_obj.created_at,
        )


class CheckedPaperListItem(BaseModel):
    """Lightweight response for listing checked papers."""
    id: UUID
    student_name: Optional[str] = None
    student_id: Optional[str] = None
    status: str
    obtained_marks: float
    percentage: float
    grade: Optional[str] = None
    created_at: datetime
    
    model_config = {"from_attributes": True}


class CheckedPaperSubmitResponse(BaseModel):
    """Response when a paper is submitted for checking."""
    id: UUID
    answer_key_id: UUID
    student_name: Optional[str] = None
    student_id: Optional[str] = None
    status: str
    task_id: Optional[str] = Field(
        None, 
        description="Background task ID for tracking progress"
    )
    
    model_config = {"from_attributes": True}


# =============================================================================
# Legacy Schemas (for backward compatibility)
# =============================================================================

class AnswerCriteria(BaseModel):
    """Legacy: Grading criteria for a single question."""
    expected_answer: str
    keywords: List[str] = Field(default_factory=list)
    max_marks: float
    partial_marking: bool = True
    acceptable_variations: List[str] = Field(default_factory=list)


class LegacyAnswerKeyCreate(BaseModel):
    """Legacy: Request to create an answer key (old format)."""
    question_paper_id: UUID
    content: dict[str, AnswerCriteria]


class LegacyAnswerKeyResponse(BaseModel):
    """Legacy: Response for answer key."""
    id: UUID
    question_paper_id: UUID
    content: dict[str, Any]
    created_at: datetime
    
    model_config = {"from_attributes": True}


class GradedAnswerResponse(BaseModel):
    """Legacy: Result for a single graded answer."""
    id: UUID
    submission_id: UUID
    question_id: Optional[UUID]
    question_text: Optional[str]
    student_answer_text: str
    marks_obtained: float
    max_marks: float
    feedback: Optional[str]
    confidence_score: Optional[float]
    
    model_config = {"from_attributes": True}


class SubmissionResponse(BaseModel):
    """Legacy: Response for a submission."""
    id: UUID
    user_id: UUID
    question_paper_id: Optional[UUID]
    status: str
    input_file_url: str
    student_name: Optional[str]
    extracted_text: Optional[str]
    overall_score: float
    max_score: float
    summary: Optional[str]
    created_at: datetime
    answers: List[GradedAnswerResponse] = []
    
    model_config = {"from_attributes": True}


class GradeOverrideRequest(BaseModel):
    """Request to manually update grades."""
    graded_answer_id: UUID
    new_marks: float = Field(..., ge=0)
    feedback_update: Optional[str] = None
