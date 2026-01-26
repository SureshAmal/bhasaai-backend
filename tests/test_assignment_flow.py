"""
BhashaAI Backend - Assignment Flow Tests

Tests the complete flow of assignment checking and help sessions
by mocking the LLM service to verify application logic.
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from uuid import uuid4

from app.services.assignment_service import AssignmentService
from app.schemas.assignment import AssignmentSubmit
from app.models.enums import AssignmentMode, ProcessingStatus

# Mock data
MOCK_SOLUTION = {
    "steps": [
        {"step": 1, "description": "Identify variables"},
        {"step": 2, "description": "Apply formula"}
    ],
    "final_answer": "x = 5",
    "explanation": "Simple algebraic equation",
    "difficulty": "easy"
}

MOCK_HINT_L0 = {
    "hint": "What is the first step?",
    "level": 0,
    "is_complete": False
}

MOCK_HINT_L1 = {
    "hint": "Isolate the variable x",
    "level": 1,
    "is_complete": False
}


from langchain_core.runnables import Runnable
from langchain_core.messages import AIMessage

# Custom Mock Runnable to handle LangChain pipe behavior
class MockRunnable(Runnable):
    def __init__(self, response_content=None, side_effects=None):
        self.response_content = response_content
        self.side_effects = side_effects or []
        
    def invoke(self, input, config=None, **kwargs):
        if self.side_effects:
            content = self.side_effects.pop(0)
            return AIMessage(content=content)
        return AIMessage(content=self.response_content)
        
    async def ainvoke(self, input, config=None, **kwargs):
        if self.side_effects:
            content = self.side_effects.pop(0)
            return AIMessage(content=content)
        return AIMessage(content=self.response_content)


import json

@pytest.mark.anyio
async def test_solve_assignment_flow(get_db_session):
    """Test the full flow of solving an assignment."""
    from app.models.user import User
    from app.models.role import Role
    from sqlalchemy import select
    
    async for db in get_db_session:
        # Get or create student role
        result = await db.execute(select(Role).where(Role.name == "student"))
        role = result.scalar_one_or_none()
        if not role:
            role = Role(name="student", is_system_role=True)
            db.add(role)
            await db.commit()
            await db.refresh(role)
        
        # Create test user
        user = User(
            email=f"flow_test_{uuid4().hex[:8]}@example.com",
            password_hash="hashed_pw",
            full_name="Flow Tester",
            role_id=str(role.id)
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        # Mock LLM service
        mock_llm_service = MagicMock()
        mock_runnable = MockRunnable(response_content=json.dumps(MOCK_SOLUTION))
        type(mock_llm_service).llm = PropertyMock(return_value=mock_runnable)
        
        with patch("app.services.assignment_service.get_llm_service", return_value=mock_llm_service):
            service = AssignmentService(db)
            
            # 1. Submit Assignment
            data = AssignmentSubmit(
                question_text="Solve 2x = 10",
                mode=AssignmentMode.SOLVE,
                subject="Math"
            )
            assignment = await service.create_assignment(user.id, data)
            
            # Refresh to load relationships
            await db.refresh(assignment)
            
            # Verify Status
            if assignment.status == ProcessingStatus.FAILED:
                 print(f"Assignment Failed: {assignment.extra_metadata}")
            
            assert assignment.status == ProcessingStatus.COMPLETED
            
            # Verify Solution
            assert assignment.solution is not None
            assert assignment.solution.final_answer == "x = 5"


@pytest.mark.anyio
async def test_help_session_flow(get_db_session):
    """Test the progress of a Socratic help session."""
    from app.models.user import User
    from app.models.role import Role
    from sqlalchemy import select

    async for db in get_db_session:
        # Get or create student role
        result = await db.execute(select(Role).where(Role.name == "student"))
        role = result.scalar_one_or_none()
        if not role:
            role = Role(name="student", is_system_role=True)
            db.add(role)
            await db.commit()
            await db.refresh(role)

        # Create test user
        user = User(
            email=f"help_test_{uuid4().hex[:8]}@example.com",
            password_hash="hashed_pw",
            full_name="Help Tester",
            role_id=str(role.id)
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        # Mock LLM service
        mock_llm_service = MagicMock()
        mock_runnable = MockRunnable(side_effects=[
            json.dumps(MOCK_HINT_L0),
            json.dumps(MOCK_HINT_L1)
        ])
        type(mock_llm_service).llm = PropertyMock(return_value=mock_runnable)
        
        with patch("app.services.assignment_service.get_llm_service", return_value=mock_llm_service):
            service = AssignmentService(db)
            
            # 1. Start Help Session
            data = AssignmentSubmit(
                question_text="Help with 2x = 10",
                mode=AssignmentMode.HELP,
                subject="Math"
            )
            assignment = await service.create_assignment(user.id, data)
            
            # Refresh to load relationships
            await db.refresh(assignment)
             
            # Verify Session Created
            assert assignment.help_session is not None
            assert assignment.help_session.current_hint_level == 0
            
            # 2. Request Next Hint
            hint_data = await service.generate_hint(
                session=assignment.help_session,
                assignment=assignment,
                student_response="I don't know",
                request_next_level=True
            )
            
            # Verify Progress to Level 1
            assert hint_data["level"] == 1
            assert assignment.help_session.current_hint_level == 1
