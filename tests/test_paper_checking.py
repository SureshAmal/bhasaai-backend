"""
BhashaAI Backend - Paper Checking Tests

Tests for the paper checking API endpoints:
- Schema validation (unit tests)
- API endpoints (integration tests)

Run with: uv run pytest tests/test_paper_checking.py -v
"""

import pytest
from uuid import uuid4


# =============================================================================
# Test Data Fixtures
# =============================================================================

@pytest.fixture
def sample_answer_key_data():
    """Sample answer key creation data."""
    return {
        "title": "Science Unit Test - Answer Key",
        "subject": "science",
        "total_marks": 20,
        "answers": [
            {
                "question_number": 1,
                "type": "mcq",
                "correct_answer": "B",
                "max_marks": 2,
                "partial_marking": False,
            },
            {
                "question_number": 2,
                "type": "mcq",
                "correct_answer": "A",
                "max_marks": 2,
                "partial_marking": False,
            },
            {
                "question_number": 3,
                "type": "short_answer",
                "expected_answer": "Photosynthesis is the process by which plants convert sunlight into energy.",
                "keywords": ["photosynthesis", "plants", "sunlight", "energy"],
                "max_marks": 6,
                "partial_marking": True,
            },
            {
                "question_number": 4,
                "type": "long_answer",
                "expected_answer": "The water cycle consists of evaporation, condensation, precipitation, and collection.",
                "keywords": ["evaporation", "condensation", "precipitation", "collection"],
                "max_marks": 10,
                "partial_marking": True,
            },
        ],
        "marking_scheme": {
            "keyword_match_percent": 50,
            "semantic_similarity_threshold": 0.7,
        },
    }


# =============================================================================
# Schema Validation Tests (Unit Tests)
# =============================================================================

class TestSchemaValidation:
    """Tests for schema validation."""

    def test_answer_key_question_number_unique(self):
        """Test that duplicate question numbers are rejected."""
        from app.schemas.paper_checking import AnswerKeyCreate
        from pydantic import ValidationError
        
        data = {
            "title": "Test Key",
            "total_marks": 10,
            "answers": [
                {"question_number": 1, "type": "mcq", "correct_answer": "A", "max_marks": 5},
                {"question_number": 1, "type": "mcq", "correct_answer": "B", "max_marks": 5},  # Duplicate!
            ],
        }
        
        with pytest.raises(ValidationError):
            AnswerKeyCreate(**data)

    def test_answer_key_marks_sum_validation(self):
        """Test that answer marks must sum to total_marks."""
        from app.schemas.paper_checking import AnswerKeyCreate
        from pydantic import ValidationError
        
        data = {
            "title": "Test Key",
            "total_marks": 100,  # Total is 100
            "answers": [
                {"question_number": 1, "type": "mcq", "correct_answer": "A", "max_marks": 10},
                {"question_number": 2, "type": "mcq", "correct_answer": "B", "max_marks": 10},
                # Only 20 marks, but total is 100
            ],
        }
        
        with pytest.raises(ValidationError):
            AnswerKeyCreate(**data)

    def test_valid_answer_key_creation(self):
        """Test valid answer key schema."""
        from app.schemas.paper_checking import AnswerKeyCreate
        
        data = {
            "title": "Valid Test Key",
            "total_marks": 15,
            "answers": [
                {"question_number": 1, "type": "mcq", "correct_answer": "A", "max_marks": 5},
                {"question_number": 2, "type": "mcq", "correct_answer": "B", "max_marks": 5},
                {"question_number": 3, "type": "short_answer", "expected_answer": "Test answer", "max_marks": 5},
            ],
        }
        
        result = AnswerKeyCreate(**data)
        assert result.title == "Valid Test Key"
        assert result.total_marks == 15
        assert len(result.answers) == 3

    def test_valid_answer_item_mcq(self):
        """Test valid MCQ answer item creation."""
        from app.schemas.paper_checking import AnswerItem
        
        item = AnswerItem(
            question_number=1,
            type="mcq",
            correct_answer="A",
            max_marks=5,
        )
        
        assert item.question_number == 1
        assert item.type == "mcq"
        assert item.correct_answer == "A"

    def test_valid_answer_item_short_answer(self):
        """Test valid short answer item creation."""
        from app.schemas.paper_checking import AnswerItem
        
        item = AnswerItem(
            question_number=2,
            type="short_answer",
            expected_answer="The answer is 42",
            keywords=["answer", "42"],
            max_marks=10,
        )
        
        assert item.question_number == 2
        assert item.type == "short_answer"
        assert item.expected_answer == "The answer is 42"
        assert len(item.keywords) == 2


# =============================================================================
# API Endpoint Tests
# =============================================================================

@pytest.mark.asyncio(loop_scope="session")
class TestAnswerKeyEndpoints:
    """Tests for answer key CRUD endpoints."""

    async def test_create_answer_key_unauthorized(
        self,
        client,
        sample_answer_key_data: dict,
    ):
        """Test creating answer key without auth returns 401."""
        response = await client.post(
            "/api/v1/paper-checking/answer-keys",
            json=sample_answer_key_data,
        )
        assert response.status_code == 401

    async def test_list_answer_keys_unauthorized(
        self,
        client,
    ):
        """Test listing answer keys without auth returns 401."""
        response = await client.get(
            "/api/v1/paper-checking/answer-keys",
        )
        assert response.status_code == 401

    async def test_get_answer_key_unauthorized(
        self,
        client,
    ):
        """Test getting answer key without auth returns 401."""
        fake_id = str(uuid4())
        response = await client.get(
            f"/api/v1/paper-checking/answer-keys/{fake_id}",
        )
        assert response.status_code == 401


@pytest.mark.asyncio(loop_scope="session")
class TestPaperCheckEndpoints:
    """Tests for paper checking endpoints."""

    async def test_submit_paper_unauthorized(
        self,
        client,
    ):
        """Test paper submission without auth returns 401."""
        fake_id = str(uuid4())
        test_file_content = b"Test paper content"
        
        response = await client.post(
            "/api/v1/paper-checking/paper-checks",
            data={
                "answer_key_id": fake_id,
            },
            files={
                "file": ("test_paper.pdf", test_file_content, "application/pdf"),
            },
        )
        assert response.status_code == 401

    async def test_get_results_unauthorized(
        self,
        client,
    ):
        """Test getting results without auth returns 401."""
        fake_id = str(uuid4())
        response = await client.get(
            f"/api/v1/paper-checking/paper-checks/{fake_id}",
        )
        assert response.status_code == 401

    async def test_list_my_papers_unauthorized(
        self,
        client,
    ):
        """Test listing papers without auth returns 401."""
        response = await client.get(
            "/api/v1/paper-checking/my-papers",
        )
        assert response.status_code == 401
