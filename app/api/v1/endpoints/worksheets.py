"""
BhashaAI Backend - Worksheet Endpoints

API routes for gamified worksheets.
"""

from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.worksheet import (
    WorksheetGenerateRequest,
    WorksheetResponse,
    AttemptStartRequest,
    AttemptResponse,
    SubmitStepRequest,
    StepFeedback
)
from app.services.worksheet_service import WorksheetService

router = APIRouter()

@router.post("/generate", response_model=WorksheetResponse)
async def generate_worksheet(
    request: WorksheetGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Generate a new step-by-step worksheet using AI.
    """
    service = WorksheetService(db)
    try:
        worksheet = await service.generate_worksheet(current_user.id, request)
        return worksheet
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to generate worksheet")

@router.get("/", response_model=List[WorksheetResponse])
async def list_worksheets(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    List user's worksheets.
    """
    service = WorksheetService(db)
    return await service.list_worksheets(current_user.id)

@router.get("/{worksheet_id}", response_model=WorksheetResponse)
async def get_worksheet(
    worksheet_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get worksheet details.
    """
    service = WorksheetService(db)
    worksheet = await service.get_worksheet(worksheet_id)
    if not worksheet:
        raise HTTPException(status_code=404, detail="Worksheet not found")
    return worksheet

@router.delete("/{worksheet_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_worksheet(
    worksheet_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Delete a worksheet.
    """
    service = WorksheetService(db)
    success = await service.delete_worksheet(current_user.id, worksheet_id)
    if not success:
        raise HTTPException(status_code=404, detail="Worksheet not found")

# --- Game / Attempt Routes ---

@router.post("/{worksheet_id}/attempts", response_model=AttemptResponse)
async def start_attempt(
    worksheet_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Start a new attempt (game session) for a worksheet.
    """
    service = WorksheetService(db)
    # Validate worksheet exists
    worksheet = await service.get_worksheet(worksheet_id)
    if not worksheet:
        raise HTTPException(status_code=404, detail="Worksheet not found")
        
    return await service.start_attempt(current_user.id, worksheet_id)

@router.get("/attempts/{attempt_id}", response_model=AttemptResponse)
async def get_attempt(
    attempt_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get attempt state.
    """
    service = WorksheetService(db)
    attempt = await service.get_attempt(attempt_id)
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    if str(attempt.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized")
    return attempt

@router.post("/attempts/{attempt_id}/step", response_model=StepFeedback)
async def submit_step(
    attempt_id: UUID,
    request: SubmitStepRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Submit an answer for a single step.
    Returns feedback and next step info.
    """
    service = WorksheetService(db)
    # Check auth
    attempt = await service.get_attempt(attempt_id)
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    if str(attempt.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized")
        
    try:
        return await service.submit_step(attempt_id, request.step_answer)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
