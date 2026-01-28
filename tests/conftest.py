"""
Pytest Configuration

Common fixtures and configuration for tests.
"""

import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def init_db():
    """Initialize database tables."""
    from app.db.session import engine
    from app.models.base import Base
    # Ensure all models are imported
    import app.models  # noqa
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    # Optional: cleanup
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create async HTTP client for testing."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def get_db_session():
    """Create database session for service tests."""
    from app.api.deps import get_db
    return get_db()


@pytest_asyncio.fixture
async def token_headers(client: AsyncClient):
    """Create a new user and return auth headers."""
    import uuid
    unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    password = "Test1234"
    
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email,
            "password": password,
            "full_name": "Test User",
        }
    )
    
    # If already exists, login instead (fallback)
    if response.status_code == 400:
        login_res = await client.post(
             "/api/v1/auth/login",
            json={
                "email": unique_email,
                "password": password,
            }
        )
        token = login_res.json()["data"]["tokens"]["access_token"]
    else:
        token = response.json()["data"]["tokens"]["access_token"]
        
    return {"Authorization": f"Bearer {token}"}
