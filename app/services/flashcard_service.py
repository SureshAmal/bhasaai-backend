"""
BhashaAI Backend - Flashcard Service

Service for managing and generating flashcards.
"""

import json
import logging
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.flashcard import Flashcard, FlashcardDeck
from app.schemas.flashcard import FlashcardDeckCreate, FlashcardGenerateRequest
from app.services.document_service import DocumentService
from app.services.llm_service import get_llm_service
from app.services.prompts import FLASHCARD_GENERATION_PROMPT, LANGUAGE_INSTRUCTIONS

logger = logging.getLogger(__name__)


class FlashcardService:
    """Service for flashcards management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_deck(self, user_id: UUID, deck_data: FlashcardDeckCreate) -> FlashcardDeck:
        """Create a new flashcard deck."""
        deck = FlashcardDeck(
            user_id=str(user_id),
            title=deck_data.title,
            description=deck_data.description,
            subject=deck_data.subject,
            is_public=deck_data.is_public,
            card_count=len(deck_data.cards),
        )
        self.db.add(deck)
        await self.db.flush()  # Get ID

        # Add initial cards
        for i, card_data in enumerate(deck_data.cards):
            card = Flashcard(
                deck_id=deck.id,
                front=card_data.front,
                back=card_data.back,
                hint=card_data.hint,
                order_index=i + 1,
            )
            self.db.add(card)

        await self.db.commit()
        
        # Re-fetch with cards loaded to avoid MissingGreenlet error
        stmt = (
            select(FlashcardDeck)
            .options(selectinload(FlashcardDeck.cards))
            .where(FlashcardDeck.id == deck.id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def get_deck(self, deck_id: UUID) -> Optional[FlashcardDeck]:
        """Get deck by ID with cards."""
        stmt = (
            select(FlashcardDeck)
            .options(selectinload(FlashcardDeck.cards))
            .where(FlashcardDeck.id == str(deck_id))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_decks(self, user_id: UUID, limit: int = 50) -> List[FlashcardDeck]:
        """List user's decks."""
        stmt = (
            select(FlashcardDeck)
            .options(selectinload(FlashcardDeck.cards))
            .where(FlashcardDeck.user_id == str(user_id))
            .order_by(FlashcardDeck.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def generate_cards(
        self, 
        request: FlashcardGenerateRequest, 
        user_id: UUID
    ) -> List[dict]:
        """
        Generate flashcards content using AI.
        Does NOT save to DB yet, returns data for preview/editing.
        """
        llm_service = get_llm_service()
        context_text = ""

        # 1. Get Context
        if request.document_id:
            doc_service = DocumentService(self.db)
            document = await doc_service.get_document(request.document_id, user_id)
            if not document:
                raise ValueError("Document not found")
            
            # Extract text
            text = await doc_service.extract_text(document)
            if not text:
                raise ValueError("Could not extract text from document")
            context_text = text[:10000] # Limit context
        
        elif request.topic:
            context_text = f"Topic: {request.topic}"
        
        else:
            raise ValueError("Either topic or document_id is required")

        # 2. Call LLM
        chain = FLASHCARD_GENERATION_PROMPT | llm_service.llm
        
        try:
            response = await chain.ainvoke({
                "topic": request.topic or "Document Content",
                "text": context_text,
                "subject": request.subject or "General",
                "grade_level": request.grade_level or "General",
                "count": request.count,
                "language_instruction": LANGUAGE_INSTRUCTIONS.get(request.language, LANGUAGE_INSTRUCTIONS["gu"])
            })
            
            # 3. Parse Response
            content = response.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1]
            
            data = json.loads(content.strip())
            cards = data.get("cards", [])
            return cards
            
        except Exception as e:
            logger.error(f"Flashcard generation failed: {e}")
            raise ValueError(f"Failed to generate flashcards: {str(e)}")
