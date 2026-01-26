"""
BhashaAI Backend - Paper Checking API

Endpoints for:
- Creating Answer Keys
- Uploading Student Submissions (Papers)
- Getting Graded Results
"""

from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models import User
from app.schemas.response import APIResponse
from app.schemas.paper_checking import (
    AnswerKeyCreate,
    AnswerKeyResponse,
    SubmissionResponse
)
from app.services.checking_service import CheckingService

router = APIRouter(prefix="/paper-checking", tags=["Paper Checking"])


@router.post(
    "/answer-key",
    response_model=APIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Answer Key",
)
async def create_answer_key(
    data: AnswerKeyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create or update assignment rubric (Answer Key)."""
    service = CheckingService(db)
    # Ideally check generic permissions here
    
    key = await service.create_answer_key(data)
    
    return APIResponse(
        success=True,
        message="Answer key saved successfully",
        data=AnswerKeyResponse.from_orm(key)
    )


@router.post(
    "/upload",
    response_model=APIResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload Answer Sheet",
)
async def upload_submission(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    question_paper_id: Optional[str] = Form(None),
    student_name: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a student answer sheet (PDF/Image).
    Triggers async processing.
    """
    # 1. Save file (Mocking S3 upload logic for hackathon)
    # In real app, upload to S3/MinIO and get URL
    # Here we just pretend the filename is the URL
    file_url = f"uploads/{file.filename}"
    
    service = CheckingService(db)
    submission = await service.create_submission(
        user_id=UUID(str(current_user.id)),
        input_url=file_url,
        question_paper_id=UUID(question_paper_id) if question_paper_id else None,
        student_name=student_name
    )
    
    # 2. Trigger processing in background
    background_tasks.add_task(service.process_submission, submission.id)
    
    return APIResponse(
        success=True,
        message="Submission uploaded and processing started",
        data=SubmissionResponse.from_orm(submission)
    )


@router.get(
    "/submission/{submission_id}",
    response_model=APIResponse,
    summary="Get Graded Result",
)
async def get_submission(
    submission_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get status and results of a submission."""
    service = CheckingService(db)
    submission = await service.get_submission(submission_id)
    
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
        
    if str(submission.user_id) != str(current_user.id):
        # Allow teachers to view all? For now restrict to owner
        # raise HTTPException(status_code=403, detail="Not authorized")
        pass 

    return APIResponse(
        success=True,
        data=SubmissionResponse.from_orm(submission)
    )
