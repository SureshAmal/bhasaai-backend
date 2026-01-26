"""
BhashaAI Backend - Teaching Tools Tests

Tests for generating and listing teaching tools.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from uuid import uuid4
from langchain_core.runnables import Runnable
from langchain_core.messages import AIMessage

from app.models import ToolType
from app.services.teaching_tool_service import TeachingToolService
from app.schemas.teaching_tool import ToolGenerateRequest

# --- Mock Data ---

MOCK_MIND_MAP = {
    "id": "root",
    "label": "Photosynthesis",
    "children": [
        {"id": "1", "label": "Light Reaction", "children": []}
    ]
}

MOCK_LESSON_PLAN = {
    "topic": "Gravity",
    "duration": "45 minutes",
    "objectives": ["Understand gravity"],
    "materials_needed": ["Ball"],
    "timeline": [
        {"time": "0-5 min", "activity": "Intro", "description": "Drop ball"}
    ],
    "homework": "Read chapter 1"
}

MOCK_ANALOGY = {
    "concept": "Cell Nucleus",
    "analogy_story": "Like a brain...",
    "comparison_points": [],
    "takeaway": "Control center"
}

# --- Mock Infrastructure ---

class MockRunnable(Runnable):
    def __init__(self, response_content=None):
        self.response_content = response_content
        
    def invoke(self, input, config=None, **kwargs):
        return AIMessage(content=self.response_content)
        
    async def ainvoke(self, input, config=None, **kwargs):
        return AIMessage(content=self.response_content)


@pytest.mark.anyio
class TestTeachingToolService:
    """Test service logic with mocked LLM."""
    
    async def test_generate_mind_map(self, get_db_session):
        """Test mind map generation."""
        from app.models.user import User
        
        async for db in get_db_session:
            # Create user
            user = User(
                email=f"map_test_{uuid4().hex[:8]}@example.com",
                password_hash="hashed",
                full_name="Map User",
                role_id=uuid4() # We assume role check is skipped or mocked, but actually user needs a valid FK? 
                # Wait, FK constraint might fail if role doesn't exist.
                # Let's reuse the role logic from previous tests if we are strict.
            )
            # Actually, let's just create a role first to be safe, or assume the fixture handles it?
            # The previous test used explicit role creation.
            
            # Let's simplify: Mock the DB add/commit? No, let's use the real DB session but create dependencies.
            # Copy-paste the User creation logic from test_assignment_flow
            from app.models.role import Role
            from sqlalchemy import select
            
            result = await db.execute(select(Role).where(Role.name == "teacher"))
            role = result.scalar_one_or_none()
            if not role:
                role = Role(name="teacher", is_system_role=True)
                db.add(role)
                await db.commit()
                await db.refresh(role)
            
            user.role_id = str(role.id)
            db.add(user)
            await db.commit()
            
            # Mock LLM
            mock_llm_service = MagicMock()
            mock_runnable = MockRunnable(response_content=json.dumps(MOCK_MIND_MAP))
            type(mock_llm_service).llm = PropertyMock(return_value=mock_runnable)
            
            with patch("app.services.teaching_tool_service.get_llm_service", return_value=mock_llm_service):
                service = TeachingToolService(db)
                
                request = ToolGenerateRequest(
                    tool_type=ToolType.MIND_MAP,
                    topic="Photosynthesis",
                    subject="Biology",
                    grade_level="10"
                )
                
                tool = await service.generate_tool(user.id, request)
                
                assert tool.tool_type == ToolType.MIND_MAP
                assert tool.topic == "Photosynthesis"
                assert tool.content["label"] == "Photosynthesis"

    async def test_generate_lesson_plan(self, get_db_session):
        """Test lesson plan generation."""
        from app.models.user import User
        from app.models.role import Role
        from sqlalchemy import select
        
        async for db in get_db_session:
             # Get teacher role
            result = await db.execute(select(Role).where(Role.name == "teacher"))
            role = result.scalar_one_or_none()
            if not role:
                role = Role(name="teacher", is_system_role=True)
                db.add(role)
                await db.commit()
            
            user = User(
                email=f"plan_test_{uuid4().hex[:8]}@example.com",
                password_hash="hashed",
                full_name="Plan User",
                role_id=str(role.id)
            )
            db.add(user)
            await db.commit()
            
            # Mock LLM
            mock_llm_service = MagicMock()
            mock_runnable = MockRunnable(response_content=json.dumps(MOCK_LESSON_PLAN))
            type(mock_llm_service).llm = PropertyMock(return_value=mock_runnable)
            
            with patch("app.services.teaching_tool_service.get_llm_service", return_value=mock_llm_service):
                service = TeachingToolService(db)
                
                request = ToolGenerateRequest(
                    tool_type=ToolType.LESSON_PLAN,
                    topic="Gravity",
                    subject="Physics"
                )
                
                tool = await service.generate_tool(user.id, request)
                
                assert tool.tool_type == ToolType.LESSON_PLAN
                assert tool.content["homework"] == "Read chapter 1"

    async def test_list_tools(self, get_db_session):
        """Test listing tools."""
        from app.models.user import User
        from app.models.role import Role
        from sqlalchemy import select
        
        async for db in get_db_session:
             # Get teacher role
            result = await db.execute(select(Role).where(Role.name == "teacher"))
            role = result.scalar_one_or_none()
            if not role:
                role = Role(name="teacher", is_system_role=True)
                db.add(role)
                await db.commit()
            
            user = User(
                email=f"list_test_{uuid4().hex[:8]}@example.com",
                password_hash="hashed",
                full_name="List User",
                role_id=str(role.id)
            )
            db.add(user)
            await db.commit()
            
            # Mock LLM for generation
            mock_llm_service = MagicMock()
            mock_runnable = MockRunnable(response_content=json.dumps(MOCK_ANALOGY))
            type(mock_llm_service).llm = PropertyMock(return_value=mock_runnable)
            
            with patch("app.services.teaching_tool_service.get_llm_service", return_value=mock_llm_service):
                service = TeachingToolService(db)
                
                # Generate 2 tools
                await service.generate_tool(user.id, ToolGenerateRequest(
                    tool_type=ToolType.ANALOGY, topic="T1"
                ))
                await service.generate_tool(user.id, ToolGenerateRequest(
                    tool_type=ToolType.ANALOGY, topic="T2"
                ))
                
                # List
                tools, _ = await service.list_tools(user.id)
                assert len(tools) >= 2


@pytest.mark.anyio
async def test_api_endpoints_exist(client):
    """Smoke test to ensure endpoints are registered."""
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/v1/teaching-tools/generate" in paths
    assert "/api/v1/teaching-tools" in paths
