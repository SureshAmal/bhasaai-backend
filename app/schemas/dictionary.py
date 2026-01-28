"""
BhashaAI Backend - Dictionary Schemas

Pydantic schemas for the bilingual English-Gujarati dictionary API:
- Request validation
- Response serialization
- LLM result parsing
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.enums import PartOfSpeech, TranslationDirection


class DictionaryLookupRequest(BaseModel):
    """
    Request to lookup or translate a word.
    
    Attributes:
        word: The word to translate (1-100 characters)
        direction: Translation direction (EN→GU or GU→EN)
        include_examples: Whether to include example sentences
        include_audio: Whether to generate TTS audio
    """
    word: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Word to translate"
    )
    direction: TranslationDirection = Field(
        default=TranslationDirection.EN_TO_GU,
        description="Translation direction"
    )
    include_examples: bool = Field(
        default=True,
        description="Include example sentences"
    )
    include_audio: bool = Field(
        default=False,
        description="Generate TTS audio pronunciation"
    )
    
    @field_validator('word')
    @classmethod
    def clean_word(cls, v: str) -> str:
        """Normalize word: strip whitespace and lowercase for consistent lookup."""
        return v.strip()
    
    model_config = {"json_schema_extra": {
        "example": {
            "word": "hello",
            "direction": "en_to_gu",
            "include_examples": True,
            "include_audio": False
        }
    }}


class TranslationResult(BaseModel):
    """
    LLM translation result structure.
    
    Parsed from LLM JSON response for structured dictionary data.
    """
    translation: str = Field(..., description="Translated word")
    transliteration: Optional[str] = Field(None, description="Romanized pronunciation")
    part_of_speech: str = Field(..., description="Grammatical category")
    meaning: str = Field(..., description="Definition in English")
    meaning_gujarati: Optional[str] = Field(None, description="Definition in Gujarati")
    example_sentence: Optional[str] = Field(None, description="Example usage")
    example_sentence_translation: Optional[str] = Field(None, description="Example translation")
    synonyms: List[str] = Field(default_factory=list, description="Similar words")
    antonyms: List[str] = Field(default_factory=list, description="Opposite words")
    confidence: float = Field(default=0.9, ge=0.0, le=1.0, description="Translation confidence")
    
    @field_validator('part_of_speech')
    @classmethod
    def validate_part_of_speech(cls, v: str) -> str:
        """Ensure part of speech is valid, default to noun if unknown."""
        valid_pos = [pos.value for pos in PartOfSpeech]
        return v.lower() if v.lower() in valid_pos else "noun"


class DictionaryEntryResponse(BaseModel):
    """
    Full dictionary entry response.
    
    Returned when looking up or retrieving a cached word.
    """
    id: UUID = Field(..., description="Entry unique identifier")
    word: str = Field(..., description="Original word")
    language: str = Field(..., description="Source language (en/gu)")
    translation: str = Field(..., description="Translated word")
    transliteration: Optional[str] = Field(None, description="Romanized pronunciation")
    part_of_speech: str = Field(..., description="Grammatical category")
    meaning: str = Field(..., description="Definition in English")
    meaning_gujarati: Optional[str] = Field(None, description="Definition in Gujarati")
    example_sentence: Optional[str] = Field(None, description="Example in source language")
    example_sentence_translation: Optional[str] = Field(None, description="Example translated")
    synonyms: List[str] = Field(default_factory=list, description="Similar words")
    antonyms: List[str] = Field(default_factory=list, description="Opposite words")
    audio_url: Optional[str] = Field(None, description="TTS pronunciation URL")
    lookup_count: int = Field(default=0, description="Times looked up")
    created_at: datetime = Field(..., description="Entry creation time")
    
    model_config = {"from_attributes": True}


class SearchHistoryItem(BaseModel):
    """
    Single item in user's search history.
    """
    id: UUID = Field(..., description="History entry ID")
    word: str = Field(..., description="Looked up word")
    translation: str = Field(..., description="Translation")
    part_of_speech: str = Field(..., description="Grammatical category")
    lookup_count: int = Field(..., description="Times this user looked up")
    last_looked_up: datetime = Field(..., description="Most recent lookup")
    
    model_config = {"from_attributes": True}


class SearchHistoryResponse(BaseModel):
    """
    Paginated list of user's search history.
    """
    items: List[SearchHistoryItem] = Field(..., description="History entries")
    total: int = Field(..., description="Total items")
    page: int = Field(default=1, description="Current page")
    per_page: int = Field(default=50, description="Items per page")


class DictionaryStats(BaseModel):
    """
    Dictionary usage statistics.
    """
    total_entries: int = Field(..., description="Total cached entries")
    total_lookups: int = Field(..., description="Total lookup count")
    popular_words: List[str] = Field(default_factory=list, description="Most looked up words")
