"""
BhashaAI Backend - Learning Models

Models for the Gujarati Learning Module, including:
- LearningProfile: User progress and gamification
- VocabularyItem: Words to learn
- UserWordProgress: Spaced repetition tracking (SM-2)
- GrammarTopic: Grammar lessons
- Exercise: Interactive games/questions
"""

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Optional
import enum

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
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

if TYPE_CHECKING:
    from app.models.user import User


class LearningDifficulty(str, enum.Enum):
    """Content difficulty level."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class ExerciseType(str, enum.Enum):
    """Type of interactive exercise."""
    FLASHCARD = "flashcard"
    WORD_MATCH = "word_match"
    SENTENCE_BUILDER = "sentence_builder"
    QUIZ = "quiz"
    PICTURE_WORD = "picture_word"
    VERB_CONJUGATION = "verb_conjugation"


class LearningProfile(Base):
    """
    User's learning profile and gamification stats.
    One-to-One with User.
    """
    __tablename__ = "learning_profiles"

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
        unique=True,
    )
    
    # Gamification
    total_xp: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    streak_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    current_level: Mapped[str] = mapped_column(String(50), default="Beginner", nullable=False)
    
    # Progress Counts
    vocabulary_mastered: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    grammar_concepts_completed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Activity tracking for streak
    last_activity_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
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

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="learning_profile")


class VocabularyItem(Base):
    """
    A single vocabulary word or phrase to learn.
    """
    __tablename__ = "vocabulary_items"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.uuid_generate_v4(),
        nullable=False,
    )
    
    # Content
    gujarati_word: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    english_translation: Mapped[str] = mapped_column(String(255), nullable=False)
    transliteration: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Metadata
    difficulty_level: Mapped[int] = mapped_column(Integer, default=1, nullable=False) # 1-5
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True) # e.g. 'food'
    
    # Assets
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    audio_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    example_sentence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    example_sentence_english: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class UserWordProgress(Base):
    """
    Tracks a user's progress on a specific word using SM-2 algorithm.
    """
    __tablename__ = "user_word_progress"

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
    vocabulary_item_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vocabulary_items.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # SM-2 Parameters
    next_review_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False,
        index=True
    )
    last_reviewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    interval_days: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    ease_factor: Mapped[float] = mapped_column(Float, default=2.5, nullable=False)
    repetitions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Stats
    is_mastered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __table_args__ = (
        Index("idx_word_progress_user_review", "user_id", "next_review_date"),
    )
    
    # Relationships
    vocabulary_item: Mapped["VocabularyItem"] = relationship("VocabularyItem")


class GrammarTopic(Base):
    """
    A grammar lesson/topic.
    """
    __tablename__ = "grammar_topics"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.uuid_generate_v4(),
        nullable=False,
    )
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="Markdown or HTML content")
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    difficulty: Mapped[LearningDifficulty] = mapped_column(
        Enum(LearningDifficulty, name="learning_difficulty_level"),
        default=LearningDifficulty.BEGINNER,
        nullable=False
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class Exercise(Base):
    """
    Interactive exercise question.
    """
    __tablename__ = "exercises"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.uuid_generate_v4(),
        nullable=False,
    )
    
    exercise_type: Mapped[ExerciseType] = mapped_column(
        Enum(ExerciseType, name="exercise_type"),
        nullable=False
    )
    
    # Content structure depends on type
    # e.g. Flashcard: {front: "", back: ""}
    # e.g. Quiz: {question: "", options: [], correct: 0}
    content: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    
    difficulty_level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    # Optional link to grammar topic
    grammar_topic_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("grammar_topics.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
