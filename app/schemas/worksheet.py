"""
BhashaAI Backend - Worksheet Schemas

Pydantic schemas for worksheet generation and solving.
"""

from datetime import datetime
from typing import Any, Optional, List
from uuid import UUID

from pydantic import BaseModel, Field

class WorksheetStep(BaseModel):
    step_text: str
    answer_key: str
    hint: Optional[str] = None

class WorksheetQuestionBase(BaseModel):
    content: str
    steps: List[WorksheetStep]
    correct_answer: str
    order: int

class WorksheetBase(BaseModel):
    title: str
    topic: str
    subject: str
    grade_level: Optional[str] = None
    difficulty: str = "medium"

class WorksheetCreate(WorksheetBase):
    pass

class WorksheetGenerateRequest(BaseModel):
    topic: str
    subject: str
    grade_level: str
    difficulty: str = "medium"
    num_questions: int = 3

class WorksheetResponse(WorksheetBase):
    id: UUID
    user_id: UUID
    status: str
    created_at: datetime
    questions: List[WorksheetQuestionBase] = []

    model_config = {"from_attributes": True}

# Game/Attempt Schemas

class AttemptStartRequest(BaseModel):
    worksheet_id: UUID

class SubmitStepRequest(BaseModel):
    attempt_id: UUID
    step_answer: str

class StepFeedback(BaseModel):
    is_correct: bool
    message: str
    points_awarded: int
    next_step_index: Optional[int] = None
    next_question_index: Optional[int] = None
    is_complete: bool = False
    correct_answer: Optional[str] = None # Show if they give up or after max retries (optional logic)

class AttemptResponse(BaseModel):
    id: UUID
    worksheet_id: UUID
    current_question_index: int
    current_step_index: int
    score: int
    status: str
    progress_data: dict[str, Any]
    
    model_config = {"from_attributes": True}
