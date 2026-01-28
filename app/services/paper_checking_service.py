"""
BhashaAI Backend - Paper Checking Service

Service layer for paper checking operations:
- Answer key CRUD operations
- Paper submission and grading workflow
- OCR extraction and AI-powered evaluation
- Result aggregation and feedback generation

This service orchestrates:
1. File upload to storage
2. OCR text extraction (via OCRService)
3. Answer segmentation
4. AI grading against answer key
5. Result aggregation and grade calculation
"""

import logging
import re
from typing import Any, List, Optional
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.paper_checking import (
    AnswerKey,
    CheckedPaper,
    CheckedPaperStatus,
)
from app.schemas.paper_checking import (
    AnswerKeyCreate,
    AnswerKeyResponse,
    CheckedPaperResponse,
    QuestionResult,
)
from app.services.ocr_service import OCRService
from app.services.llm_service import get_llm_service
from app.services.prompts import (
    GRADING_PROMPT, 
    LANGUAGE_INSTRUCTIONS,
    ANSWER_KEY_EXTRACTION_PROMPT,
)

logger = logging.getLogger(__name__)


class PaperCheckingService:
    """
    Service for paper checking operations.
    
    Handles the complete workflow of creating answer keys,
    submitting student papers, and generating grading results.
    
    Attributes:
        db: AsyncSession for database operations
        llm: LLM service for AI grading
        ocr: OCR service for text extraction
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize the paper checking service.
        
        Args:
            db: AsyncSession for database operations
        """
        self.db = db
        self.llm = get_llm_service()
        self.ocr = OCRService()
    
    # =========================================================================
    # Answer Key Operations
    # =========================================================================
    
    async def create_answer_key(
        self, 
        user_id: UUID, 
        data: AnswerKeyCreate
    ) -> AnswerKey:
        """
        Create a new answer key.
        
        Args:
            user_id: ID of the teacher creating the answer key
            data: Answer key creation data
            
        Returns:
            AnswerKey: The created answer key
            
        Raises:
            ValueError: If validation fails
        """
        try:
            # Convert Pydantic models to dicts for JSONB storage
            answers_list = [item.model_dump() for item in data.answers]
            marking_scheme = data.marking_scheme.model_dump() if data.marking_scheme else {}
            
            answer_key = AnswerKey(
                user_id=str(user_id),
                paper_id=str(data.paper_id) if data.paper_id else None,
                title=data.title,
                subject=data.subject,
                total_marks=data.total_marks,
                answers=answers_list,
                marking_scheme=marking_scheme,
            )
            
            self.db.add(answer_key)
            await self.db.commit()
            await self.db.refresh(answer_key)
            
            logger.info(f"Created answer key {answer_key.id} for user {user_id}")
            return answer_key
            
        except Exception as e:
            logger.error(f"Failed to create answer key: {e}")
            await self.db.rollback()
            raise
    
    async def get_answer_key(self, key_id: UUID) -> Optional[AnswerKey]:
        """
        Get an answer key by ID.
        
        Args:
            key_id: Answer key UUID
            
        Returns:
            AnswerKey or None if not found
        """
        stmt = select(AnswerKey).where(AnswerKey.id == str(key_id))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_answer_keys_by_user(
        self, 
        user_id: UUID,
        search: Optional[str] = None
    ) -> List[AnswerKey]:
        """
        List all answer keys for a user with optional search.
        
        Args:
            user_id: User's UUID
            search: Search term for title
            
        Returns:
            List of answer keys
        """
        stmt = select(AnswerKey).where(AnswerKey.user_id == str(user_id))
        
        if search:
            stmt = stmt.where(AnswerKey.title.ilike(f"%{search}%"))
            
        stmt = stmt.order_by(AnswerKey.created_at.desc())
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def delete_answer_key(self, key_id: UUID) -> bool:
        """
        Delete an answer key.
        
        Args:
            key_id: Answer key UUID
            
        Returns:
            True if deleted, False if not found
        """
        answer_key = await self.get_answer_key(key_id)
        if not answer_key:
            return False
        
        await self.db.delete(answer_key)
        await self.db.commit()
        logger.info(f"Deleted answer key {key_id}")
        return True
    
    async def extract_answer_key_from_file(self, file_path: str) -> dict:
        """
        Extract answer key structure from a file (PDF/Image) using OCR and AI.
        
        Args:
            file_path: Path to the uploaded file
            
        Returns:
            Dict matching AnswerKeyCreate schema structure
        """
        try:
            # 1. OCR Extraction
            logger.info(f"Extracting answer key from {file_path}")
            extracted_text = await self.ocr.extract_text(file_path)
            
            if not extracted_text.strip():
                raise ValueError("No text could be extracted from the file.")
            
            # 2. AI Parsing
            chain = ANSWER_KEY_EXTRACTION_PROMPT | self.llm.llm
            response = await chain.ainvoke({"text": extracted_text[:10000]}) # Limit context size
            
            content = response.content.strip()
            
            # Clean JSON markdown
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1]
                
            import json
            data = json.loads(content.strip())
            
            # Additional cleanup/validation could go here
            return data
            
        except Exception as e:
            logger.error(f"Failed to extract answer key: {e}")
            raise
    
    # =========================================================================
    # Paper Submission Operations
    # =========================================================================
    
    async def submit_paper(
        self,
        user_id: UUID,
        answer_key_id: UUID,
        file_path: str,
        student_name: Optional[str] = None,
        student_id: Optional[str] = None,
    ) -> CheckedPaper:
        """
        Submit a student paper for checking.
        
        Args:
            user_id: Teacher's UUID
            answer_key_id: Answer key to grade against
            file_path: Path to uploaded file in storage
            student_name: Optional student name
            student_id: Optional student ID
            
        Returns:
            CheckedPaper: The created paper submission
            
        Raises:
            ValueError: If answer key not found
        """
        # Verify answer key exists
        answer_key = await self.get_answer_key(answer_key_id)
        if not answer_key:
            raise ValueError(f"Answer key {answer_key_id} not found")
        
        checked_paper = CheckedPaper(
            answer_key_id=str(answer_key_id),
            teacher_id=str(user_id),
            student_name=student_name,
            student_id=student_id,
            scanned_file_path=file_path,
            total_marks=answer_key.total_marks,
            obtained_marks=0.0,
            percentage=0.0,
            results=[],
            status=CheckedPaperStatus.PENDING,
        )
        
        self.db.add(checked_paper)
        await self.db.commit()
        await self.db.refresh(checked_paper)
        
        logger.info(f"Created checked paper {checked_paper.id} for answer key {answer_key_id}")
        return checked_paper
    
    async def process_paper(self, paper_id: UUID) -> None:
        """
        Process a submitted paper through OCR and AI grading.
        
        This is intended to be run as a background task.
        
        Args:
            paper_id: CheckedPaper UUID
        """
        stmt = select(CheckedPaper).where(CheckedPaper.id == str(paper_id))
        result = await self.db.execute(stmt)
        paper = result.scalar_one_or_none()
        
        if not paper:
            logger.error(f"CheckedPaper {paper_id} not found")
            return
        
        try:
            # Update status to processing
            paper.status = CheckedPaperStatus.PROCESSING
            await self.db.commit()
            
            # 1. OCR Extraction
            logger.info(f"Starting OCR for paper {paper_id}")
            extracted_text = await self.ocr.extract_text(paper.scanned_file_path)
            paper.extracted_text = extracted_text
            
            # 2. Get Answer Key
            # paper.answer_key_id is already a UUID object due to as_uuid=True
            answer_key = await self.get_answer_key(paper.answer_key_id)
            if not answer_key:
                raise ValueError("Answer key not found")
            
            # 3. Segment and Grade Answers
            results = await self._grade_paper(
                extracted_text=extracted_text,
                answer_key=answer_key,
            )
            
            # 4. Calculate totals
            total_obtained = sum(r["obtained_marks"] for r in results)
            percentage = (total_obtained / answer_key.total_marks * 100) if answer_key.total_marks > 0 else 0
            
            # 5. Update paper with results
            paper.results = results
            paper.obtained_marks = total_obtained
            paper.percentage = round(percentage, 2)
            paper.grade = self._calculate_grade(percentage)
            paper.overall_feedback = self._generate_overall_feedback(results, percentage)
            paper.overall_feedback_gujarati = self._generate_overall_feedback_gujarati(results, percentage)
            paper.status = CheckedPaperStatus.COMPLETED
            
            await self.db.commit()
            logger.info(f"Completed grading paper {paper_id}: {total_obtained}/{answer_key.total_marks}")
            
        except Exception as e:
            logger.error(f"Failed to process paper {paper_id}: {e}")
            paper.status = CheckedPaperStatus.FAILED  # Mark as failed on error
            paper.overall_feedback = f"Processing failed: {str(e)}"
            await self.db.commit()
    
    async def _grade_paper(
        self, 
        extracted_text: str, 
        answer_key: AnswerKey
    ) -> List[dict]:
        """
        Grade extracted text against answer key.
        
        Args:
            extracted_text: OCR extracted text from student paper
            answer_key: Answer key with expected answers
            
        Returns:
            List of question result dicts
        """
        results = []
        
        # Segment the text into answers
        segments = self.ocr.segment_answers(extracted_text)
        answers = answer_key.answers or []
        
        for answer_item in answers:
            q_num = answer_item.get("question_number", 0)
            q_type = answer_item.get("type", "short_answer")
            max_marks = answer_item.get("max_marks", 1.0)
            
            # Find matching segment
            student_answer = self._find_answer_segment(q_num, segments)
            
            if q_type == "mcq":
                result = self._grade_mcq(
                    student_answer=student_answer,
                    correct_answer=answer_item.get("correct_answer", ""),
                    max_marks=max_marks,
                )
            else:
                result = await self._grade_text_answer(
                    student_answer=student_answer,
                    expected_answer=answer_item.get("expected_answer", ""),
                    keywords=answer_item.get("keywords", []),
                    max_marks=max_marks,
                    partial_marking=answer_item.get("partial_marking", True),
                )
            
            result["question_number"] = q_num
            result["max_marks"] = max_marks
            results.append(result)
        
        return results
    
    def _find_answer_segment(self, question_number: int, segments: List[dict]) -> str:
        """
        Find the answer segment for a given question number.
        
        Args:
            question_number: Question number to find
            segments: List of OCR segments
            
        Returns:
            Student's answer text or empty string
        """
        for segment in segments:
            label = segment.get("label", "")
            # Match patterns like "Q1", "1.", "1)", "Question 1"
            match = re.search(r'(\d+)', label)
            if match and int(match.group(1)) == question_number:
                return segment.get("text", "")
        return ""
    
    def _grade_mcq(
        self, 
        student_answer: str, 
        correct_answer: str, 
        max_marks: float
    ) -> dict:
        """
        Grade an MCQ answer.
        
        Args:
            student_answer: Student's chosen option
            correct_answer: Correct option
            max_marks: Maximum marks
            
        Returns:
            Grading result dict
        """
        # Clean and normalize answers
        student_clean = student_answer.strip().upper()[:1] if student_answer else ""
        correct_clean = correct_answer.strip().upper()[:1] if correct_answer else ""
        
        is_correct = student_clean == correct_clean
        
        return {
            "obtained_marks": max_marks if is_correct else 0.0,
            "status": "correct" if is_correct else "incorrect",
            "student_answer": student_clean or None,
            "keyword_matches": [],
            "missing_keywords": [],
            "semantic_similarity": None,
            "feedback": "Correct answer." if is_correct else f"Incorrect. The correct answer is {correct_clean}.",
            "feedback_gujarati": "સાચો જવાબ." if is_correct else f"ખોટો જવાબ. સાચો જવાબ {correct_clean} છે.",
        }
    
    async def _grade_text_answer(
        self,
        student_answer: str,
        expected_answer: str,
        keywords: List[str],
        max_marks: float,
        partial_marking: bool = True,
    ) -> dict:
        """
        Grade a text-based answer using keywords and AI.
        
        Args:
            student_answer: Student's answer text
            expected_answer: Expected answer
            keywords: Keywords for matching
            max_marks: Maximum marks
            partial_marking: Whether to give partial marks
            
        Returns:
            Grading result dict
        """
        if not student_answer.strip():
            return {
                "obtained_marks": 0.0,
                "status": "incorrect",
                "student_answer": None,
                "keyword_matches": [],
                "missing_keywords": keywords,
                "semantic_similarity": 0.0,
                "feedback": "No answer provided.",
                "feedback_gujarati": "કોઈ જવાબ આપવામાં આવ્યો નથી.",
            }
        
        # Keyword matching
        student_lower = student_answer.lower()
        keyword_matches = [kw for kw in keywords if kw.lower() in student_lower]
        missing_keywords = [kw for kw in keywords if kw.lower() not in student_lower]
        
        # Calculate keyword score
        keyword_score = len(keyword_matches) / len(keywords) if keywords else 0.5
        
        # Use LLM for semantic grading
        try:
            llm_result = await self._llm_grade_answer(
                student_answer=student_answer,
                expected_answer=expected_answer,
                max_marks=max_marks,
                keywords=keywords,
            )
            semantic_similarity = llm_result.get("confidence", 0.5)
            obtained_marks = llm_result.get("marks", 0.0)
            feedback = llm_result.get("feedback", "")
        except Exception as e:
            logger.warning(f"LLM grading failed: {e}, using keyword-based grading")
            semantic_similarity = keyword_score
            obtained_marks = max_marks * keyword_score if partial_marking else (max_marks if keyword_score >= 0.7 else 0)
            feedback = f"Matched {len(keyword_matches)}/{len(keywords)} keywords."
        
        # Determine status
        if obtained_marks >= max_marks * 0.9:
            status = "correct"
        elif obtained_marks > 0:
            status = "partial"
        else:
            status = "incorrect"
        
        return {
            "obtained_marks": round(obtained_marks, 2),
            "status": status,
            "student_answer": student_answer[:500],  # Truncate for storage
            "keyword_matches": keyword_matches,
            "missing_keywords": missing_keywords,
            "semantic_similarity": round(semantic_similarity, 2),
            "feedback": feedback,
            "feedback_gujarati": None,  # Could add Gujarati translation
        }
    
    async def _llm_grade_answer(
        self,
        student_answer: str,
        expected_answer: str,
        max_marks: float,
        keywords: List[str],
        language: str = "gu",
    ) -> dict:
        """
        Use LLM to grade an answer.
        
        Args:
            student_answer: Student's answer
            expected_answer: Expected answer
            max_marks: Maximum marks
            keywords: Keywords for matching
            language: Language for feedback
            
        Returns:
            Dict with marks, feedback, and confidence
        """
        chain = GRADING_PROMPT | self.llm.llm
        
        response = await chain.ainvoke({
            "question": "Evaluate this answer",
            "expected_answer": expected_answer,
            "student_answer": student_answer,
            "max_marks": max_marks,
            "keywords": ", ".join(keywords),
            "partial_marking": "true",
            "language_instruction": LANGUAGE_INSTRUCTIONS.get(language, LANGUAGE_INSTRUCTIONS["gu"]),
        })
        
        content = response.content.strip()
        
        # Parse JSON response
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1]
        
        import json
        data = json.loads(content.strip())
        
        return {
            "marks": data.get("marks_obtained", 0.0),
            "feedback": data.get("feedback", ""),
            "confidence": data.get("confidence_score", 0.5),
        }
    
    def _calculate_grade(self, percentage: float) -> str:
        """
        Calculate letter grade from percentage.
        
        Args:
            percentage: Score percentage (0-100)
            
        Returns:
            Letter grade string
        """
        if percentage >= 90:
            return "A+"
        elif percentage >= 80:
            return "A"
        elif percentage >= 70:
            return "B+"
        elif percentage >= 60:
            return "B"
        elif percentage >= 50:
            return "C"
        elif percentage >= 40:
            return "D"
        else:
            return "F"
    
    def _generate_overall_feedback(self, results: List[dict], percentage: float) -> str:
        """
        Generate overall feedback based on results.
        
        Args:
            results: List of question results
            percentage: Overall percentage
            
        Returns:
            Feedback string
        """
        correct_count = sum(1 for r in results if r.get("status") == "correct")
        total_count = len(results)
        
        if percentage >= 80:
            return f"Excellent performance! You answered {correct_count}/{total_count} questions correctly. Strong understanding of the concepts."
        elif percentage >= 60:
            return f"Good work! You scored correctly on {correct_count}/{total_count} questions. Review the missed concepts for improvement."
        elif percentage >= 40:
            return f"Satisfactory performance with {correct_count}/{total_count} correct. Focus on understanding core concepts better."
        else:
            return f"Needs improvement. Only {correct_count}/{total_count} correct. Please review the material and practice more."
    
    def _generate_overall_feedback_gujarati(self, results: List[dict], percentage: float) -> str:
        """
        Generate overall feedback in Gujarati.
        
        Args:
            results: List of question results
            percentage: Overall percentage
            
        Returns:
            Gujarati feedback string
        """
        correct_count = sum(1 for r in results if r.get("status") == "correct")
        total_count = len(results)
        
        if percentage >= 80:
            return f"ઉત્કૃષ્ટ પ્રદર્શન! તમે {correct_count}/{total_count} પ્રશ્નોના સાચા જવાબ આપ્યા. ખ્યાલોની મજબૂત સમજ."
        elif percentage >= 60:
            return f"સારું કામ! તમે {correct_count}/{total_count} પ્રશ્નો સાચા ઉકેલ્યા. સુધારણા માટે ચૂકી ગયેલા ખ્યાલોની સમીક્ષા કરો."
        elif percentage >= 40:
            return f"{correct_count}/{total_count} સાચા સાથે સંતોષકારક પ્રદર્શન. મૂળભૂત ખ્યાલોને વધુ સારી રીતે સમજવા પર ધ્યાન આપો."
        else:
            return f"સુધારણાની જરૂર છે. માત્ર {correct_count}/{total_count} સાચા. કૃપા કરીને સામગ્રીની સમીક્ષા કરો અને વધુ પ્રેક્ટિસ કરો."
    
    # =========================================================================
    # Retrieval Operations
    # =========================================================================
    
    async def get_checked_paper(self, paper_id: UUID) -> Optional[CheckedPaper]:
        """
        Get a checked paper by ID.
        
        Args:
            paper_id: CheckedPaper UUID
            
        Returns:
            CheckedPaper or None
        """
        stmt = select(CheckedPaper).where(CheckedPaper.id == str(paper_id))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def list_checked_papers(self, answer_key_id: UUID) -> List[CheckedPaper]:
        """
        List all papers checked with a specific answer key.
        
        Args:
            answer_key_id: Answer key UUID
            
        Returns:
            List of checked papers
        """
        stmt = (
            select(CheckedPaper)
            .where(CheckedPaper.answer_key_id == str(answer_key_id))
            .order_by(CheckedPaper.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_user_checked_papers(self, user_id: UUID) -> List[CheckedPaper]:
        """
        List all papers checked by a user.
        
        Args:
            user_id: Teacher's UUID
            
        Returns:
            List of checked papers
        """
        stmt = (
            select(CheckedPaper)
            .where(CheckedPaper.teacher_id == str(user_id))
            .order_by(CheckedPaper.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
