"""
BhashaAI Backend - Dictionary Service

Service layer for bilingual English-Gujarati dictionary operations:
- Word lookup with caching
- LLM-powered translations
- User history tracking

This service:
1. Checks cache (database) for existing translations
2. Falls back to LLM for new translations
3. Caches LLM results for future lookups
4. Tracks user search history
"""

import json
import logging
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dictionary import DictionaryEntry, UserDictionaryHistory
from app.models.enums import PartOfSpeech, TranslationDirection
from app.schemas.dictionary import (
    DictionaryLookupRequest,
    DictionaryEntryResponse,
    TranslationResult,
    SearchHistoryItem,
)
from app.services.llm_service import get_llm_service
from app.services.prompts import DICTIONARY_TRANSLATION_PROMPT, LANGUAGE_INSTRUCTIONS

logger = logging.getLogger(__name__)


class DictionaryService:
    """
    Service for bilingual dictionary operations.
    
    Provides:
    - Word lookup with automatic caching
    - LLM-powered translations
    - User history tracking
    
    Attributes:
        db: AsyncSession for database operations
        llm: LLM service for translations
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize the dictionary service.
        
        Args:
            db: AsyncSession for database operations
        """
        self.db = db
        self.llm = get_llm_service()
    
    async def lookup_word(
        self,
        request: DictionaryLookupRequest,
        user_id: Optional[UUID] = None,
    ) -> DictionaryEntry:
        """
        Lookup a word, fetching from cache or translating via LLM.
        
        Args:
            request: Lookup request with word and direction
            user_id: Optional user ID for history tracking
            
        Returns:
            DictionaryEntry: The dictionary entry (cached or newly created)
            
        Raises:
            ValueError: If translation fails
        """
        word = request.word.lower().strip()
        source_language = "en" if request.direction == TranslationDirection.EN_TO_GU else "gu"
        
        # 1. Check cache
        cached_entry = await self._get_cached_entry(word, source_language)
        
        if cached_entry:
            logger.info(f"Cache hit for word: {word}")
            # Increment lookup count
            cached_entry.lookup_count += 1
            await self.db.commit()
            
            # Track history if user provided
            if user_id:
                await self._add_to_history(user_id, cached_entry.id)
            
            return cached_entry
        
        # 2. Translate via LLM
        logger.info(f"Cache miss for word: {word}, translating via LLM")
        translation_result = await self._translate_with_llm(word, request.direction)
        
        # 3. Create and cache entry
        entry = await self._create_entry(
            word=word,
            language=source_language,
            result=translation_result,
        )
        
        # 4. Track history if user provided
        if user_id:
            await self._add_to_history(user_id, entry.id)
        
        return entry
    
    async def _get_cached_entry(
        self,
        word: str,
        language: str,
    ) -> Optional[DictionaryEntry]:
        """
        Get a cached dictionary entry.
        
        Args:
            word: Word to lookup (lowercase)
            language: Source language ('en' or 'gu')
            
        Returns:
            DictionaryEntry or None
        """
        stmt = select(DictionaryEntry).where(
            and_(
                func.lower(DictionaryEntry.word) == word.lower(),
                DictionaryEntry.language == language
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def _translate_with_llm(
        self,
        word: str,
        direction: TranslationDirection,
    ) -> TranslationResult:
        """
        Use LLM to translate and get full dictionary entry.
        
        Args:
            word: Word to translate
            direction: Translation direction
            
        Returns:
            TranslationResult with all dictionary fields
            
        Raises:
            ValueError: If LLM response parsing fails
        """
        direction_text = "English to Gujarati" if direction == TranslationDirection.EN_TO_GU else "Gujarati to English"
        
        # Build LangChain chain
        chain = DICTIONARY_TRANSLATION_PROMPT | self.llm.llm
        
        try:
            response = await chain.ainvoke({
                "word": word,
                "direction": direction_text,
                "language_instruction": LANGUAGE_INSTRUCTIONS.get("gu-en", ""),
            })
            
            # Parse JSON response
            content = response.content.strip()
            
            # Clean markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1]
            
            data = json.loads(content.strip())
            
            # Validate and create TranslationResult
            result = TranslationResult(
                translation=data.get("translation", ""),
                transliteration=data.get("transliteration"),
                part_of_speech=data.get("part_of_speech", "noun"),
                meaning=data.get("meaning", ""),
                meaning_gujarati=data.get("meaning_gujarati"),
                example_sentence=data.get("example_sentence"),
                example_sentence_translation=data.get("example_sentence_translation"),
                synonyms=data.get("synonyms", []),
                antonyms=data.get("antonyms", []),
                confidence=data.get("confidence", 0.9),
            )
            
            logger.info(f"LLM translation successful for: {word}")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {e}")
            raise ValueError(f"Failed to parse translation response: {e}")
        except Exception as e:
            logger.error(f"LLM translation failed: {e}")
            raise ValueError(f"Translation failed: {e}")
    
    async def _create_entry(
        self,
        word: str,
        language: str,
        result: TranslationResult,
    ) -> DictionaryEntry:
        """
        Create and cache a new dictionary entry.
        
        Args:
            word: Original word
            language: Source language
            result: LLM translation result
            
        Returns:
            DictionaryEntry: The created entry
        """
        # Map part_of_speech string to enum
        try:
            pos = PartOfSpeech(result.part_of_speech.lower())
        except ValueError:
            pos = PartOfSpeech.NOUN
        
        entry = DictionaryEntry(
            word=word,
            language=language,
            translation=result.translation,
            transliteration=result.transliteration,
            part_of_speech=pos,
            meaning=result.meaning,
            meaning_gujarati=result.meaning_gujarati,
            example_sentence=result.example_sentence,
            example_sentence_translation=result.example_sentence_translation,
            synonyms=result.synonyms or [],
            antonyms=result.antonyms or [],
            lookup_count=1,
        )
        
        self.db.add(entry)
        await self.db.commit()
        await self.db.refresh(entry)
        
        logger.info(f"Created dictionary entry: {entry.id} for word: {word}")
        return entry
    
    async def get_entry_by_id(self, entry_id: UUID) -> Optional[DictionaryEntry]:
        """
        Get a cached dictionary entry by ID.
        
        Args:
            entry_id: Entry UUID
            
        Returns:
            DictionaryEntry or None
        """
        stmt = select(DictionaryEntry).where(DictionaryEntry.id == str(entry_id))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def _add_to_history(
        self,
        user_id: UUID,
        entry_id: UUID,
    ) -> None:
        """
        Track user lookup in history.
        
        Args:
            user_id: User's UUID
            entry_id: Dictionary entry UUID
        """
        try:
            # Check if already in history
            stmt = select(UserDictionaryHistory).where(
                and_(
                    UserDictionaryHistory.user_id == str(user_id),
                    UserDictionaryHistory.dictionary_entry_id == str(entry_id)
                )
            )
            result = await self.db.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if existing:
                # Update existing
                existing.lookup_count += 1
                existing.last_looked_up = func.now()
            else:
                # Create new
                history = UserDictionaryHistory(
                    user_id=str(user_id),
                    dictionary_entry_id=str(entry_id),
                    lookup_count=1,
                )
                self.db.add(history)
            
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to add to history: {e}")
            # Don't raise - history is non-critical
    
    async def get_user_history(
        self,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[List[SearchHistoryItem], int]:
        """
        Get user's recent word lookups.
        
        Args:
            user_id: User's UUID
            limit: Max items to return
            offset: Pagination offset
            
        Returns:
            Tuple of (list of history items, total count)
        """
        # Count total
        count_stmt = select(func.count()).select_from(UserDictionaryHistory).where(
            UserDictionaryHistory.user_id == str(user_id)
        )
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar()
        
        # Get items with joined entry data
        stmt = (
            select(UserDictionaryHistory)
            .where(UserDictionaryHistory.user_id == str(user_id))
            .order_by(UserDictionaryHistory.last_looked_up.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        history_items = result.scalars().all()
        
        # Load entry data and build response
        items = []
        for h in history_items:
            entry = await self.get_entry_by_id(h.dictionary_entry_id)
            if entry:
                items.append(SearchHistoryItem(
                    id=h.id,
                    word=entry.word,
                    translation=entry.translation,
                    part_of_speech=entry.part_of_speech.value,
                    lookup_count=h.lookup_count,
                    last_looked_up=h.last_looked_up,
                ))
        
        return items, total
    
    async def delete_history_item(
        self,
        user_id: UUID,
        history_id: UUID,
    ) -> bool:
        """
        Remove an item from user's history.
        
        Args:
            user_id: User's UUID
            history_id: History item UUID
            
        Returns:
            True if deleted, False if not found
        """
        stmt = select(UserDictionaryHistory).where(
            and_(
                UserDictionaryHistory.id == str(history_id),
                UserDictionaryHistory.user_id == str(user_id)
            )
        )
        result = await self.db.execute(stmt)
        item = result.scalar_one_or_none()
        
        if not item:
            return False
        
        await self.db.delete(item)
        await self.db.commit()
        
        logger.info(f"Deleted history item: {history_id} for user: {user_id}")
        return True
    
    async def get_popular_words(self, limit: int = 10) -> List[DictionaryEntry]:
        """
        Get most frequently looked up words.
        
        Args:
            limit: Number of words to return
            
        Returns:
            List of popular dictionary entries
        """
        stmt = (
            select(DictionaryEntry)
            .order_by(DictionaryEntry.lookup_count.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
