"""
BhashaAI Backend - Dictionary Models

SQLAlchemy models for the bilingual English-Gujarati dictionary:
- DictionaryEntry: Cached word translations with meanings and examples
- UserDictionaryHistory: Track user's word lookup history

These models support:
- Bidirectional translation (EN→GU, GU→EN)
- Part of speech tagging (noun, verb, adjective, etc.)
- Example sentences with translations
- Synonyms and antonyms
- User search history tracking
"""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import PartOfSpeech, TranslationDirection

if TYPE_CHECKING:
    from app.models.user import User


class DictionaryEntry(Base):
    """
    Cached dictionary entry for bilingual translations.
    
    Stores LLM-generated translations with full linguistic details
    to avoid repeated API calls for the same words.
    
    Attributes:
        id: Unique identifier (UUID)
        word: Original word (indexed for fast lookup)
        language: Source language ('en' or 'gu')
        translation: Translated word in target language
        transliteration: Romanized pronunciation (for Gujarati)
        part_of_speech: Grammatical category (noun, verb, etc.)
        meaning: Definition in English
        meaning_gujarati: Definition in Gujarati
        example_sentence: Usage example in source language
        example_sentence_translation: Example translated
        synonyms: List of similar words (JSONB)
        antonyms: List of opposite words (JSONB)
        audio_url: TTS pronunciation URL
        lookup_count: Number of times this entry was looked up
        created_at: Entry creation timestamp
        updated_at: Last update timestamp
    
    Indexes:
        - word + language (composite) for fast lookups
        - lookup_count for popular words
    """
    __tablename__ = "dictionary_entries"
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.uuid_generate_v4(),
        nullable=False,
    )
    
    word: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Original word to translate"
    )
    
    language: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="Source language: 'en' or 'gu'"
    )
    
    translation: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Translated word in target language"
    )
    
    transliteration: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Romanized pronunciation"
    )
    
    part_of_speech: Mapped[PartOfSpeech] = mapped_column(
        Enum(PartOfSpeech, name="part_of_speech"),
        nullable=False,
        default=PartOfSpeech.NOUN,
        comment="Grammatical category"
    )
    
    meaning: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Definition in English"
    )
    
    meaning_gujarati: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Definition in Gujarati"
    )
    
    example_sentence: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Example usage in source language"
    )
    
    example_sentence_translation: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Example translated to target language"
    )
    
    synonyms: Mapped[List[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=[],
        comment="List of similar words"
    )
    
    antonyms: Mapped[List[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=[],
        comment="List of opposite words"
    )
    
    audio_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="TTS pronunciation URL"
    )
    
    lookup_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of times looked up"
    )
    
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
    
    # Composite index for word + language lookups
    __table_args__ = (
        Index("idx_dictionary_word_language", "word", "language"),
        Index("idx_dictionary_lookup_count", "lookup_count"),
    )
    
    # Relationships
    history_entries: Mapped[List["UserDictionaryHistory"]] = relationship(
        "UserDictionaryHistory",
        back_populates="dictionary_entry",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<DictionaryEntry {self.word} ({self.language}) -> {self.translation}>"


class UserDictionaryHistory(Base):
    """
    Track user's word lookup history.
    
    Records which words users have looked up, enabling:
    - Recently viewed words list
    - Lookup frequency tracking
    - Personalized suggestions
    
    Attributes:
        id: Unique identifier (UUID)
        user_id: User who performed the lookup
        dictionary_entry_id: The word that was looked up
        lookup_count: How many times this user looked up this word
        last_looked_up: Most recent lookup timestamp
        created_at: First lookup timestamp
    
    Constraints:
        - Unique (user_id, dictionary_entry_id) pair
    """
    __tablename__ = "user_dictionary_history"
    
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
        comment="User who performed the lookup"
    )
    
    dictionary_entry_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dictionary_entries.id", ondelete="CASCADE"),
        nullable=False,
        comment="Word that was looked up"
    )
    
    lookup_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="Number of times this user looked up this word"
    )
    
    last_looked_up: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Most recent lookup timestamp"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    # Unique constraint and indexes
    __table_args__ = (
        Index("idx_user_dict_history_user", "user_id"),
        Index("idx_user_dict_history_last_lookup", "user_id", "last_looked_up"),
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    dictionary_entry: Mapped["DictionaryEntry"] = relationship(
        "DictionaryEntry",
        back_populates="history_entries"
    )
    
    def __repr__(self) -> str:
        return f"<UserDictionaryHistory user={self.user_id} word={self.dictionary_entry_id}>"
