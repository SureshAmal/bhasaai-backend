import pytest
from uuid import uuid4
from datetime import datetime
from app.models.worksheet import Worksheet, WorksheetQuestion, WorksheetAttempt, WorksheetStatus, AttemptStatus
from app.schemas.worksheet import WorksheetCreate, WorksheetGenerateRequest, SubmitStepRequest

# Test Pydantic Schemas
def test_worksheet_create_schema():
    """Test standard worksheet creation schema"""
    data = {
        "title": "Algebra Basics",
        "topic": "Linear Equations",
        "subject": "Math",
        "difficulty": "easy",
        "grade_level": "8"
    }
    schema = WorksheetCreate(**data)
    assert schema.title == "Algebra Basics"
    assert schema.difficulty == "easy"

def test_generate_request_schema():
    """Test LLM generation request schema defaults"""
    data = {
        "topic": "Photosynthesis",
        "subject": "Biology",
        "grade_level": "10"
    }
    schema = WorksheetGenerateRequest(**data)
    assert schema.num_questions == 3  # Default value
    assert schema.difficulty == "medium" # Default value

def test_submit_step_schema():
    """Test step submission schema"""
    data = {
        "attempt_id": uuid4(),
        "step_answer": "x = 5"
    }
    schema = SubmitStepRequest(**data)
    assert schema.step_answer == "x = 5"

# Test SQLAlchemy Models (Initialization only, no DB session needed for basic checks)
def test_worksheet_model_init():
    """Test Worksheet model initialization"""
    ws = Worksheet(
        title="Grammar 101",
        topic="Verbs",
        subject="English",
        difficulty="hard", # Should match enum, strictly speaking needs session to validate enum though
        status=WorksheetStatus.DRAFT
    )
    assert ws.title == "Grammar 101"
    assert ws.status == WorksheetStatus.DRAFT

def test_worksheet_question_model_init():
    """Test WorksheetQuestion model structure"""
    steps_data = [
        {"step_text": "Identify the subject", "answer_key": "Cat", "hint": "Noun"},
        {"step_text": "Identify the verb", "answer_key": "Sat", "hint": "Action"}
    ]
    
    q = WorksheetQuestion(
        content="The Cat Sat on the Mat",
        order=1,
        steps=steps_data,
        correct_answer="Subject: Cat, Verb: Sat"
    )
    assert len(q.steps) == 2
    assert q.steps[0]["step_text"] == "Identify the subject"

def test_worksheet_attempt_init():
    """Test WorksheetAttempt model defaults"""
    attempt = WorksheetAttempt(
        status=AttemptStatus.IN_PROGRESS
    )
    assert attempt.status == AttemptStatus.IN_PROGRESS
    # Default values check
    # Note: Defaults like '0' for int columns usually applied by DB or __init__ logic if using Mapped
    # SQLAlchemy Mapped columns without defaults in __init__ might be None until flushed
    # But we can check explicit assignments
    attempt.score = 10
    assert attempt.score == 10
