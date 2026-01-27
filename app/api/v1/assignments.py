"""
BhashaAI Backend - Assignments API

Endpoints for assignment submission and interaction.
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models import User
from app.schemas.assignment import (
    AssignmentListResponse,
    AssignmentResponse,
    AssignmentCreate,
    AssignmentSubmit,
    HintRequest,
    HintResponse,
)
from app.schemas.response import APIResponse
from app.services.assignment_service import AssignmentService

router = APIRouter(prefix="/assignments", tags=["Assignments"])


@router.post(
    "/submit",
    response_model=APIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit Assignment",
    description="Submit a question for solution or help.",
)
async def submit_assignment(
    data: AssignmentSubmit,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit an assignment question.
    
    - **mode**: 'solve' for AI solution, 'help' for Socratic hints
    - **input_type**: text (others to follow)
    """
    service = AssignmentService(db)
    assignment = await service.create_assignment(
        user_id=UUID(str(current_user.id)),
        data=data
    )
    
    # Reload with relations
    assignment = await service.get_assignment(assignment.id, current_user.id)
    
    return APIResponse(
        success=True,
        message="Assignment submitted successfully",
        data=AssignmentResponse.from_orm_with_details(assignment)
    )


@router.post(
    "",
    response_model=APIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Assignment",
    description="Publish a question paper as an assignment.",
)
async def create_assignment(
    data: AssignmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new assignment (Teacher only).
    """
    service = AssignmentService(db)
    assignment = await service.create_assignment(
        user_id=UUID(str(current_user.id)),
        data=data 
    )
    assignment = await service.get_assignment(assignment.id, current_user.id)
    
    return APIResponse(
        success=True,
        message="Assignment created successfully",
        data=AssignmentResponse.from_orm_with_details(assignment)
    )


@router.get(
    "",
    response_model=APIResponse,
    summary="List Assignments",
)
async def list_assignments(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's assignments."""
    service = AssignmentService(db)
    assignments, total = await service.list_assignments(
        user_id=UUID(str(current_user.id)),
        page=page,
        per_page=per_page,
        status=status,
        search=search,
    )
    
    return APIResponse(
        success=True,
        data=AssignmentListResponse(
            assignments=[
                AssignmentResponse.from_orm_with_details(a) 
                for a in assignments
            ],
            total=total,
            page=page,
            per_page=per_page,
            pages=(total + per_page - 1) // per_page if per_page > 0 else 0
        )
    )


@router.get(
    "/{assignment_id}",
    response_model=APIResponse,
    summary="Get Assignment Details",
)
async def get_assignment(
    assignment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get assignment details including solution/help session."""
    service = AssignmentService(db)
    assignment = await service.get_assignment(assignment_id, UUID(str(current_user.id)))
    
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
        
    return APIResponse(
        success=True,
        data=AssignmentResponse.from_orm_with_details(assignment)
    )


@router.post(
    "/{assignment_id}/hint",
    response_model=APIResponse,
    summary="Get Next Hint",
)
async def get_hint(
    assignment_id: UUID,
    data: HintRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get next hint for a help session.
    Only valid if assignment mode is 'help'.
    """
    service = AssignmentService(db)
    assignment = await service.get_assignment(assignment_id, UUID(str(current_user.id)))
    
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
        
    if not assignment.help_session:
        # Lazy initialization for existing assignments
        await service.start_help_session(assignment)
        # Reload to get session
        assignment = await service.get_assignment(assignment_id, UUID(str(current_user.id)))
        
        if not assignment or not assignment.help_session:
            raise HTTPException(status_code=500, detail="Failed to initialize help session")
        
    hint_data = await service.generate_hint(
        session=assignment.help_session,
        assignment=assignment,
        student_response=data.student_response,
        request_next_level=data.request_next_level
    )
    
    return APIResponse(
        success=True,
        data=HintResponse(
            hint=hint_data.get("hint", ""),
            hint_level=hint_data.get("level", 0),
            is_completed=hint_data.get("is_complete", False),
            explanation=hint_data.get("explanation")
        )
    )


@router.delete(
    "/{assignment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Assignment",
    description="Delete an assignment (soft delete).",
)
async def delete_assignment(
    assignment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an assignment."""
    service = AssignmentService(db)
    deleted = await service.delete_assignment(
        assignment_id=assignment_id,
        user_id=UUID(str(current_user.id)),
    )
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "message": "Assignment not found",
                "message_gu": "એસાઇનમેન્ટ મળ્યું નથી",
            }
        )
    
    return
