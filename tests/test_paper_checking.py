"""
BhashaAI Backend - Paper Checking Tests

Tests for Answer Key management and Submission grading workflow.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from uuid import uuid4
from langchain_core.runnables import Runnable
from langchain_core.messages import AIMessage

from app.models.paper_checking import SubmissionStatus
from app.schemas.paper_checking import AnswerKeyCreate, AnswerCriteria
from app.services.checking_service import CheckingService


# --- Mock Data ---

MOCK_OCR_TEXT = """
Student Name: Test User
Q1. Photosynthesis
Q2. Gravity
"""

MOCK_SEGMENTS = [
    {"label": "Q1", "text": "Photosynthesis is the process..."},
    {"label": "Q2", "text": "Gravity pulls objects..."}
]

MOCK_GRADING_RESULT = {
    "marks_obtained": 4.5,
    "confidence_score": 0.9,
    "feedback": "Well done",
    "improvement_suggestion": "None"
}


# --- Mock Helpers ---

class MockRunnable(Runnable):
    def __init__(self, response_content=None):
        self.response_content = response_content
        
    def invoke(self, input, config=None, **kwargs):
        return AIMessage(content=self.response_content)
        
    async def ainvoke(self, input, config=None, **kwargs):
        return AIMessage(content=self.response_content)


@pytest.mark.anyio
class TestCheckingService:
    """Test paper checking business logic."""
    
    async def test_create_answer_key(self, get_db_session):
        """Test answer key creation."""
        async for db in get_db_session:
             # Need a valid QP ID, let's just make a fake one because the FK is mocked or we create one
             # Real integration test needs QP. Let's create one.
            from app.models.question_paper import QuestionPaper
            from app.models.user import User
            from app.models.role import Role
            from sqlalchemy import select
            
            # Setup User & Role
            result = await db.execute(select(Role).where(Role.name == "teacher"))
            role = result.scalar_one_or_none()
            if not role:
                role = Role(name="teacher", is_system_role=True)
                db.add(role)
                await db.commit()
            
            user = User(
                email=f"key_test_{uuid4().hex[:8]}@example.com",
                password_hash="pw",
                full_name="Key User",
                role_id=str(role.id)
            )
            db.add(user)
            await db.commit()
            
            # Setup QuestionPaper
            qp = QuestionPaper(
                user_id=str(user.id),
                title="Test Paper",
                subject="Science",
                grade_level="10",
                total_marks=100
                # removed content={} as it's not in model
            )
            db.add(qp)
            await db.commit()
            
            # Test Logic
            service = CheckingService(db)
            data = AnswerKeyCreate(
                question_paper_id=qp.id,
                content={
                    "1": AnswerCriteria(expected_answer="Ans1", max_marks=5),
                    "2": AnswerCriteria(expected_answer="Ans2", max_marks=5)
                }
            )
            
            key = await service.create_answer_key(data)
            assert key.content["1"]["expected_answer"] == "Ans1"
            assert str(key.question_paper_id) == str(qp.id)

    async def test_process_submission_workflow(self, get_db_session):
        """Test full OCR -> Grading pipeline."""
        from sqlalchemy import select
        async for db in get_db_session:
            # Setup User
            from app.models.user import User
            # Reuse logic or assume distinct due to test isolation (though session scope fixture might share)
            # Create user
            # (In production tests, use fixtures like 'teacher_user', 'student_user')
            
            stmt = select(User).limit(1)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            if not user:
                # Fallback if previous test didn't run or order differs
                # ... creation logic ...
                pass 
            
            # We need a fresh user to avoid conflicts? No, users table is fine.
            # Let's create a temp user for this test
            try:
                from app.models.role import Role
                result = await db.execute(select(Role).where(Role.name == "student"))
                role = result.scalar_one_or_none()
                if not role:
                    role = Role(name="student", is_system_role=True)
                    db.add(role)
                    await db.commit()

                user = User(
                    email=f"sub_test_{uuid4().hex[:8]}@example.com",
                    password_hash="pw",
                    full_name="Sub User",
                    role_id=str(role.id)
                )
                db.add(user)
                await db.commit()
            except:
                # If already exists or error, fetch existing (basic handling)
                pass

            
            # Mock OCR and LLM
            mock_ocr = MagicMock()
            mock_ocr.extract_text = AsyncMock(return_value=MOCK_OCR_TEXT)
            mock_ocr.segment_answers = MagicMock(return_value=MOCK_SEGMENTS)
            
            mock_llm_service = MagicMock()
            mock_runnable = MockRunnable(response_content=json.dumps(MOCK_GRADING_RESULT))
            type(mock_llm_service).llm = PropertyMock(return_value=mock_runnable)
            
            with patch("app.services.checking_service.OCRService", return_value=mock_ocr), \
                 patch("app.services.checking_service.get_llm_service", return_value=mock_llm_service):
                
                service = CheckingService(db)
                # Ensure the service instance uses our mocks
                service.ocr = mock_ocr
                service.llm = mock_llm_service # Override init
                
                # 1. Create Submission
                submission = await service.create_submission(
                    user_id=user.id,
                    input_url="http://test.com/paper.jpg"
                )
                assert submission.status == SubmissionStatus.UPLOADING
                
                # 2. Process
                await service.process_submission(submission.id)
                
                # 3. Verify
                await db.refresh(submission)
                assert submission.status == SubmissionStatus.COMPLETED
                assert submission.extracted_text == MOCK_OCR_TEXT
                assert len(submission.answers) == 2
                assert submission.answers[0].marks_obtained == 4.5
                assert submission.overall_score == 9.0  # 4.5 * 2


@pytest.mark.anyio
async def test_api_endpoints(client):
    """Test API registration."""
    response = await client.get("/openapi.json")
    paths = response.json()["paths"]
    # Router prefix is /paper-checking, and included in /api/v1
    assert "/api/v1/paper-checking/upload" in paths
    assert "/api/v1/paper-checking/answer-key" in paths
