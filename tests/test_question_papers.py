"""
BhashaAI Backend - Documents and Question Papers API Tests

Tests for document upload and question paper generation endpoints.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from io import BytesIO

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
    import uuid
    unique_email = f"doctest_{uuid.uuid4().hex[:8]}@example.com"
    
    response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email,
            "password": "Test1234",
            "full_name": "Doc Test User",
        }
    )
    
    token = response.json()["data"]["tokens"]["access_token"]
    return token


class TestDocumentsAPI:
    """Test document endpoints."""
    
    @pytest.mark.anyio
    async def test_upload_document_unauthorized(self, async_client: AsyncClient):
        """Test upload without auth returns 401."""
        response = await async_client.post(
            "/api/v1/documents/upload",
            files={"file": ("test.txt", b"test content", "text/plain")},
        )
        assert response.status_code == 401
    
    @pytest.mark.anyio
    async def test_list_documents_empty(self, async_client: AsyncClient, auth_token: str):
        """Test listing documents returns empty list for new user."""
        response = await async_client.get(
            "/api/v1/documents",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    @pytest.mark.anyio
    async def test_get_document_not_found(self, async_client: AsyncClient, auth_token: str):
        """Test getting non-existent document returns 404."""
        import uuid
        fake_id = uuid.uuid4()
        
        response = await async_client.get(
            f"/api/v1/documents/{fake_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 404


class TestQuestionPapersAPI:
    """Test question paper endpoints."""
    
    @pytest.mark.anyio
    async def test_generate_paper_unauthorized(self, async_client: AsyncClient):
        """Test generation without auth returns 401."""
        response = await async_client.post(
            "/api/v1/question-papers/generate",
            json={
                "title": "Test Paper",
                "subject": "Mathematics",
                "topic": "Algebra",
            }
        )
        assert response.status_code == 401
    
    @pytest.mark.anyio
    async def test_list_papers_empty(self, async_client: AsyncClient, auth_token: str):
        """Test listing papers returns empty for new user."""
        response = await async_client.get(
            "/api/v1/question-papers",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    @pytest.mark.anyio
    async def test_get_paper_not_found(self, async_client: AsyncClient, auth_token: str):
        """Test getting non-existent paper returns 404."""
        import uuid
        fake_id = uuid.uuid4()
        
        response = await async_client.get(
            f"/api/v1/question-papers/{fake_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 404
    
    @pytest.mark.anyio
    async def test_generate_paper_no_source(self, async_client: AsyncClient, auth_token: str):
        """Test generation without source returns 400."""
        response = await async_client.post(
            "/api/v1/question-papers/generate",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "title": "Test Paper",
                "subject": "Mathematics",
                # Missing: document_id, topic, or context
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["success"] is False


class TestEndpointsExist:
    """Verify all endpoints are registered."""
    
    @pytest.mark.anyio
    async def test_openapi_includes_documents(self, async_client: AsyncClient):
        """Test OpenAPI schema includes document endpoints."""
        response = await async_client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = response.json()
        paths = schema.get("paths", {})
        
        assert "/api/v1/documents/upload" in paths
        assert "/api/v1/documents" in paths
    
    @pytest.mark.anyio
    async def test_openapi_includes_question_papers(self, async_client: AsyncClient):
        """Test OpenAPI schema includes question paper endpoints."""
        response = await async_client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = response.json()
        paths = schema.get("paths", {})
        
        assert "/api/v1/question-papers/generate" in paths
        assert "/api/v1/question-papers" in paths
