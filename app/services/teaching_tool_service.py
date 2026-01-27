"""
BhashaAI Backend - Teaching Tool Service

Generates educational content like mind maps, lesson plans, and analogies.
"""

import json
import logging
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import TeachingTool, ToolType
from app.schemas.teaching_tool import ToolGenerateRequest
from app.services.llm_service import get_llm_service
from app.services.prompts import (
    MIND_MAP_PROMPT,
    LESSON_PLAN_PROMPT,
    ANALOGY_PROMPT,
    LANGUAGE_INSTRUCTIONS,
)

logger = logging.getLogger(__name__)


class TeachingToolService:
    """Service for generating and managing teaching tools."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm = get_llm_service()
        
    async def generate_tool(
        self, 
        user_id: UUID, 
        request: ToolGenerateRequest
    ) -> TeachingTool:
        """
        Generate a teaching tool based on request type.
        """
        prompt_map = {
            ToolType.MIND_MAP: self._generate_mind_map,
            ToolType.LESSON_PLAN: self._generate_lesson_plan,
            ToolType.ANALOGY: self._generate_analogy,
        }
        
        generator = prompt_map.get(request.tool_type)
        if not generator:
            raise ValueError(f"Unsupported tool type: {request.tool_type}")
            
        # Generate generic tool record
        tool = TeachingTool(
            user_id=str(user_id),
            tool_type=request.tool_type,
            topic=request.topic,
            subject=request.subject,
            grade_level=request.grade_level,
            language=request.language,
            content={},  # Will be populated
            is_active=True
        )
        
        try:
            content = await generator(request)
            tool.content = content
            
            self.db.add(tool)
            await self.db.commit()
            await self.db.refresh(tool)
            
            return tool
            
        except Exception as e:
            logger.error(f"Tool generation failed: {e}")
            raise
            
    async def _generate_mind_map(self, request: ToolGenerateRequest) -> dict:
        """Generate JSON structure for mind map."""
        lang_instruction = LANGUAGE_INSTRUCTIONS.get(request.language, LANGUAGE_INSTRUCTIONS["gu"])
        
        chain = MIND_MAP_PROMPT | self.llm.llm
        
        response = await chain.ainvoke({
            "topic": request.topic,
            "subject": request.subject or "General",
            "grade_level": request.grade_level or "General",
            "language_instruction": lang_instruction
        })
        
        return self._parse_json(response.content)

    async def _generate_lesson_plan(self, request: ToolGenerateRequest) -> dict:
        """Generate structured lesson plan."""
        lang_instruction = LANGUAGE_INSTRUCTIONS.get(request.language, LANGUAGE_INSTRUCTIONS["gu"])
        
        chain = LESSON_PLAN_PROMPT | self.llm.llm
        
        response = await chain.ainvoke({
            "topic": request.topic,
            "subject": request.subject or "General",
            "grade_level": request.grade_level or "General",
            "duration": "45 minutes",  # Default
            "language_instruction": lang_instruction
        })
        
        return self._parse_json(response.content)

    async def _generate_analogy(self, request: ToolGenerateRequest) -> dict:
        """Generate concept analogy."""
        lang_instruction = LANGUAGE_INSTRUCTIONS.get(request.language, LANGUAGE_INSTRUCTIONS["gu"])
        
        chain = ANALOGY_PROMPT | self.llm.llm
        
        response = await chain.ainvoke({
            "topic": request.topic,
            "subject": request.subject or "General",
            "grade_level": request.grade_level or "General",
            "language_instruction": lang_instruction
        })
        
        return self._parse_json(response.content)
        
    def _parse_json(self, content: str) -> dict:
        """Helper to parse LLM JSON response."""
        content = content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        if content.endswith("```"):
            content = content[:-3]
        return json.loads(content.strip())

    async def list_tools(
        self, 
        user_id: UUID, 
        tool_type: Optional[ToolType] = None,
        page: int = 1, 
        per_page: int = 20
    ) -> tuple[list[TeachingTool], int]:
        """List user's tools."""
        stmt = select(TeachingTool).where(
            TeachingTool.user_id == str(user_id),
            TeachingTool.is_active == True,
        )
        
        if tool_type:
            stmt = stmt.where(TeachingTool.tool_type == tool_type)
            
        stmt = stmt.order_by(TeachingTool.created_at.desc())
        
        # Paginate
        offset = (page - 1) * per_page
        result = await self.db.execute(stmt.offset(offset).limit(per_page))
        return result.scalars().all(), 0  # Total count skipped for brevity
    
    async def get_tool(self, tool_id: UUID, user_id: UUID) -> Optional[TeachingTool]:
        """Get specific tool."""
        stmt = select(TeachingTool).where(
            TeachingTool.id == str(tool_id),
            TeachingTool.user_id == str(user_id),
            TeachingTool.is_active == True,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_tool(self, tool_id: UUID, user_id: UUID) -> bool:
        """Soft delete a teaching tool."""
        tool = await self.get_tool(tool_id, user_id)
        if not tool:
            return False
            
        tool.is_active = False
        await self.db.commit()
        
        logger.info(f"Teaching tool deleted: {tool_id}")
        return True
