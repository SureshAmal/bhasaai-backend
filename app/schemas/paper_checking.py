"""
BhashaAI Backend - Paper Checking Schemas

Pydantic schemas for Answer Keys, Submissions, and Grading Results.
"""

from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.paper_checking import SubmissionStatus


# --- Answer Key Schemas ---

class AnswerCriteria(BaseModel):
    """Grading criteria for a single question."""
    expected_answer: str
    keywords: List[str] = Field(default_factory=list)
    max_marks: float
    partial_marking: bool = True
    acceptable_variations: List[str] = Field(default_factory=list)


class AnswerKeyCreate(BaseModel):
    """Request to create an answer key."""
    question_paper_id: UUID
    # Map of question_id -> criteria
    content: dict[str, AnswerCriteria]


class AnswerKeyResponse(BaseModel):
    """Response for answer key."""
    id: UUID
    question_paper_id: UUID
    content: dict[str, Any]
    created_at: datetime
    
    model_config = {"from_attributes": True}


# --- Submission & Grading Schemas ---

class SubmissionCreate(BaseModel):
    """Metadata for a new submission."""
    question_paper_id: Optional[UUID] = None
    student_name: Optional[str] = None


class GradedAnswerResponse(BaseModel):
    """Result for a single answer."""
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
    """Response for a full submission."""
    id: UUID
    user_id: UUID
    question_paper_id: Optional[UUID]
    status: SubmissionStatus
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
    new_marks: float
    feedback_update: Optional[str] = None
