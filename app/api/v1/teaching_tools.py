"""
BhashaAI Backend - Teaching Tools API

Endpoints for generating Mind Maps, Lesson Plans, and Analogies.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models import User, ToolType
from app.schemas.response import APIResponse
from app.schemas.teaching_tool import (
    ToolGenerateRequest,
    TeachingToolResponse,
    ToolListResponse
)
from app.services.teaching_tool_service import TeachingToolService

router = APIRouter(prefix="/teaching-tools", tags=["Teaching Tools"])


@router.post(
    "/generate",
    response_model=APIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate Teaching Tool",
    description="Generate a Mind Map, Lesson Plan, or Analogy.",
)
async def generate_tool(
    data: ToolGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a new teaching tool.
    
    - **tool_type**: 'mind_map', 'lesson_plan', or 'analogy'
    - **topic**: Main subject matter
    """
    service = TeachingToolService(db)
    tool = await service.generate_tool(
        user_id=UUID(str(current_user.id)),
        request=data
    )
    
    return APIResponse(
        success=True,
        message=f"{data.tool_type.value.replace('_', ' ').title()} generated successfully",
        data=TeachingToolResponse.from_orm(tool)
    )


@router.get(
    "",
    response_model=APIResponse,
    summary="List Teaching Tools",
)
async def list_tools(
    type: Optional[ToolType] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List generated tools."""
    service = TeachingToolService(db)
    tools, total = await service.list_tools(
        user_id=UUID(str(current_user.id)),
        tool_type=type,
        page=page,
        per_page=per_page
    )
    
    return APIResponse(
        success=True,
        data=ToolListResponse(
            tools=[TeachingToolResponse.from_orm(t) for t in tools],
            total=total,  # Service returns 0 currently, can implement count if needed
            page=page,
            per_page=per_page,
            pages=1
        )
    )


@router.get(
    "/{tool_id}",
    response_model=APIResponse,
    summary="Get Tool Details",
)
async def get_tool(
    tool_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get specific teaching tool."""
    service = TeachingToolService(db)
    tool = await service.get_tool(tool_id, UUID(str(current_user.id)))
    
    if not tool:
        raise HTTPException(status_code=404, detail="Teaching tool not found")
        
    return APIResponse(
        success=True,
        data=TeachingToolResponse.from_orm(tool)
    )


@router.delete(
    "/{tool_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Teaching Tool",
    description="Delete a teaching tool (soft delete).",
)
async def delete_tool(
    tool_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a teaching tool."""
    service = TeachingToolService(db)
    deleted = await service.delete_tool(
        tool_id=tool_id,
        user_id=UUID(str(current_user.id)),
    )
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "message": "Teaching tool not found",
                "message_gu": "ટીચિંગ ટૂલ મળ્યું નથી",
            }
        )
    
    return
