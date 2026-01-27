"""
BhashaAI Backend - Worksheet Service

Handles gamified worksheet generation and solving logic.
"""

import json
import logging
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.worksheet import (
    Worksheet,
    WorksheetQuestion,
    WorksheetAttempt,
    WorksheetStatus,
    AttemptStatus
)
from app.schemas.worksheet import (
    WorksheetGenerateRequest,
    WorksheetQuestionBase,
    StepFeedback,
    WorksheetStep
)
from app.services.llm_service import get_llm_service
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)

WORKSHEET_GENERATION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an expert educational content creator. Create a step-by-step worksheet for a student.
    
    Topic: {topic}
    Subject: {subject}
    Grade: {grade_level}
    Difficulty: {difficulty}
    Count: {num_questions}
    
    For each question, break it down into logical steps that guide the student to the solution.
    Each step must have:
    1. step_text: The instruction or sub-question.
    2. answer_key: The expected short answer for this step (number, word, or short phrase).
    3. hint: A helpful hint if they get it wrong.
    
    Return the response as a JSON list of objects with this structure:
    [
        {{
            "content": "The main question text",
            "correct_answer": "The final answer",
            "steps": [
                {{
                    "step_text": "First, find X...",
                    "answer_key": "10",
                    "hint": "Remember rule Y..."
                }}
            ]
        }}
    ]
    
    Ensure strict JSON format. No markdown formatting.
    """),
    ("user", "Generate the worksheet.")
])

class WorksheetService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm = get_llm_service()

    async def generate_worksheet(
        self,
        user_id: UUID,
        request: WorksheetGenerateRequest
    ) -> Worksheet:
        """Generate a new worksheet using LLM."""
        
        # 1. Call LLM
        chain = WORKSHEET_GENERATION_PROMPT | self.llm.llm
        
        try:
            response = await chain.ainvoke({
                "topic": request.topic,
                "subject": request.subject,
                "grade_level": request.grade_level,
                "difficulty": request.difficulty,
                "num_questions": request.num_questions
            })
            
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
                
            questions_data = json.loads(content.strip())
            
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise ValueError("Failed to generate worksheet content")

        # 2. Save to DB
        worksheet = Worksheet(
            user_id=str(user_id),
            title=f"{request.topic} Worksheet",
            topic=request.topic,
            subject=request.subject,
            grade_level=request.grade_level,
            difficulty=request.difficulty,
            status=WorksheetStatus.PUBLISHED
        )
        self.db.add(worksheet)
        await self.db.flush()

        for idx, q_data in enumerate(questions_data):
            # Validate step structure
            steps = q_data.get("steps", [])
            # normalized_steps = [
            #     WorksheetStep(**s).model_dump() for s in steps
            # ]
            
            question = WorksheetQuestion(
                worksheet_id=worksheet.id,
                content=q_data["content"],
                correct_answer=q_data["correct_answer"],
                order=idx + 1,
                steps=steps
            )
            self.db.add(question)
            
        await self.db.commit()
        await self.db.refresh(worksheet)
        return worksheet

    async def get_worksheet(self, worksheet_id: UUID) -> Optional[Worksheet]:
        stmt = select(Worksheet).where(Worksheet.id == str(worksheet_id))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_worksheets(self, user_id: UUID) -> List[Worksheet]:
        stmt = select(Worksheet).where(Worksheet.user_id == str(user_id)).order_by(Worksheet.created_at.desc())
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def delete_worksheet(self, user_id: UUID, worksheet_id: UUID) -> bool:
        """Delete a worksheet if owned by user."""
        stmt = select(Worksheet).where(
            Worksheet.id == str(worksheet_id),
            Worksheet.user_id == str(user_id)
        )
        result = await self.db.execute(stmt)
        worksheet = result.scalar_one_or_none()
        
        if not worksheet:
            return False
            
        await self.db.delete(worksheet)
        await self.db.commit()
        return True

    # --- Game Logic ---

    async def start_attempt(self, user_id: UUID, worksheet_id: UUID) -> WorksheetAttempt:
        attempt = WorksheetAttempt(
            user_id=str(user_id),
            worksheet_id=str(worksheet_id),
            status=AttemptStatus.IN_PROGRESS,
            current_question_index=0,
            current_step_index=0,
            score=0,
            progress_data={}
        )
        self.db.add(attempt)
        await self.db.commit()
        await self.db.refresh(attempt)
        return attempt

    async def get_attempt(self, attempt_id: UUID) -> Optional[WorksheetAttempt]:
        stmt = select(WorksheetAttempt).where(WorksheetAttempt.id == str(attempt_id))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def submit_step(
        self, 
        attempt_id: UUID, 
        step_answer: str
    ) -> StepFeedback:
        """
        Process a user's answer for the current step.
        """
        attempt = await self.get_attempt(attempt_id)
        if not attempt:
            raise ValueError("Attempt not found")

        worksheet = await self.get_worksheet(attempt.worksheet_id)
        if not worksheet:
             raise ValueError("Worksheet not found")

        # Get current question
        current_q = worksheet.questions[attempt.current_question_index]
        current_step = current_q.steps[attempt.current_step_index]
        
        # Check answer
        correct_key = current_step["answer_key"].lower().strip()
        user_input = step_answer.strip()
        user_input_lower = user_input.lower()
        
        is_correct = False
        is_skipped = user_input == "SKIP"
        
        if is_skipped:
            is_correct = True # We treat it as "done" but give 0 points
            message = "Skipped. The answer was: " + current_step["answer_key"]
        elif user_input_lower == correct_key:
            is_correct = True
            message = "Correct!"
        else:
            # Fuzzy match attempt: if user answer is IN key or key is IN user answer (lenient)
            # Useful for "Jupiter" vs "Jupiter, Saturn..."
            if (len(user_input) > 2 and user_input_lower in correct_key) or \
               (len(correct_key) > 2 and correct_key in user_input_lower):
                is_correct = True
                message = "Correct!"
            else:
                is_correct = False
                message = f"Incorrect. Hint: {current_step.get('hint', 'Try again')}"
        
        feedback = StepFeedback(
            is_correct=is_correct,
            message=message,
            points_awarded=0,
            next_step_index=attempt.current_step_index,
            next_question_index=attempt.current_question_index,
             correct_answer=current_step["answer_key"] if is_skipped else None
        )

        if is_correct:
            # Update Score only if not skipped
            points = 10 if not is_skipped else 0
            attempt.score += points
            feedback.points_awarded = points
            
            # Record progress
            q_id = str(current_q.id)
            if q_id not in attempt.progress_data:
                attempt.progress_data[q_id] = {}
            attempt.progress_data[q_id][str(attempt.current_step_index)] = step_answer
            
            # Move to next step or question
            if attempt.current_step_index < len(current_q.steps) - 1:
                attempt.current_step_index += 1
                feedback.next_step_index = attempt.current_step_index
                if not is_skipped:
                     feedback.message = "Good job! Moving to next step."
            else:
                # Question completed
                if attempt.current_question_index < len(worksheet.questions) - 1:
                    attempt.current_question_index += 1
                    attempt.current_step_index = 0
                    feedback.next_question_index = attempt.current_question_index
                    feedback.next_step_index = 0
                    feedback.message = "Question completed! Next question."
                else:
                    # Worksheet completed
                    attempt.status = AttemptStatus.COMPLETED
                    feedback.message = "Worksheet completed!"
                    feedback.is_complete = True

        # Save state
        # Force update for JSONB field
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(attempt, "progress_data")
        
        await self.db.commit()
        await self.db.refresh(attempt)
        
        return feedback
