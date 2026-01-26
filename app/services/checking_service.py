"""
BhashaAI Backend - Checking Service

Orchestrates the paper checking process:
1. OCR Extraction (via OCRService)
2. Answer Segmentation
3. AI Grading (via LLM)
4. Result Aggregation
"""

import json
import logging
from uuid import UUID
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.paper_checking import (
    Submission, 
    SubmissionStatus, 
    AnswerKey, 
    GradedAnswer
)
from app.schemas.paper_checking import AnswerKeyCreate
from app.services.ocr_service import OCRService
from app.services.llm_service import get_llm_service
from app.services.prompts import GRADING_PROMPT, LANGUAGE_INSTRUCTIONS

logger = logging.getLogger(__name__)


class CheckingService:
    """Service for automated paper checking."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm = get_llm_service()
        self.ocr = OCRService()

    async def create_answer_key(self, data: AnswerKeyCreate) -> AnswerKey:
        """Create or update answer key for a paper."""
        # Check if exists
        stmt = select(AnswerKey).where(AnswerKey.question_paper_id == str(data.question_paper_id))
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        content_dict = {k: v.model_dump() for k, v in data.content.items()}
        
        if existing:
            existing.content = content_dict
            await self.db.commit()
            await self.db.refresh(existing)
            return existing
        
        new_key = AnswerKey(
            question_paper_id=str(data.question_paper_id),
            content=content_dict
        )
        self.db.add(new_key)
        await self.db.commit()
        await self.db.refresh(new_key)
        return new_key

    async def create_submission(
        self, 
        user_id: UUID, 
        input_url: str,
        question_paper_id: Optional[UUID] = None,
        student_name: Optional[str] = None
    ) -> Submission:
        """Initialize a new submission record."""
        submission = Submission(
            user_id=str(user_id),
            input_file_url=input_url,
            question_paper_id=str(question_paper_id) if question_paper_id else None,
            student_name=student_name,
            status=SubmissionStatus.UPLOADING
        )
        self.db.add(submission)
        await self.db.commit()
        await self.db.refresh(submission)
        return submission

    async def process_submission(self, submission_id: UUID):
        """
        Main processing pipeline. 
        Should ideally run as a background task.
        """
        stmt = select(Submission).where(Submission.id == str(submission_id))
        result = await self.db.execute(stmt)
        submission = result.scalar_one_or_none()
        
        if not submission:
            logger.error(f"Submission {submission_id} not found")
            return

        try:
            # 1. OCR
            submission.status = SubmissionStatus.OCR_PROCESSING
            await self.db.commit()
            
            raw_text = await self.ocr.extract_text(submission.input_file_url)
            submission.extracted_text = raw_text
            
            # 2. Segmentation
            segments = self.ocr.segment_answers(raw_text)
            
            # 3. Grading
            submission.status = SubmissionStatus.GRADING
            await self.db.commit()
            
            # Fetch Question Paper to get language preference
            paper_lang = "gu" # Default
            if submission.question_paper_id:
                from app.models.question_paper import QuestionPaper
                qp_stmt = select(QuestionPaper).where(QuestionPaper.id == submission.question_paper_id)
                qp_res = await self.db.execute(qp_stmt)
                qp = qp_res.scalar_one_or_none()
                if qp and qp.language:
                    paper_lang = qp.language

            # Fetch Answer Key if available
            answer_key_map = {}
            if submission.question_paper_id:
                key_stmt = select(AnswerKey).where(
                    AnswerKey.question_paper_id == submission.question_paper_id
                )
                key_res = await self.db.execute(key_stmt)
                key = key_res.scalar_one_or_none()
                if key:
                    answer_key_map = key.content

            # Grade each segment
            total_obtained = 0.0
            total_max = 0.0
            
            for i, segment in enumerate(segments):
                # Try to map to a question ID or index
                # Ideally, segment labels (Q1) map to question IDs
                # For now, we assume simple mapping logic or generic evaluation
                
                # Find matching criteria from Answer Key if possible
                # This is heuristic for the prototype
                criteria = self._find_criteria(segment["label"], answer_key_map)
                
                graded = await self._grade_single_answer(
                    question_text=segment["label"], # or mapped question text
                    student_answer=segment["text"],
                    criteria=criteria,
                    language=paper_lang
                )
                
                # Save GradedAnswer
                answer_record = GradedAnswer(
                    submission_id=str(submission.id),
                    question_text=segment["label"],
                    student_answer_text=segment["text"],
                    marks_obtained=graded["marks"],
                    max_marks=criteria.get("max_marks", 5.0), # Default if not found
                    feedback=graded["feedback"],
                    confidence_score=graded["confidence"]
                )
                self.db.add(answer_record)
                
                total_obtained += graded["marks"]
                total_max += criteria.get("max_marks", 5.0)

            # 4. Finalize
            submission.overall_score = total_obtained
            submission.max_score = total_max
            submission.status = SubmissionStatus.COMPLETED
            if not submission.student_name:
                 # Try to find name in text heuristic (omitted for brevity)
                 pass

            await self.db.commit()
            
        except Exception as e:
            logger.error(f"Processing failed: {e}")
            submission.status = SubmissionStatus.FAILED
            submission.summary = str(e)
            await self.db.commit()

    def _find_criteria(self, label: str, key_map: dict) -> dict:
        """Helper to find matching expected answer."""
        # Simple heuristic: extract number from "Q1" -> "1"
        # In prod, use fuzzy matching or ID mapping
        import re
        match = re.search(r'\d+', label)
        if match:
            q_num = match.group(0) # e.g. "1" from "Q1" or "1."
            # In key_map, keys might be UUIDs or numbers.
            # Assuming key_map keys match the question ordering for this prototype for simplicity
            # Or assume key_map keys ARE the numbers
            return key_map.get(q_num, {})
        return {}
        
    async def _grade_single_answer(self, question_text: str, student_answer: str, criteria: dict, language: str = "gu") -> dict:
        """Use LLM to grade answer."""
        
        expected = criteria.get("expected_answer", "N/A (General Evaluation)")
        max_marks = criteria.get("max_marks", 5.0)
        keywords = criteria.get("keywords", [])
        partial = criteria.get("partial_marking", True)
        
        chain = GRADING_PROMPT | self.llm.llm
        
        try:
            response = await chain.ainvoke({
                "question": question_text,
                "expected_answer": expected,
                "student_answer": student_answer,
                "max_marks": max_marks,
                "keywords": ", ".join(keywords),
                "partial_marking": str(partial),
                "language_instruction": LANGUAGE_INSTRUCTIONS.get(language, LANGUAGE_INSTRUCTIONS["gu"])
            })
            
            content = response.content.strip()
            # Clean json
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                 content = content.split("```")[1]
                 
            data = json.loads(content.strip())
            return {
                "marks": data.get("marks_obtained", 0.0),
                "feedback": data.get("feedback", ""),
                "confidence": data.get("confidence_score", 0.8)
            }
        except Exception as e:
            logger.error(f"LLM Grading failed: {e}")
            return {"marks": 0.0, "feedback": "Auto-grading failed.", "confidence": 0.0}

    async def get_submission(self, submission_id: UUID) -> Optional[Submission]:
        stmt = select(Submission).where(Submission.id == str(submission_id))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
