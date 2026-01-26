"""
BhashaAI Backend - Learning API

Endpoints for:
- Learning Profile & Stats
- Vocabulary Daily Lessons
- SM-2 Progress Updates
- Audio/TTS Services
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models import User
from app.schemas.response import APIResponse
from app.schemas.learning import (
    LearningProfileResponse,
    VocabularyLessonItem,
    VocabularyProgressSubmit,
    ProgressResponse,
    TTSRequest
)
from app.services.learning_service import LearningService
from app.services.audio_service import AudioService

router = APIRouter(prefix="/learning", tags=["Learning"])


@router.get(
    "/profile",
    response_model=APIResponse[LearningProfileResponse],
    summary="Get User Profile",
)
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's learning stats and gamification profile."""
    service = LearningService(db)
    profile = await service.get_or_create_profile(current_user.id)
    return APIResponse(success=True, data=profile)


@router.get(
    "/vocabulary/daily",
    response_model=APIResponse[List[VocabularyLessonItem]],
    summary="Get Daily Vocabulary",
)
async def get_daily_vocabulary(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get today's vocabulary lesson.
    Returns a mix of 'review' items (due today) and 'new' items.
    """
    service = LearningService(db)
    items = await service.get_daily_vocabulary(current_user.id, limit=limit)
    
    # Transform to schema
    # service returns list of dicts: {'type':..., 'word': obj}
    # Pydantic will handle dict -> Schema conversion if keys match
    return APIResponse(success=True, data=items)


@router.post(
    "/vocabulary/{word_id}/progress",
    response_model=APIResponse[ProgressResponse],
    summary="Submit Word Progress",
)
async def submit_progress(
    word_id: UUID,
    data: VocabularyProgressSubmit,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit result of a vocabulary review (0-5 rating).
    Updates scheduling using SM-2 algorithm.
    """
    service = LearningService(db)
    progress = await service.update_word_progress(
        current_user.id, 
        word_id, 
        data.quality
    )
    
    return APIResponse(
        success=True, 
        data=ProgressResponse(
            vocabulary_item_id=progress.vocabulary_item_id,
            next_review_date=progress.next_review_date,
            interval_days=progress.interval_days,
            is_mastered=progress.is_mastered,
            # XP gain is hidden logic for now, could return total_xp
        )
    )


@router.post(
    "/audio/tts",
    response_model=APIResponse[dict],
    summary="Generate Audio (TTS)",
)
async def generate_audio(
    data: TTSRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate audio URL for given text (Gujarati/English)."""
    service = AudioService()
    url = await service.generate_pronunciation(data.text, lang=data.language)
    
    return APIResponse(
        success=True,
        data={"audio_url": url},
        message="Audio generated"
    )
