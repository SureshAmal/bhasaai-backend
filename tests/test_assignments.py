"""
BhashaAI Backend - Assignments API Tests

Tests for assignment submission, solution generation, and help sessions.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from uuid import uuid4

from app.main import app


@pytest.fixture(scope="module")
def anyio_backend():
    """Use asyncio backend for pytest-anyio."""
    return "asyncio"


@pytest.fixture(scope="module")
async def async_client():
    """Create async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture(scope="module")
async def auth_token(async_client: AsyncClient):
    """Get auth token for authenticated requests."""
    unique_email = f"assign_test_{uuid4().hex[:8]}@example.com"
    
    response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email,
            "password": "Test1234",
            "full_name": "Assignment Tester",
            "role": "student"
        }
    )
    
    token = response.json()["data"]["tokens"]["access_token"]
    return token


class TestAssignmentsAPI:
    """Test assignment endpoints."""
    
    @pytest.mark.anyio
    async def test_submit_assignment_solve(self, async_client: AsyncClient, auth_token: str):
        """Test submitting assignment for solution."""
        response = await async_client.post(
            "/api/v1/assignments/submit",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "question_text": "Solve 2x + 5 = 15",
                "subject": "Mathematics",
                "grade_level": "10",
                "mode": "solve",
                "language": "en"
            }
        )
        
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["question_text"] == "Solve 2x + 5 = 15"
        assert data["mode"] == "solve"
        # Status might be processing, completed, or failed (if no LLM key)
        assert data["status"] in ["pending", "processing", "completed", "failed"]

    @pytest.mark.anyio
    async def test_submit_assignment_help(self, async_client: AsyncClient, auth_token: str):
        """Test submitting assignment for help session."""
        response = await async_client.post(
            "/api/v1/assignments/submit",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "question_text": "What is photosynthesis?",
                "subject": "Science",
                "mode": "help",
                "language": "en"
            }
        )
        
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["mode"] == "help"
        
        # Check if help session was created (even if failed later)
        # Verify ID exists
        assert "id" in data

    @pytest.mark.anyio
    async def test_list_assignments(self, async_client: AsyncClient, auth_token: str):
        """Test listing assignments."""
        response = await async_client.get(
            "/api/v1/assignments",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert "assignments" in data
        assert len(data["assignments"]) >= 2  # We just created 2

    @pytest.mark.anyio
    async def test_submit_assignment_invalid(self, async_client: AsyncClient, auth_token: str):
        """Test submitting invalid assignment."""
        response = await async_client.post(
            "/api/v1/assignments/submit",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                # Missing question_text
                "subject": "Mathematics",
                "mode": "solve"
            }
        )
        
        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_get_assignment_not_found(self, async_client: AsyncClient, auth_token: str):
        """Test getting non-existent assignment."""
        fake_id = uuid4()
        response = await async_client.get(
            f"/api/v1/assignments/{fake_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 404

    @pytest.mark.anyio
    async def test_get_hint_no_session(self, async_client: AsyncClient, auth_token: str):
        """Test requesting hint for assignment without help session (or non-existent)."""
        # Create a solve assignment
        create_res = await async_client.post(
            "/api/v1/assignments/submit",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "question_text": "Quick solve",
                "mode": "solve"
            }
        )
        assign_id = create_res.json()["data"]["id"]
        
        # Try to get hint
        response = await async_client.post(
            f"/api/v1/assignments/{assign_id}/hint",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"request_next_level": True}
        )
        
        # Should fail as mode is solve, so no help session created
        # The service returns 400 if no active help session
        assert response.status_code == 400

class TestEndpointsExist:
    """Verify all endpoints are registered."""
    
    @pytest.mark.anyio
    async def test_openapi_includes_assignments(self, async_client: AsyncClient):
        """Test OpenAPI schema includes assignment endpoints."""
        response = await async_client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = response.json()
        paths = schema.get("paths", {})
        
        assert "/api/v1/assignments/submit" in paths
        assert "/api/v1/assignments" in paths
