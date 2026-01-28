"""
BhashaAI Backend - Flashcard Schemas

Pydantic models for flashcard endpoints.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

# --- Flashcard Schemas ---
from pydantic import BaseModel, ConfigDict, Field

class FlashcardBase(BaseModel):
    """Base schema for a flashcard."""
    front: str = Field(..., min_length=1, description="Question or term on front")
    back: str = Field(..., min_length=1, description="Answer or definition on back")
    hint: Optional[str] = Field(None, description="Optional hint")
    order_index: int = Field(0, description="Order in the deck")


class FlashcardCreate(FlashcardBase):
    """Schema for creating a flashcard."""
    pass


class FlashcardResponse(FlashcardBase):
    """Schema for reading a flashcard."""
    id: UUID
    deck_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Deck Schemas ---

class FlashcardDeckBase(BaseModel):
    """Base schema for a flashcard deck."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    subject: Optional[str] = None
    is_public: bool = False


class FlashcardDeckCreate(FlashcardDeckBase):
    """Schema for creating a deck."""
    cards: List[FlashcardCreate] = [] # Optional initial cards


class FlashcardDeckResponse(FlashcardDeckBase):
    """Schema for reading a deck."""
    id: UUID
    user_id: UUID
    card_count: int
    view_count: int
    created_at: datetime
    updated_at: datetime
    
    # Optional nested cards
    cards: List[FlashcardResponse] = []

    model_config = ConfigDict(from_attributes=True)


# --- Generation Request ---

class FlashcardGenerateRequest(BaseModel):
    """Request to generate flashcards from content."""
    topic: Optional[str] = None
    document_id: Optional[UUID] = None
    subject: Optional[str] = None
    grade_level: Optional[str] = None
    count: int = Field(10, ge=5, le=50)
    language: str = "gu" # gu, en, gu-en
