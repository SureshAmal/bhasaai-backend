"""
BhashaAI Backend - Flashcard Models

Models for user-created flashcard decks and cards.
"""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User


from sqlalchemy.dialects.postgresql import UUID

class FlashcardDeck(Base):
    """
    A collection of flashcards (Flashcard Deck).
    Owned by a user.
    """
    __tablename__ = "flashcard_decks"

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
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    subject: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Metadata
    card_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
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
    user: Mapped["User"] = relationship("User", backref="flashcard_decks")
    cards: Mapped[List["Flashcard"]] = relationship(
        "Flashcard", 
        back_populates="deck", 
        cascade="all, delete-orphan",
        order_by="Flashcard.order_index"
    )


class Flashcard(Base):
    """
    A single flashcard.
    """
    __tablename__ = "flashcards"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.uuid_generate_v4(),
        nullable=False,
    )
    
    deck_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("flashcard_decks.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Content
    front: Mapped[str] = mapped_column(Text, nullable=False, comment="Question or Term")
    back: Mapped[str] = mapped_column(Text, nullable=False, comment="Answer or Definition")
    hint: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Ordering
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    deck: Mapped["FlashcardDeck"] = relationship("FlashcardDeck", back_populates="cards")
