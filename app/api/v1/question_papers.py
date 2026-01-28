"""
BhashaAI Backend - Question Papers API

Endpoints for question paper generation and management.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models import User
from app.schemas.question_paper import (
    GeneratePaperRequest,
    GeneratePaperResponse,
    QuestionPaperListResponse,
    QuestionPaperResponse,
    QuestionPaperUpdate,
    QuestionResponse,
)
from app.schemas.response import APIResponse
from app.services.question_paper_service import QuestionPaperService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/question-papers", tags=["Question Papers"])


@router.post(
    "/generate",
    response_model=GeneratePaperResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate Question Paper",
    description="Generate a question paper using AI from document or topic.",
)
async def generate_paper(
    request: GeneratePaperRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a question paper using AI.
    
    Provide one of:
    - **document_id**: Source document for RAG-based generation
    - **topic**: Topic for knowledge-based generation
    - **context**: Custom text for question generation
    """
    # Validate at least one source is provided
    if not request.document_id and not request.topic and not request.context:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "message": "Provide document_id, topic, or context for generation",
                "message_gu": "જનરેશન માટે document_id, topic, અથવા context આપો",
            }
        )
    
    try:
        paper_service = QuestionPaperService(db)
        paper = await paper_service.generate_paper(
            user_id=UUID(str(current_user.id)),
            request=request,
            institution_id=UUID(str(current_user.institution_id)) if current_user.institution_id else None,
        )
        
        return GeneratePaperResponse(
            data=QuestionPaperResponse(
                id=UUID(str(paper.id)),
                user_id=UUID(str(paper.user_id)),
                institution_id=UUID(str(paper.institution_id)) if paper.institution_id else None,
                document_id=UUID(str(paper.document_id)) if paper.document_id else None,
                title=paper.title,
                title_gujarati=paper.title_gujarati,
                subject=paper.subject,
                grade_level=paper.grade_level,
                total_marks=paper.total_marks,
                duration_minutes=paper.duration_minutes,
                language=paper.language,
                instructions=paper.instructions,
                instructions_gujarati=paper.instructions_gujarati,
                difficulty_distribution=paper.difficulty_distribution,
                question_type_distribution=paper.question_type_distribution,
                status=paper.status.value,
                is_active=paper.is_active,
                created_at=paper.created_at,
                updated_at=paper.updated_at,
                questions=[
                    QuestionResponse(
                        id=UUID(str(q.id)),
                        paper_id=UUID(str(q.paper_id)),
                        question_number=q.question_number,
                        question_text=q.question_text,
                        question_text_gujarati=q.question_text_gujarati,
                        question_type=q.question_type.value,
                        marks=q.marks,
                        difficulty=q.difficulty.value,
                        answer=q.answer,
                        answer_gujarati=q.answer_gujarati,
                        options=q.options,
                        correct_option=q.correct_option,
                        explanation=q.explanation,
                        bloom_level=q.bloom_level,
                        topic=q.topic,
                        keywords=q.keywords,
                        created_at=q.created_at,
                    )
                    for q in paper.questions
                ],
                question_count=len(paper.questions),
            )
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "message": str(e),
                "message_gu": str(e),
            }
        )
    except Exception as e:
        logger.error(f"Paper generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Failed to generate paper. Please try again.",
                "message_gu": "પ્રશ્નપત્ર જનરેટ કરવામાં નિષ્ફળ. કૃપા કરીને ફરી પ્રયાસ કરો.",
            }
        )


@router.get(
    "",
    response_model=APIResponse,
    summary="List Question Papers",
    description="List all question papers for the current user.",
)
async def list_papers(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    subject: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List user's question papers with pagination.
    
    - **page**: Page number
    - **per_page**: Items per page (max: 100)
    - **subject**: Filter by subject
    - **status**: Filter by status (draft, generated, published)
    - **search**: Search by title
    """
    paper_service = QuestionPaperService(db)
    papers, total = await paper_service.list_papers(
        user_id=UUID(str(current_user.id)),
        page=page,
        per_page=per_page,
        subject=subject,
        status=status,
        search=search,
    )
    
    pages = (total + per_page - 1) // per_page if per_page > 0 else 0
    
    return APIResponse(
        success=True,
        data=QuestionPaperListResponse(
            papers=[
                QuestionPaperResponse(
                    id=UUID(str(p.id)),
                    user_id=UUID(str(p.user_id)),
                    institution_id=UUID(str(p.institution_id)) if p.institution_id else None,
                    document_id=UUID(str(p.document_id)) if p.document_id else None,
                    title=p.title,
                    title_gujarati=p.title_gujarati,
                    subject=p.subject,
                    grade_level=p.grade_level,
                    total_marks=p.total_marks,
                    duration_minutes=p.duration_minutes,
                    language=p.language,
                    instructions=p.instructions,
                    instructions_gujarati=p.instructions_gujarati,
                    difficulty_distribution=p.difficulty_distribution,
                    question_type_distribution=p.question_type_distribution,
                    status=p.status.value,
                    is_active=p.is_active,
                    created_at=p.created_at,
                    updated_at=p.updated_at,
                    question_count=len(p.questions) if p.questions else 0,
                )
                for p in papers
            ],
            total=total,
            page=page,
            per_page=per_page,
            pages=pages,
        )
    )


@router.get(
    "/{paper_id}",
    response_model=APIResponse,
    summary="Get Question Paper",
    description="Get question paper details with all questions.",
)
async def get_paper(
    paper_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific question paper with all questions."""
    paper_service = QuestionPaperService(db)
    paper = await paper_service.get_paper(
        paper_id=paper_id,
        user_id=UUID(str(current_user.id)),
    )
    
    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "message": "Question paper not found",
                "message_gu": "પ્રશ્નપત્ર મળ્યું નથી",
            }
        )
    
    return APIResponse(
        success=True,
        data=QuestionPaperResponse(
            id=UUID(str(paper.id)),
            user_id=UUID(str(paper.user_id)),
            institution_id=UUID(str(paper.institution_id)) if paper.institution_id else None,
            document_id=UUID(str(paper.document_id)) if paper.document_id else None,
            title=paper.title,
            title_gujarati=paper.title_gujarati,
            subject=paper.subject,
            grade_level=paper.grade_level,
            total_marks=paper.total_marks,
            duration_minutes=paper.duration_minutes,
            language=paper.language,
            instructions=paper.instructions,
            instructions_gujarati=paper.instructions_gujarati,
            difficulty_distribution=paper.difficulty_distribution,
            question_type_distribution=paper.question_type_distribution,
            status=paper.status.value,
            is_active=paper.is_active,
            created_at=paper.created_at,
            updated_at=paper.updated_at,
            questions=[
                QuestionResponse(
                    id=UUID(str(q.id)),
                    paper_id=UUID(str(q.paper_id)),
                    question_number=q.question_number,
                    question_text=q.question_text,
                    question_text_gujarati=q.question_text_gujarati,
                    question_type=q.question_type.value,
                    marks=q.marks,
                    difficulty=q.difficulty.value,
                    answer=q.answer,
                    answer_gujarati=q.answer_gujarati,
                    options=q.options,
                    correct_option=q.correct_option,
                    explanation=q.explanation,
                    bloom_level=q.bloom_level,
                    topic=q.topic,
                    keywords=q.keywords,
                    created_at=q.created_at,
                )
                for q in paper.questions
            ],
            question_count=len(paper.questions),
        )
    )


@router.put(
    "/{paper_id}",
    response_model=APIResponse,
    summary="Update Question Paper",
    description="Update question paper details.",
)
async def update_paper(
    paper_id: UUID,
    update_data: QuestionPaperUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a question paper."""
    paper_service = QuestionPaperService(db)
    paper = await paper_service.update_paper(
        paper_id=paper_id,
        user_id=UUID(str(current_user.id)),
        update_data=update_data,
    )
    
    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "message": "Question paper not found",
                "message_gu": "પ્રશ્નપત્ર મળ્યું નથી",
            }
        )
    
    return APIResponse(
        success=True,
        message="Question paper updated successfully",
        message_gu="પ્રશ્નપત્ર સફળતાપૂર્વક અપડેટ થયું",
        data={"id": str(paper.id)},
    )


@router.delete(
    "/{paper_id}",
    response_model=APIResponse,
    summary="Delete Question Paper",
    description="Delete a question paper (soft delete).",
)
async def delete_paper(
    paper_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a question paper."""
    paper_service = QuestionPaperService(db)
    deleted = await paper_service.delete_paper(
        paper_id=paper_id,
        user_id=UUID(str(current_user.id)),
    )
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "message": "Question paper not found",
                "message_gu": "પ્રશ્નપત્ર મળ્યું નથી",
            }
        )
    
    return APIResponse(
        success=True,
        message="Question paper deleted successfully",
        message_gu="પ્રશ્નપત્ર સફળતાપૂર્વક કાઢી નાખ્યું",
    )


@router.post(
    "/{paper_id}/publish",
    response_model=APIResponse,
    summary="Publish Question Paper",
    description="Publish a question paper for use.",
)
async def publish_paper(
    paper_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Publish a question paper."""
    paper_service = QuestionPaperService(db)
    paper = await paper_service.publish_paper(
        paper_id=paper_id,
        user_id=UUID(str(current_user.id)),
    )
    
    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "message": "Question paper not found",
                "message_gu": "પ્રશ્નપત્ર મળ્યું નથી",
            }
        )
    
    return APIResponse(
        success=True,
        message="Question paper published successfully",
        message_gu="પ્રશ્નપત્ર સફળતાપૂર્વક પ્રકાશિત થયું",
        data={"id": str(paper.id), "status": paper.status.value},
    )


from fastapi.responses import StreamingResponse
from app.services.pdf_service import PDFService
import io

@router.get(
    "/{paper_id}/download",
    response_class=StreamingResponse,
    summary="Download Question Paper PDF",
    description="Download question paper as PDF with proper formatting.",
)
async def download_paper_pdf(
    paper_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate and download PDF for a question paper.
    Supporting English and Gujarati text.
    """
    # 1. Get paper details
    paper_service = QuestionPaperService(db)
    paper = await paper_service.get_paper(
        paper_id=paper_id,
        user_id=UUID(str(current_user.id)),
    )
    
    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "message": "Question paper not found",
                "message_gu": "પ્રશ્નપત્ર મળ્યું નથી",
            }
        )
    
    # 2. Generate PDF
    try:
        pdf_service = PDFService()
        pdf_bytes = pdf_service.generate_question_paper(paper)
        
        # 3. Stream response
        # Use safe ASCII filename to avoid header encoding errors
        safe_filename = f"paper_{str(paper.id)[:8]}.pdf"
        
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={safe_filename}"}
        )
    except Exception as e:
        import traceback
        with open("pdf_debug_error.log", "w") as f:
            f.write(f"Error: {str(e)}\n\n")
            traceback.print_exc(file=f)
            
        logger.error(f"PDF generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Failed to generate PDF",
                "message_gu": "PDF જનરેટ કરવામાં નિષ્ફળ",
            }
        )
