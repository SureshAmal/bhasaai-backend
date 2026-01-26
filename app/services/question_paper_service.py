"""
BhashaAI Backend - Question Paper Service

Handles question paper generation and management.
"""

import logging
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Question,
    QuestionPaper,
    PaperStatus,
    QuestionType,
    DifficultyLevel,
)
from app.schemas.question_paper import (
    GeneratePaperRequest,
    QuestionPaperUpdate,
)
from app.services.document_service import DocumentService
from app.services.llm_service import get_llm_service

logger = logging.getLogger(__name__)


class QuestionPaperService:
    """
    Service for question paper generation and management.
    """
    
    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db
        self.llm = get_llm_service()
    
    async def generate_paper(
        self,
        user_id: UUID,
        request: GeneratePaperRequest,
        institution_id: Optional[UUID] = None,
    ) -> QuestionPaper:
        """
        Generate a question paper using AI.
        
        Args:
            user_id: Creator's user ID
            request: Generation request with parameters
            institution_id: Associated institution
        
        Returns:
            QuestionPaper: Generated paper with questions
        """
        # Get context from document or topic
        context = await self._get_context(user_id, request)
        
        # Generate questions using LLM
        question_types_dict = {
            "mcq": request.question_types.mcq,
            "short_answer": request.question_types.short_answer,
            "long_answer": request.question_types.long_answer,
            "true_false": request.question_types.true_false,
            "fill_blank": request.question_types.fill_blank,
        }
        # Remove zero counts
        question_types_dict = {k: v for k, v in question_types_dict.items() if v > 0}
        
        difficulty_dict = {
            "easy": request.difficulty_distribution.easy,
            "medium": request.difficulty_distribution.medium,
            "hard": request.difficulty_distribution.hard,
        }
        
        generated_questions = await self.llm.generate_questions(
            context=context,
            subject=request.subject,
            grade_level=request.grade_level,
            language=request.language,
            total_marks=request.total_marks,
            difficulty_distribution=difficulty_dict,
            question_types=question_types_dict,
            include_answers=request.include_answers,
        )
        
        # Create question paper
        paper = QuestionPaper(
            user_id=str(user_id),
            institution_id=str(institution_id) if institution_id else None,
            document_id=str(request.document_id) if request.document_id else None,
            title=request.title,
            title_gujarati=request.title_gujarati,
            subject=request.subject,
            grade_level=request.grade_level,
            total_marks=request.total_marks,
            duration_minutes=request.duration_minutes,
            language=request.language,
            difficulty_distribution=difficulty_dict,
            question_type_distribution=question_types_dict,
            status=PaperStatus.GENERATED,
        )
        
        self.db.add(paper)
        await self.db.flush()  # Get paper ID
        
        # Create questions
        for q_data in generated_questions:
            question = Question(
                paper_id=str(paper.id),
                question_number=q_data["question_number"],
                question_text=q_data["question_text"],
                question_text_gujarati=q_data.get("question_text_gujarati"),
                question_type=QuestionType(q_data.get("question_type", "short_answer")),
                marks=q_data.get("marks", 1),
                difficulty=DifficultyLevel(q_data.get("difficulty", "medium")),
                answer=q_data.get("answer"),
                answer_gujarati=q_data.get("answer_gujarati"),
                options=q_data.get("options"),
                correct_option=q_data.get("correct_option"),
                explanation=q_data.get("explanation"),
                bloom_level=q_data.get("bloom_level"),
                topic=q_data.get("topic"),
                keywords=q_data.get("keywords"),
            )
            self.db.add(question)
        
        await self.db.commit()
        await self.db.refresh(paper)
        
        logger.info(f"Generated paper {paper.id} with {len(generated_questions)} questions")
        return paper
    
    async def _get_context(
        self,
        user_id: UUID,
        request: GeneratePaperRequest,
    ) -> str:
        """Get context text for question generation."""
        if request.context:
            return request.context
        
        if request.document_id:
            doc_service = DocumentService(self.db)
            document = await doc_service.get_document(request.document_id, user_id)
            
            if not document:
                raise ValueError("Document not found")
            
            # Use cached text or extract
            if document.text_content:
                return document.text_content
            
            text = await doc_service.extract_text(document)
            
            # Cache extracted text
            document.text_content = text
            await self.db.commit()
            
            return text
        
        if request.topic:
            return f"Topic: {request.topic}\n\nGenerate questions about this topic for {request.subject} subject."
        
        raise ValueError("No context source provided (document_id, topic, or context required)")
    
    async def get_paper(
        self,
        paper_id: UUID,
        user_id: UUID,
    ) -> Optional[QuestionPaper]:
        """Get paper by ID for a specific user."""
        stmt = select(QuestionPaper).where(
            QuestionPaper.id == str(paper_id),
            QuestionPaper.user_id == str(user_id),
            QuestionPaper.is_active == True,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def list_papers(
        self,
        user_id: UUID,
        page: int = 1,
        per_page: int = 20,
        subject: Optional[str] = None,
        status: Optional[str] = None,
    ) -> tuple[list[QuestionPaper], int]:
        """List papers for a user with pagination."""
        # Build query
        conditions = [
            QuestionPaper.user_id == str(user_id),
            QuestionPaper.is_active == True,
        ]
        
        if subject:
            conditions.append(QuestionPaper.subject == subject)
        if status:
            conditions.append(QuestionPaper.status == PaperStatus(status))
        
        # Count
        count_stmt = select(func.count()).select_from(QuestionPaper).where(*conditions)
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar() or 0
        
        # Get results
        offset = (page - 1) * per_page
        stmt = (
            select(QuestionPaper)
            .where(*conditions)
            .order_by(QuestionPaper.created_at.desc())
            .offset(offset)
            .limit(per_page)
        )
        result = await self.db.execute(stmt)
        papers = result.scalars().all()
        
        return list(papers), total
    
    async def update_paper(
        self,
        paper_id: UUID,
        user_id: UUID,
        update_data: QuestionPaperUpdate,
    ) -> Optional[QuestionPaper]:
        """Update a question paper."""
        paper = await self.get_paper(paper_id, user_id)
        if not paper:
            return None
        
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            if value is not None:
                if key == "status":
                    setattr(paper, key, PaperStatus(value))
                else:
                    setattr(paper, key, value)
        
        await self.db.commit()
        await self.db.refresh(paper)
        
        return paper
    
    async def delete_paper(
        self,
        paper_id: UUID,
        user_id: UUID,
    ) -> bool:
        """Soft delete a paper."""
        paper = await self.get_paper(paper_id, user_id)
        if not paper:
            return False
        
        paper.is_active = False
        await self.db.commit()
        
        logger.info(f"Paper deleted: {paper_id}")
        return True
    
    async def publish_paper(
        self,
        paper_id: UUID,
        user_id: UUID,
    ) -> Optional[QuestionPaper]:
        """Publish a paper (change status to published)."""
        paper = await self.get_paper(paper_id, user_id)
        if not paper:
            return None
        
        paper.status = PaperStatus.PUBLISHED
        await self.db.commit()
        await self.db.refresh(paper)
        
        return paper
