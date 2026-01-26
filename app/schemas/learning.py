"""
BhashaAI Backend - Learning Schemas

Pydantic schemas for the Learning Module.
"""

from datetime import datetime
from typing import Any, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.learning import LearningDifficulty, ExerciseType

# --- Profile Schemas ---

class LearningProfileResponse(BaseModel):
    """User learning profile statistics."""
    total_xp: int
    streak_days: int
    current_level: str
    vocabulary_mastered: int
    grammar_concepts_completed: int
    last_activity_date: datetime
    
    model_config = {"from_attributes": True}

# --- Vocabulary Schemas ---

class VocabularyItemResponse(BaseModel):
    """Vocabulary item details."""
    id: UUID
    gujarati_word: str
    english_translation: str
    transliteration: Optional[str] = None
    difficulty_level: int
    category: str
    image_url: Optional[str] = None
    audio_url: Optional[str] = None
    example_sentence: Optional[str] = None
    
    model_config = {"from_attributes": True}

class VocabularyLessonItem(BaseModel):
    """Item in a daily lesson."""
    type: str = Field(description="'new' or 'review'")
    progress_id: Optional[UUID] = None
    word: VocabularyItemResponse

class VocabularyProgressSubmit(BaseModel):
    """Submission of study result."""
    quality: int = Field(..., ge=0, le=5, description="0=Forgot, 5=Perfect")

class ProgressResponse(BaseModel):
    """Scheduling result after submission."""
    vocabulary_item_id: UUID
    next_review_date: datetime
    interval_days: float
    is_mastered: bool
    xp_gained: int = 0

# --- Grammar & Exercise Schemas ---

class GrammarTopicResponse(BaseModel):
    """Grammar topic definition."""
    id: UUID
    title: str
    description: Optional[str] = None
    difficulty: LearningDifficulty
    
    model_config = {"from_attributes": True}

class ExerciseCreate(BaseModel):
    exercise_type: ExerciseType
    content: dict[str, Any]
    difficulty_level: int = 1

class TTSRequest(BaseModel):
    """Request for Text-to-Speech generation."""
    text: str
    language: str = "gu"
