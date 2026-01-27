"""
BhashaAI Backend - Paper Checking API

RESTful API endpoints for automated paper checking:
- Answer Key management (CRUD)
- Paper submission and checking
- Grading results retrieval

API Flow:
1. Teacher creates an answer key with expected answers
2. Teacher uploads student papers for batch checking
3. System processes papers with OCR + AI grading
4. Results are available with question-wise feedback
"""

from typing import List, Optional
from uuid import UUID

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models import User
from app.schemas.response import APIResponse
from app.schemas.paper_checking import (
    AnswerKeyCreate,
    AnswerKeyResponse,
    AnswerKeyListItem,
    CheckedPaperResponse,
    CheckedPaperListItem,
    CheckedPaperSubmitResponse,
)
from app.services.paper_checking_service import PaperCheckingService

router = APIRouter(prefix="/paper-checking", tags=["Paper Checking"])


# =============================================================================
# Answer Key Endpoints
# =============================================================================

@router.post(
    "/answer-keys",
    response_model=APIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Answer Key",
    description="Create an answer key with expected answers, keywords, and marking scheme for grading student papers.",
)
async def create_answer_key(
    data: AnswerKeyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """
    Create a new answer key for paper checking.
    
    The answer key contains:
    - Question-wise expected answers
    - Keywords for semantic matching
    - Marking scheme configuration
    
    Args:
        data: Answer key creation data
        current_user: Authenticated user (teacher)
        db: Database session
        
    Returns:
        APIResponse with created answer key data
    """
    service = PaperCheckingService(db)
    
    try:
        answer_key = await service.create_answer_key(
            user_id=UUID(str(current_user.id)),
            data=data,
        )
        
        return APIResponse(
            success=True,
            message="Answer key created successfully",
            message_gu="જવાબ ચાવી સફળતાપૂર્વક બનાવવામાં આવી",
            data=AnswerKeyResponse.from_db(answer_key),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/answer-keys",
    response_model=APIResponse,
    summary="List Answer Keys",
    description="Retrieve all answer keys created by the current user.",
)
async def list_answer_keys(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """
    List all answer keys for the current user.
    
    Args:
        current_user: Authenticated user
        db: Database session
        
    Returns:
        APIResponse with list of answer keys
    """
    service = PaperCheckingService(db)
    answer_keys = await service.get_answer_keys_by_user(UUID(str(current_user.id)))
    
    items = [
        AnswerKeyListItem(
            id=key.id,
            title=key.title,
            subject=key.subject,
            total_marks=key.total_marks,
            total_questions=len(key.answers) if key.answers else 0,
            created_at=key.created_at,
        )
        for key in answer_keys
    ]
    
    return APIResponse(
        success=True,
        data=items,
    )


@router.get(
    "/answer-keys/{key_id}",
    response_model=APIResponse,
    summary="Get Answer Key",
    description="Retrieve a specific answer key by ID.",
)
async def get_answer_key(
    key_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """
    Get a specific answer key.
    
    Args:
        key_id: Answer key UUID
        current_user: Authenticated user
        db: Database session
        
    Returns:
        APIResponse with answer key data
        
    Raises:
        HTTPException: 404 if not found, 403 if not owner
    """
    service = PaperCheckingService(db)
    answer_key = await service.get_answer_key(key_id)
    
    if not answer_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Answer key not found",
        )
    
    # Check ownership
    if str(answer_key.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this answer key",
        )
    
    return APIResponse(
        success=True,
        data=AnswerKeyResponse.from_db(answer_key),
    )


@router.delete(
    "/answer-keys/{key_id}",
    response_model=APIResponse,
    summary="Delete Answer Key",
    description="Delete an answer key. This will also delete all checked papers associated with it.",
)
async def delete_answer_key(
    key_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """
    Delete an answer key.
    
    Args:
        key_id: Answer key UUID
        current_user: Authenticated user
        db: Database session
        
    Returns:
        APIResponse confirming deletion
    """
    service = PaperCheckingService(db)
    answer_key = await service.get_answer_key(key_id)
    
    if not answer_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Answer key not found",
        )
    
    if str(answer_key.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this answer key",
        )
    
    await service.delete_answer_key(key_id)
    
    return APIResponse(
        success=True,
        message="Answer key deleted successfully",
        message_gu="જવાબ ચાવી સફળતાપૂર્વક કાઢી નાખવામાં આવી",
    )


# =============================================================================
# Paper Check Endpoints
# =============================================================================

@router.post(
    "/paper-checks",
    response_model=APIResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit Paper for Checking",
    description="Upload a student answer paper (PDF/Image) for automated checking against an answer key.",
)
async def submit_paper_for_checking(
    background_tasks: BackgroundTasks,
    answer_key_id: UUID = Form(..., description="Answer key ID to check against"),
    file: UploadFile = File(..., description="Student answer paper (PDF or image)"),
    student_name: Optional[str] = Form(None, description="Student's name"),
    student_id: Optional[str] = Form(None, description="Student's ID or roll number"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """
    Submit a student paper for checking.
    
    The paper will be processed asynchronously:
    1. File is uploaded to storage
    2. OCR extracts text from the paper
    3. AI grades each answer against the answer key
    4. Results are stored with feedback
    
    Args:
        background_tasks: FastAPI background tasks
        answer_key_id: Answer key to grade against
        file: Uploaded paper file
        student_name: Optional student name
        student_id: Optional student ID
        current_user: Authenticated user
        db: Database session
        
    Returns:
        APIResponse with submission ID and status
    """
    # Validate file type
    allowed_types = {"application/pdf", "image/jpeg", "image/png", "image/webp"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: PDF, JPEG, PNG, WebP",
        )
    
    service = PaperCheckingService(db)
    
    # Verify answer key exists and user has access
    answer_key = await service.get_answer_key(answer_key_id)
    if not answer_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Answer key not found",
        )
    
    if str(answer_key.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to use this answer key",
        )
    
    # Save file (simplified - in production, upload to S3/MinIO)
    file_path = f"uploads/papers/{file.filename}"
    # TODO: Actually save file to storage
    # For now, just use the filename as path
    
    try:
        checked_paper = await service.submit_paper(
            user_id=UUID(str(current_user.id)),
            answer_key_id=answer_key_id,
            file_path=file_path,
            student_name=student_name,
            student_id=student_id,
        )
        
        # Trigger background processing
        background_tasks.add_task(
            service.process_paper,
            UUID(str(checked_paper.id)),
        )
        
        return APIResponse(
            success=True,
            message="Paper submitted for checking",
            message_gu="પેપર ચકાસણી માટે સબમિટ કરવામાં આવ્યું",
            data=CheckedPaperSubmitResponse(
                id=checked_paper.id,
                answer_key_id=checked_paper.answer_key_id,
                student_name=checked_paper.student_name,
                student_id=checked_paper.student_id,
                status=checked_paper.status.value,
                task_id=f"task_{checked_paper.id}",
            ),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/paper-checks/{paper_id}",
    response_model=APIResponse,
    summary="Get Check Results",
    description="Retrieve the grading results for a submitted paper.",
)
async def get_check_results(
    paper_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """
    Get grading results for a checked paper.
    
    Args:
        paper_id: Checked paper UUID
        current_user: Authenticated user
        db: Database session
        
    Returns:
        APIResponse with grading results
    """
    service = PaperCheckingService(db)
    paper = await service.get_checked_paper(paper_id)
    
    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Checked paper not found",
        )
    
    if str(paper.teacher_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access these results",
        )
    
    return APIResponse(
        success=True,
        data=CheckedPaperResponse.from_db(paper),
    )


@router.get(
    "/answer-keys/{key_id}/papers",
    response_model=APIResponse,
    summary="List Papers for Answer Key",
    description="List all student papers checked with a specific answer key.",
)
async def list_papers_for_answer_key(
    key_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """
    List all papers checked against an answer key.
    
    Args:
        key_id: Answer key UUID
        current_user: Authenticated user
        db: Database session
        
    Returns:
        APIResponse with list of checked papers
    """
    service = PaperCheckingService(db)
    
    # Verify answer key access
    answer_key = await service.get_answer_key(key_id)
    if not answer_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Answer key not found",
        )
    
    if str(answer_key.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this answer key",
        )
    
    papers = await service.list_checked_papers(key_id)
    
    items = [
        CheckedPaperListItem(
            id=paper.id,
            student_name=paper.student_name,
            student_id=paper.student_id,
            status=paper.status.value,
            obtained_marks=paper.obtained_marks,
            percentage=paper.percentage,
            grade=paper.grade,
            created_at=paper.created_at,
        )
        for paper in papers
    ]
    
    return APIResponse(
        success=True,
        data={
            "answer_key_id": str(key_id),
            "answer_key_title": answer_key.title,
            "total_papers": len(items),
            "papers": items,
        },
    )


@router.get(
    "/my-papers",
    response_model=APIResponse,
    summary="List My Checked Papers",
    description="List all papers checked by the current user.",
)
async def list_my_checked_papers(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """
    List all papers checked by the current user.
    
    Args:
        current_user: Authenticated user
        db: Database session
        
    Returns:
        APIResponse with list of checked papers
    """
    service = PaperCheckingService(db)
    papers = await service.get_user_checked_papers(UUID(str(current_user.id)))
    
    items = [
        CheckedPaperListItem(
            id=paper.id,
            student_name=paper.student_name,
            student_id=paper.student_id,
            status=paper.status.value,
            obtained_marks=paper.obtained_marks,
            percentage=paper.percentage,
            grade=paper.grade,
            created_at=paper.created_at,
        )
        for paper in papers
    ]
    
    return APIResponse(
        success=True,
        data=items,
    )
