"""
BhashaAI Backend - Flashcard API

Endpoints for flashcard management and generation.
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.flashcard import (
    FlashcardDeckCreate,
    FlashcardDeckResponse,
    FlashcardGenerateRequest,
    FlashcardCreate,
)
from app.schemas.response import APIResponse
from app.services.flashcard_service import FlashcardService

router = APIRouter(prefix="/flashcards", tags=["Flashcards"])


@router.post(
    "/generate",
    response_model=APIResponse,
    summary="Generate Flashcards",
    description="Generate flashcard content from topic or document using AI.",
)
async def generate_flashcards(
    request: FlashcardGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate flashcards (preview mode)."""
    service = FlashcardService(db)
    try:
        cards = await service.generate_cards(request, UUID(str(current_user.id)))
        return APIResponse(
            success=True,
            data=cards,
            message="Flashcards generated successfully"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "",
    response_model=APIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Deck",
    description="Create a new flashcard deck.",
)
async def create_deck(
    deck_data: FlashcardDeckCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new deck."""
    service = FlashcardService(db)
    deck = await service.create_deck(UUID(str(current_user.id)), deck_data)
    
    return APIResponse(
        success=True,
        data=FlashcardDeckResponse.model_validate(deck),
        message="Deck created successfully"
    )


@router.get(
    "",
    response_model=APIResponse,
    summary="List Decks",
    description="List user's flashcard decks.",
)
async def list_decks(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List decks."""
    service = FlashcardService(db)
    decks = await service.list_decks(UUID(str(current_user.id)), limit)
    
    return APIResponse(
        success=True,
        data=[FlashcardDeckResponse.model_validate(d) for d in decks]
    )


@router.get(
    "/{deck_id}",
    response_model=APIResponse,
    summary="Get Deck",
    description="Get deck details and cards.",
)
async def get_deck(
    deck_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get specific deck."""
    service = FlashcardService(db)
    deck = await service.get_deck(deck_id)
    
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
        
    return APIResponse(
        success=True,
        data=FlashcardDeckResponse.model_validate(deck)
    )
