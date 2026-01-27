"""
BhashaAI Backend - Assignment Schemas

Pydantic schemas for assignment inputs, solutions, and help sessions.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import AssignmentMode, DifficultyLevel, InputType, ProcessingStatus


class Step(BaseModel):
    """Single step in a solution."""
    
    step: int
    description: str
    explanation: Optional[str] = None


class AssignmentBase(BaseModel):
    """Base assignment schema."""
    
    input_type: InputType = Field(InputType.TEXT)
    subject: Optional[str] = None
    grade_level: Optional[str] = None
    mode: AssignmentMode = Field(AssignmentMode.SOLVE)
    language: str = Field("gu", pattern="^(gu|en|gu-en)$")


class AssignmentSubmit(AssignmentBase):
    """Schema for submitting an assignment."""
    
    question_text: str = Field(..., min_length=1)
    question_image_url: Optional[str] = None


class AssignmentCreate(BaseModel):
    """Schema for creating a new assignment from a QP."""
    title: str
    description: Optional[str] = None
    question_paper_id: UUID
    due_date: Optional[datetime] = None
    status: str = "published"
    mode: str = "solve" # solve or help mode default for this assignment



class SolutionResponse(BaseModel):
    """Detailed solution response schema."""
    
    steps: list[Step]
    final_answer: str
    explanation: Optional[str] = None
    difficulty: DifficultyLevel


class HelpSessionResponse(BaseModel):
    """Help session state response."""
    
    id: UUID
    current_hint_level: int
    is_completed: bool
    interactions: list[dict[str, Any]]
    
    model_config = {"from_attributes": True}


class AssignmentResponse(AssignmentBase):
    """Full assignment response."""
    
    id: UUID
    user_id: UUID
    question_text: str
    question_image_url: Optional[str] = None
    status: ProcessingStatus
    extra_metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    
    # Optional related data
    solution: Optional[SolutionResponse] = None
    help_session: Optional[HelpSessionResponse] = None
    
    model_config = {"from_attributes": True}
    
    @classmethod
    def from_orm_with_details(cls, assignment):
        """Create response mapping nested ORM objects."""
        data = assignment.__dict__.copy()
        
        if assignment.solution:
            sol = assignment.solution
            data["solution"] = SolutionResponse(
                steps=[Step(**s) for s in sol.steps],
                final_answer=sol.final_answer,
                explanation=sol.explanation,
                difficulty=sol.difficulty
            )
            
        if assignment.help_session:
            data["help_session"] = HelpSessionResponse.model_validate(assignment.help_session)
            
        return cls(**data)


class AssignmentListResponse(BaseModel):
    """Paginated list of assignments."""
    
    assignments: list[AssignmentResponse]
    total: int
    page: int
    per_page: int
    pages: int


class HintRequest(BaseModel):
    """Request for next hint in help mode."""
    
    student_response: Optional[str] = None
    request_next_level: bool = True


class HintResponse(BaseModel):
    """Response with new hint."""
    
    hint: str
    hint_level: int
    is_completed: bool
    explanation: Optional[str] = None
