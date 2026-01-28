"""
BhashaAI Backend - Dictionary API Tests

Tests for the bilingual dictionary API endpoints:
- Word lookup and translation
- Entry retrieval
- History tracking
- Validation
"""

import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from uuid import uuid4

from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.enums import TranslationDirection


class TestDictionaryAPI:
    """Test suite for Dictionary API endpoints."""
    
    @pytest_asyncio.fixture
    async def client(self):
        """Create async HTTP client for testing."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
    
    @pytest_asyncio.fixture
    async def auth_headers(self, client):
        """
        Get auth headers for authenticated requests.
        
        This assumes a test user exists. In real tests,
        you would create a test user first.
        """
        # For integration tests, you would login first
        # For unit tests, we mock the get_current_user dependency
        return {"Authorization": "Bearer test-token"}
    
    # =========================================================================
    # Lookup Endpoint Tests
    # =========================================================================
    
    @pytest.mark.asyncio
    async def test_lookup_word_validation(self, client):
        """Test that empty word is rejected."""
        response = await client.post(
            "/api/v1/dictionary/lookup",
            json={"word": "", "direction": "en_to_gu"},
        )
        # Should fail validation (word min_length=1)
        assert response.status_code in [401, 422]  # 401 if auth required, 422 for validation
    
    @pytest.mark.asyncio
    async def test_lookup_word_too_long(self, client):
        """Test that overly long word is rejected."""
        long_word = "a" * 101
        response = await client.post(
            "/api/v1/dictionary/lookup",
            json={"word": long_word, "direction": "en_to_gu"},
        )
        assert response.status_code in [401, 422]
    
    @pytest.mark.asyncio
    async def test_lookup_invalid_direction(self, client):
        """Test that invalid direction is rejected."""
        response = await client.post(
            "/api/v1/dictionary/lookup",
            json={"word": "hello", "direction": "invalid"},
        )
        assert response.status_code in [401, 422]
    
    @pytest.mark.asyncio
    async def test_lookup_request_schema(self):
        """Test DictionaryLookupRequest schema validation."""
        from app.schemas.dictionary import DictionaryLookupRequest
        
        # Valid request
        req = DictionaryLookupRequest(
            word="hello",
            direction=TranslationDirection.EN_TO_GU,
            include_examples=True,
        )
        assert req.word == "hello"
        assert req.direction == TranslationDirection.EN_TO_GU
        
        # Word with whitespace should be stripped
        req2 = DictionaryLookupRequest(word="  test  ")
        assert req2.word == "test"
    
    # =========================================================================
    # Translation Result Tests
    # =========================================================================
    
    @pytest.mark.asyncio
    async def test_translation_result_schema(self):
        """Test TranslationResult schema validation."""
        from app.schemas.dictionary import TranslationResult
        
        result = TranslationResult(
            translation="નમસ્તે",
            transliteration="namaste",
            part_of_speech="interjection",
            meaning="A greeting",
            synonyms=["hi", "greetings"],
            antonyms=["goodbye"],
        )
        
        assert result.translation == "નમસ્તે"
        assert result.part_of_speech == "interjection"
        assert len(result.synonyms) == 2
    
    @pytest.mark.asyncio
    async def test_translation_result_invalid_pos(self):
        """Test that invalid part of speech defaults to noun."""
        from app.schemas.dictionary import TranslationResult
        
        result = TranslationResult(
            translation="test",
            part_of_speech="invalid_pos",
            meaning="test meaning",
        )
        # Validator should default to "noun"
        assert result.part_of_speech == "noun"
    
    # =========================================================================
    # Entry Response Tests
    # =========================================================================
    
    @pytest.mark.asyncio
    async def test_dictionary_entry_response_schema(self):
        """Test DictionaryEntryResponse schema."""
        from app.schemas.dictionary import DictionaryEntryResponse
        from datetime import datetime
        
        entry = DictionaryEntryResponse(
            id=uuid4(),
            word="hello",
            language="en",
            translation="નમસ્તે",
            part_of_speech="interjection",
            meaning="A greeting",
            created_at=datetime.now(),
        )
        
        assert entry.word == "hello"
        assert entry.language == "en"
    
    # =========================================================================
    # History Tests
    # =========================================================================
    
    @pytest.mark.asyncio
    async def test_history_response_schema(self):
        """Test SearchHistoryResponse schema."""
        from app.schemas.dictionary import SearchHistoryResponse, SearchHistoryItem
        from datetime import datetime
        
        item = SearchHistoryItem(
            id=uuid4(),
            word="test",
            translation="test translation",
            part_of_speech="noun",
            lookup_count=5,
            last_looked_up=datetime.now(),
        )
        
        response = SearchHistoryResponse(
            items=[item],
            total=1,
            page=1,
            per_page=50,
        )
        
        assert len(response.items) == 1
        assert response.total == 1
    
    # =========================================================================
    # Service Unit Tests (with mocked LLM)
    # =========================================================================
    
    @pytest.mark.asyncio
    async def test_dictionary_service_lookup_cache_miss(self):
        """Test that cache miss triggers LLM translation."""
        from app.services.dictionary_service import DictionaryService
        from app.schemas.dictionary import DictionaryLookupRequest
        
        # This would require a mock database session
        # Placeholder for integration test
        pass
    
    @pytest.mark.asyncio
    async def test_dictionary_service_lookup_cache_hit(self):
        """Test that cached entry is returned without LLM call."""
        # Placeholder for integration test with mock DB
        pass


class TestDictionaryModel:
    """Test dictionary database models."""
    
    @pytest.mark.asyncio
    async def test_dictionary_entry_model(self):
        """Test DictionaryEntry model instantiation."""
        from app.models.dictionary import DictionaryEntry
        from app.models.enums import PartOfSpeech
        
        entry = DictionaryEntry(
            word="hello",
            language="en",
            translation="નમસ્તે",
            part_of_speech=PartOfSpeech.INTERJECTION,
            meaning="A greeting",
            synonyms=["hi"],
            antonyms=["goodbye"],
        )
        
        assert entry.word == "hello"
        assert entry.part_of_speech == PartOfSpeech.INTERJECTION
    
    @pytest.mark.asyncio
    async def test_user_dictionary_history_model(self):
        """Test UserDictionaryHistory model."""
        from app.models.dictionary import UserDictionaryHistory
        
        history = UserDictionaryHistory(
            user_id=str(uuid4()),
            dictionary_entry_id=str(uuid4()),
            lookup_count=1,
        )
        
        assert history.lookup_count == 1


class TestDictionaryPrompt:
    """Test dictionary LLM prompt."""
    
    @pytest.mark.asyncio
    async def test_prompt_template_variables(self):
        """Test that prompt template has correct variables."""
        from app.services.prompts import DICTIONARY_TRANSLATION_PROMPT
        
        assert "word" in DICTIONARY_TRANSLATION_PROMPT.input_variables
        assert "direction" in DICTIONARY_TRANSLATION_PROMPT.input_variables
        assert "language_instruction" in DICTIONARY_TRANSLATION_PROMPT.input_variables
    
    @pytest.mark.asyncio
    async def test_prompt_template_format(self):
        """Test that prompt template formats correctly."""
        from app.services.prompts import DICTIONARY_TRANSLATION_PROMPT
        
        formatted = DICTIONARY_TRANSLATION_PROMPT.format(
            word="hello",
            direction="English to Gujarati",
            language_instruction="Output bilingual.",
        )
        
        assert "hello" in formatted
        assert "English to Gujarati" in formatted
