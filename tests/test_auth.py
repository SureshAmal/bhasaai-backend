"""
BhashaAI Backend - Auth API Tests

Tests for authentication endpoints.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.config import settings
from app.db.session import get_db
from app.main import app
from app.models import Base, Role


# Test database URL - use same as main but could be different for isolation
TEST_DATABASE_URL = settings.database_url


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
async def test_db():
    """Get database session for test setup."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session() as session:
        yield session
    
    await engine.dispose()


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    @pytest.mark.anyio
    async def test_health_check(self, async_client: AsyncClient):
        """Test basic health endpoint."""
        response = await async_client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "status" in data["data"]


class TestAuthRegister:
    """Test user registration endpoint."""
    
    @pytest.mark.anyio
    async def test_register_success(self, async_client: AsyncClient):
        """Test successful user registration."""
        import uuid
        unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": unique_email,
                "password": "Test1234",
                "full_name": "Test User",
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "user" in data["data"]
        assert "tokens" in data["data"]
        assert data["data"]["user"]["email"] == unique_email
        assert "access_token" in data["data"]["tokens"]
        assert "refresh_token" in data["data"]["tokens"]
    
    @pytest.mark.anyio
    async def test_register_duplicate_email(self, async_client: AsyncClient):
        """Test registration with existing email returns error."""
        import uuid
        unique_email = f"dup_{uuid.uuid4().hex[:8]}@example.com"
        
        # First registration
        await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": unique_email,
                "password": "Test1234",
                "full_name": "First User",
            }
        )
        
        # Duplicate registration
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": unique_email,
                "password": "Test1234",
                "full_name": "Second User",
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "already registered" in data["message"].lower()
    
    @pytest.mark.anyio
    async def test_register_weak_password(self, async_client: AsyncClient):
        """Test registration with weak password fails validation."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "weak@example.com",
                "password": "weak",  # Too short, no uppercase, no digit
                "full_name": "Weak Password User",
            }
        )
        
        assert response.status_code == 422  # Pydantic validation error


class TestAuthLogin:
    """Test user login endpoint."""
    
    @pytest.mark.anyio
    async def test_login_success(self, async_client: AsyncClient):
        """Test successful login."""
        import uuid
        unique_email = f"login_{uuid.uuid4().hex[:8]}@example.com"
        password = "Test1234"
        
        # Register first
        await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": unique_email,
                "password": password,
                "full_name": "Login Test User",
            }
        )
        
        # Login
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": unique_email,
                "password": password,
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "tokens" in data["data"]
        assert "access_token" in data["data"]["tokens"]
    
    @pytest.mark.anyio
    async def test_login_wrong_password(self, async_client: AsyncClient):
        """Test login with wrong password."""
        import uuid
        unique_email = f"wrongpw_{uuid.uuid4().hex[:8]}@example.com"
        
        # Register
        await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": unique_email,
                "password": "Test1234",
                "full_name": "Wrong PW User",
            }
        )
        
        # Login with wrong password
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": unique_email,
                "password": "WrongPassword1",
            }
        )
        
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
    
    @pytest.mark.anyio
    async def test_login_nonexistent_user(self, async_client: AsyncClient):
        """Test login with non-existent email."""
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "Test1234",
            }
        )
        
        assert response.status_code == 401


class TestAuthMe:
    """Test get current user endpoint."""
    
    @pytest.mark.anyio
    async def test_get_me_authenticated(self, async_client: AsyncClient):
        """Test getting current user profile with valid token."""
        import uuid
        unique_email = f"me_{uuid.uuid4().hex[:8]}@example.com"
        
        # Register and get token
        register_response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": unique_email,
                "password": "Test1234",
                "full_name": "Me Test User",
            }
        )
        
        token = register_response.json()["data"]["tokens"]["access_token"]
        
        # Get profile
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["email"] == unique_email
    
    @pytest.mark.anyio
    async def test_get_me_unauthenticated(self, async_client: AsyncClient):
        """Test getting profile without token returns 401."""
        response = await async_client.get("/api/v1/auth/me")
        
        assert response.status_code == 401


class TestAuthRefresh:
    """Test token refresh endpoint."""
    
    @pytest.mark.anyio
    async def test_refresh_token_success(self, async_client: AsyncClient):
        """Test successful token refresh."""
        import uuid
        unique_email = f"refresh_{uuid.uuid4().hex[:8]}@example.com"
        
        # Register and get tokens
        register_response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": unique_email,
                "password": "Test1234",
                "full_name": "Refresh Test User",
            }
        )
        
        refresh_token = register_response.json()["data"]["tokens"]["refresh_token"]
        
        # Refresh
        response = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
    
    @pytest.mark.anyio
    async def test_refresh_invalid_token(self, async_client: AsyncClient):
        """Test refresh with invalid token fails."""
        response = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid.token.here"}
        )
        
        assert response.status_code == 401


class TestAuthLogout:
    """Test logout endpoint."""
    
    @pytest.mark.anyio
    async def test_logout_success(self, async_client: AsyncClient):
        """Test successful logout."""
        import uuid
        unique_email = f"logout_{uuid.uuid4().hex[:8]}@example.com"
        
        # Register
        register_response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": unique_email,
                "password": "Test1234",
                "full_name": "Logout Test User",
            }
        )
        
        refresh_token = register_response.json()["data"]["tokens"]["refresh_token"]
        
        # Logout
        response = await async_client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": refresh_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
