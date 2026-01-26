"""
BhashaAI Backend - Learning Service

Core logic for the Learning Module:
- Spaced Repetition Algorithm (SM-2)
- Vocabulary Lesson Management
- Gamification (Streaks, XP)
"""

import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID
from typing import List, Optional

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.learning import (
    LearningProfile, 
    VocabularyItem, 
    UserWordProgress, 
    GrammarTopic,
    Exercise
)
from app.models.user import User

logger = logging.getLogger(__name__)


class LearningService:
    """Service for managing the learning process."""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_profile(self, user_id: UUID) -> LearningProfile:
        """Get user profile or create if not exists."""
        stmt = select(LearningProfile).where(LearningProfile.user_id == str(user_id))
        result = await self.db.execute(stmt)
        profile = result.scalar_one_or_none()
        
        if not profile:
            profile = LearningProfile(user_id=str(user_id))
            self.db.add(profile)
            await self.db.commit()
            await self.db.refresh(profile)
            
        return profile

    async def get_daily_vocabulary(self, user_id: UUID, limit: int = 10) -> List[dict]:
        """
        Get words to learn today:
        1. Words due for review (SM-2 scheduled)
        2. New words (if review count < limit)
        """
        now = datetime.now(timezone.utc)
        
        # 1. Fetch Review Items
        # Words where next_review_date <= now
        review_stmt = (
            select(UserWordProgress)
            .options(selectinload(UserWordProgress.vocabulary_item))
            .where(
                UserWordProgress.user_id == str(user_id),
                UserWordProgress.next_review_date <= now
            )
            .limit(limit)
        )
        review_result = await self.db.execute(review_stmt)
        reviews = review_result.scalars().all()
        
        items = []
        for r in reviews:
            items.append({
                "type": "review",
                "progress_id": r.id,
                "word": r.vocabulary_item
            })
            
        # 2. Fetch New Items if we have space
        remaining = limit - len(items)
        if remaining > 0:
            # Subquery to find IDs user has already started
            subquery = select(UserWordProgress.vocabulary_item_id).where(
                UserWordProgress.user_id == str(user_id)
            )
            
            # Select words NOT in progress
            new_stmt = (
                select(VocabularyItem)
                .where(VocabularyItem.id.not_in(subquery))
                .order_by(VocabularyItem.difficulty_level, func.random()) # Simple curriculum logic
                .limit(remaining)
            )
            new_result = await self.db.execute(new_stmt)
            new_words = new_result.scalars().all()
            
            for w in new_words:
                items.append({
                    "type": "new",
                    "progress_id": None, 
                    "word": w
                })
                
        return items

    async def update_word_progress(self, user_id: UUID, word_id: UUID, quality: int) -> UserWordProgress:
        """
        Apply SM-2 Algorithm to update word progress.
        
        Args:
            quality: 0-5 rating (0=blackout, 3=pass, 5=perfect)
        """
        # Fetch existing progress
        stmt = select(UserWordProgress).where(
            UserWordProgress.user_id == str(user_id),
            UserWordProgress.vocabulary_item_id == str(word_id)
        )
        result = await self.db.execute(stmt)
        progress = result.scalar_one_or_none()
        
        if not progress:
            # Initialize new progress
            progress = UserWordProgress(
                user_id=str(user_id),
                vocabulary_item_id=str(word_id),
                ease_factor=2.5,
                interval_days=0,
                repetitions=0
            )
            self.db.add(progress)
        
        # SuperMemo-2 Strategy
        if quality >= 3:
            # Correct response
            if progress.repetitions == 0:
                progress.interval_days = 1
            elif progress.repetitions == 1:
                progress.interval_days = 6
            else:
                progress.interval_days = progress.interval_days * progress.ease_factor
            
            progress.repetitions += 1
            progress.is_mastered = (progress.repetitions > 5)
        else:
            # Incorrect response
            progress.repetitions = 0
            progress.interval_days = 1
            
        # Update Ease Factor
        # EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
        progress.ease_factor = progress.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        if progress.ease_factor < 1.3:
            progress.ease_factor = 1.3
            
        # Schedule next review
        now = datetime.now(timezone.utc)
        progress.last_reviewed_at = now
        progress.next_review_date = now + timedelta(days=progress.interval_days)
        
        # Update Profile (Activity & XP)
        await self._update_profile_activity(user_id, quality)
        
        await self.db.commit()
        await self.db.refresh(progress)
        return progress

    async def _update_profile_activity(self, user_id: UUID, quality: int):
        """Update streak and XP."""
        profile = await self.get_or_create_profile(user_id)
        now = datetime.now(timezone.utc)
        
        # XP Calculation
        # Quality 3-5 gives 10-15 XP
        xp_gain = quality * 3 if quality >= 3 else 1
        profile.total_xp += xp_gain
        
        # Streak Calculation
        # Check if last activity was "yesterday" (naive check) or today
        # For hackathon simple logic: if diff > 24h reset, if diff < 24h ok
        # Ideally check calendar days
        
        last_date = profile.last_activity_date.date()
        today = now.date()
        
        if last_date == today - timedelta(days=1):
            profile.streak_days += 1
        elif last_date < today - timedelta(days=1):
            profile.streak_days = 1 # Reset
        elif last_date == today:
            pass # Already active today
        else:
             profile.streak_days = 1 # First ever
             
        profile.last_activity_date = now
        self.db.add(profile)
