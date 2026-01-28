
import pytest
from httpx import AsyncClient
from uuid import uuid4

@pytest.mark.asyncio
async def test_generate_flashcards(client: AsyncClient, token_headers):
    """Test generating flashcards from topic."""
    response = await client.post(
        "/api/v1/flashcards/generate",
        headers=token_headers,
        json={
            "topic": "Solar System",
            "count": 5,
            "language": "en"
        }
    )
    if response.status_code != 200:
        print(response.json())
        
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) > 0
    assert "front" in data["data"][0]
    assert "back" in data["data"][0]


@pytest.mark.asyncio
async def test_create_deck(client: AsyncClient, token_headers):
    """Test creating a deck."""
    response = await client.post(
        "/api/v1/flashcards",
        headers=token_headers,
        json={
            "title": "My Test Deck",
            "description": "Testing deck creation",
            "subject": "Science",
            "cards": [
                {"front": "Q1", "back": "A1"},
                {"front": "Q2", "back": "A2"}
            ]
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    deck_id = data["data"]["id"]
    
    # Verify Get
    get_res = await client.get(f"/api/v1/flashcards/{deck_id}", headers=token_headers)
    assert get_res.status_code == 200
    deck = get_res.json()["data"]
    assert deck["title"] == "My Test Deck"
    assert len(deck["cards"]) == 2
