"""
BhashaAI Backend - Assignment Service

Handles assignment submission, solution generation, and Socratic help sessions.
"""

import json
import logging
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Assignment,
    AssignmentSolution,
    HelpSession,
    AssignmentMode,
    ProcessingStatus,
    DifficultyLevel,
)
from app.schemas.assignment import AssignmentSubmit
from app.services.llm_service import get_llm_service
from app.services.prompts import (
    SOLUTION_GENERATION_PROMPT,
    SOCRATIC_HINT_PROMPT,
    LANGUAGE_INSTRUCTIONS,
)

logger = logging.getLogger(__name__)


class AssignmentService:
    """
    Service for assignment management and AI interaction.
    """
    
    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db
        self.llm = get_llm_service()
    
    async def create_assignment(
        self,
        user_id: UUID,
        data: AssignmentSubmit,
    ) -> Assignment:
        """
        Create a new assignment entry.
        
        Args:
            user_id: Student ID
            data: Assignment submission data
        
        Returns:
            Assignment: Created assignment
        """
        assignment = Assignment(
            user_id=str(user_id),
            question_text=data.question_text,
            question_image_url=data.question_image_url,
            input_type=data.input_type,
            subject=data.subject,
            grade_level=data.grade_level,
            mode=data.mode,
            language=data.language,
            status=ProcessingStatus.PENDING,
        )
        
        self.db.add(assignment)
        await self.db.commit()
        await self.db.refresh(assignment)
        
        # Trigger async processing based on mode
        if assignment.mode == AssignmentMode.SOLVE:
            await self._generate_solution(assignment)
        elif assignment.mode == AssignmentMode.HELP:
            await self._start_help_session(assignment)
            
        return assignment

    async def _generate_solution(self, assignment: Assignment) -> None:
        """Generate AI solution for assignment."""
        try:
            assignment.status = ProcessingStatus.PROCESSING
            await self.db.commit()
            
            # Prepare prompts
            lang_instruction = LANGUAGE_INSTRUCTIONS.get(
                assignment.language, 
                LANGUAGE_INSTRUCTIONS["gu"]
            )
            
            chain = SOLUTION_GENERATION_PROMPT | self.llm.llm
            
            response = await chain.ainvoke({
                "question": assignment.question_text,
                "subject": assignment.subject or "General",
                "grade_level": assignment.grade_level or "Not specified",
                "language_instruction": lang_instruction,
            })
            
            # Parse JSON
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            if content.endswith("```"):
                content = content[:-3]
                
            data = json.loads(content.strip())
            
            # Create solution record
            solution = AssignmentSolution(
                assignment_id=str(assignment.id),
                steps=data.get("steps", []),
                final_answer=data.get("final_answer", ""),
                explanation=data.get("explanation"),
                difficulty=DifficultyLevel(data.get("difficulty", "medium").lower()),
            )
            
            self.db.add(solution)
            assignment.status = ProcessingStatus.COMPLETED
            await self.db.commit()
            logger.info(f"Generated solution for assignment {assignment.id}")
            
        except Exception as e:
            logger.error(f"Solution generation failed: {e}")
            assignment.status = ProcessingStatus.FAILED
            assignment.extra_metadata = {"error": str(e)}
            await self.db.commit()

    async def _start_help_session(self, assignment: Assignment) -> None:
        """Initialize Socratic help session."""
        try:
            assignment.status = ProcessingStatus.PROCESSING
            
            session = HelpSession(
                assignment_id=str(assignment.id),
                current_hint_level=0,
                interactions=[],
            )
            self.db.add(session)
            await self.db.commit()
            
            # Generate first hint (Level 0)
            await self.generate_hint(session, assignment)
            
            assignment.status = ProcessingStatus.COMPLETED
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"Help session start failed: {e}")
            assignment.status = ProcessingStatus.FAILED
            await self.db.commit()

    async def generate_hint(
        self, 
        session: HelpSession, 
        assignment: Assignment,
        student_response: Optional[str] = None,
        request_next_level: bool = False
    ) -> dict[str, Any]:
        """
        Generate next hint for help session.
        
        Args:
            session: HelpSession object
            assignment: Parent Assignment
            student_response: Optional user input
            request_next_level: Force next hint level
        
        Returns:
            dict: Hint response
        """
        if request_next_level and session.current_hint_level < 5:
            session.current_hint_level += 1
            
        # Format history
        history_text = ""
        for i in session.interactions:
            history_text += f"Type: {i.get('type')}\nContent: {i.get('content')}\n\n"
            
        if student_response:
            history_text += f"Student: {student_response}\n"
            
        # LLM Call
        lang_instruction = LANGUAGE_INSTRUCTIONS.get(
            assignment.language, 
            LANGUAGE_INSTRUCTIONS["gu"]
        )
        
        chain = SOCRATIC_HINT_PROMPT | self.llm.llm
        
        try:
            response = await chain.ainvoke({
                "question": assignment.question_text,
                "subject": assignment.subject or "General",
                "grade_level": assignment.grade_level or "Not specified",
                "hint_level": session.current_hint_level,
                "history": history_text,
                "language_instruction": lang_instruction,
            })
            
            # Parse JSON
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            if content.endswith("```"):
                content = content[:-3]
                
            data = json.loads(content.strip())
            
            # Update session
            hint = {
                "type": "hint",
                "level": session.current_hint_level,
                "content": data.get("hint"),
                "timestamp": str(datetime.now())
            }
            
            # Log interaction
            if student_response:
                session.interactions.append({
                    "type": "student", 
                    "content": student_response,
                    "timestamp": str(datetime.now())
                })
            
            session.interactions.append(hint)
            session.is_completed = data.get("is_complete", False)
            
            # Ensure session is modified for SQLAlchemy tracking
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(session, "interactions")
            
            await self.db.commit()
            return data
            
        except Exception as e:
            logger.error(f"Hint generation failed: {e}")
            raise

    async def get_assignment(self, assignment_id: UUID, user_id: UUID) -> Optional[Assignment]:
        """Get assignment by ID."""
        stmt = select(Assignment).where(
            Assignment.id == str(assignment_id),
            Assignment.user_id == str(user_id),
            Assignment.is_active == True,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
        
    async def list_assignments(
        self, 
        user_id: UUID, 
        page: int = 1, 
        per_page: int = 20
    ) -> tuple[list[Assignment], int]:
        """List user assignments."""
        stmt = select(Assignment).where(
            Assignment.user_id == str(user_id),
            Assignment.is_active == True,
        ).order_by(Assignment.created_at.desc())
        
        # Count
        count_stmt = select(func.count()).select_from(Assignment).where(
            Assignment.user_id == str(user_id),
            Assignment.is_active == True
        )
        count_res = await self.db.execute(count_stmt)
        total = count_res.scalar()
        
        # Paginate
        offset = (page - 1) * per_page
        result = await self.db.execute(stmt.offset(offset).limit(per_page))
        return result.scalars().all(), total
