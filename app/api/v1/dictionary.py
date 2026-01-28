"""
BhashaAI Backend - Dictionary API

Endpoints for the bilingual English-Gujarati dictionary:
- POST /dictionary/lookup - Lookup/translate a word
- GET /dictionary/history - User's search history
- GET /dictionary/popular - Trending words
- GET /dictionary/{entry_id} - Get cached entry by ID
- DELETE /dictionary/history/{id} - Remove history item
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models import User
from app.schemas.response import APIResponse
from app.schemas.dictionary import (
    DictionaryLookupRequest,
    DictionaryEntryResponse,
    SearchHistoryResponse,
    SearchHistoryItem,
)
from app.services.dictionary_service import DictionaryService

router = APIRouter(prefix="/dictionary", tags=["Dictionary"])


@router.post(
    "/lookup",
    response_model=APIResponse[DictionaryEntryResponse],
    status_code=status.HTTP_200_OK,
    summary="Lookup/Translate Word",
    description="Lookup a word in the bilingual dictionary. Returns cached result or generates translation via LLM.",
)
async def lookup_word(
    request: DictionaryLookupRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Lookup a word and get translation, meaning, and examples.
    
    The word is first checked in the cache. If not found, 
    an LLM-powered translation is generated and cached.
    
    Args:
        request: Word and translation direction
        
    Returns:
        Complete dictionary entry with translation, meaning,
        part of speech, examples, synonyms, and antonyms.
    """
    service = DictionaryService(db)
    
    try:
        entry = await service.lookup_word(
            request=request,
            user_id=current_user.id,
        )
        
        return APIResponse(
            success=True,
            data=DictionaryEntryResponse.model_validate(entry),
            message="Word found"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Translation failed: {str(e)}"
        )


# IMPORTANT: Static routes MUST come BEFORE dynamic routes like /{entry_id}

@router.get(
    "/history",
    response_model=APIResponse[SearchHistoryResponse],
    summary="Get Search History",
    description="Get user's word lookup history.",
)
async def get_history(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the current user's word lookup history.
    
    Returns a paginated list of recently looked up words,
    ordered by most recent first.
    
    Args:
        page: Page number (1-indexed)
        per_page: Items per page (max 100)
        
    Returns:
        Paginated search history
    """
    service = DictionaryService(db)
    offset = (page - 1) * per_page
    
    items, total = await service.get_user_history(
        user_id=current_user.id,
        limit=per_page,
        offset=offset,
    )
    
    return APIResponse(
        success=True,
        data=SearchHistoryResponse(
            items=items,
            total=total,
            page=page,
            per_page=per_page,
        )
    )


@router.delete(
    "/history/{history_id}",
    response_model=APIResponse[dict],
    summary="Delete History Item",
    description="Remove a word from search history.",
)
async def delete_history_item(
    history_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Remove a specific word from the user's search history.
    
    Args:
        history_id: UUID of the history item to delete
        
    Returns:
        Success message
        
    Raises:
        404: History item not found
    """
    service = DictionaryService(db)
    deleted = await service.delete_history_item(
        user_id=current_user.id,
        history_id=history_id,
    )
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="History item not found"
        )
    
    return APIResponse(
        success=True,
        data={"deleted": True},
        message="History item removed"
    )


@router.get(
    "/popular",
    response_model=APIResponse[list[DictionaryEntryResponse]],
    summary="Get Popular Words",
    description="Get most frequently looked up words.",
)
async def get_popular_words(
    limit: int = Query(10, ge=1, le=50, description="Number of words"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the most popular dictionary entries.
    
    Returns words sorted by lookup count, useful for
    showing trending or commonly searched terms.
    
    Args:
        limit: Number of words to return (max 50)
        
    Returns:
        List of popular dictionary entries
    """
    service = DictionaryService(db)
    entries = await service.get_popular_words(limit=limit)
    
    return APIResponse(
        success=True,
        data=[DictionaryEntryResponse.model_validate(e) for e in entries]
    )


# Dynamic route MUST come LAST to avoid matching static paths

@router.get(
    "/{entry_id}",
    response_model=APIResponse[DictionaryEntryResponse],
    summary="Get Dictionary Entry",
    description="Get a cached dictionary entry by ID.",
)
async def get_entry(
    entry_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific dictionary entry by its ID.
    
    Args:
        entry_id: UUID of the dictionary entry
        
    Returns:
        The dictionary entry if found
        
    Raises:
        404: Entry not found
    """
    service = DictionaryService(db)
    entry = await service.get_entry_by_id(entry_id)
    
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dictionary entry not found"
        )
    
    return APIResponse(
        success=True,
        data=DictionaryEntryResponse.model_validate(entry)
    )
