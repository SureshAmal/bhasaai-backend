"""
BhashaAI Backend - Learning Tests

Tests for SM-2 Algorithm, Profile Tracking, and Lesson fetching.
"""

import pytest
from datetime import datetime
from uuid import uuid4
from sqlalchemy import select

from app.models.learning import VocabularyItem, UserWordProgress
from app.services.learning_service import LearningService


@pytest.mark.anyio
class TestLearningService:
    """Test learning business logic."""
    
    async def test_sm2_algorithm(self, get_db_session):
        """Test Spaced Repetition logic."""
        async for db in get_db_session:
            # Setup
            from app.models.user import User
            from app.models.role import Role
            
            # Ensure role exists
            result = await db.execute(select(Role).where(Role.name == "student"))
            role = result.scalar_one_or_none()
            if not role:
                role = Role(name="student", is_system_role=True)
                db.add(role)
                await db.commit()
            
            # Create User
            user_id = uuid4()
            user = User(
                id=user_id,
                email=f"learn_{user_id.hex[:8]}@example.com",
                password_hash="pw",
                full_name="Learn User",
                role_id=str(role.id)
            )
            db.add(user)
            await db.commit()
            
            service = LearningService(db)
            
            # Create a Vocab Item
            item = VocabularyItem(
                gujarati_word="સફરજન", 
                english_translation="Apple", 
                category="food"
            )
            db.add(item)
            await db.commit()
            await db.refresh(item)
            
            # 1. First Review (Correct -> 5)
            # Expect interval 1
            progress = await service.update_word_progress(user_id, item.id, 5)
            assert progress.interval_days == 1.0
            assert progress.repetitions == 1
            
            # 2. Second Review (Correct -> 4)
            # Expect interval = 6
            progress = await service.update_word_progress(user_id, item.id, 4)
            assert progress.interval_days == 6.0
            assert progress.repetitions == 2
            
            # 3. Third Review (Correct -> 5)
            # Interval = Prev(6) * EF(2.6) = 15.6
            
            progress = await service.update_word_progress(user_id, item.id, 5)
            assert progress.interval_days == pytest.approx(15.6)
            
            # 4. Fail (0)
            # Expect reset
            progress = await service.update_word_progress(user_id, item.id, 0)
            assert progress.interval_days == 1.0
            assert progress.repetitions == 0

    async def test_profile_creation(self, get_db_session):
         """Test profile auto-creation."""
         async for db in get_db_session:
             from app.models.user import User
             from app.models.role import Role
             
             # Role setup (reuse if exists, but for isolation valid)
             result = await db.execute(select(Role).where(Role.name == "student"))
             role = result.scalar_one_or_none()
             if not role:
                 role = Role(name="student", is_system_role=True)
                 db.add(role)
                 await db.commit()

             user_id = uuid4()
             user = User(
                id=user_id,
                email=f"prof_{user_id.hex[:8]}@example.com",
                password_hash="pw",
                full_name="Prof User",
                role_id=str(role.id)
             )
             db.add(user)
             await db.commit()
             
             service = LearningService(db)
             
             # Should create new
             profile = await service.get_or_create_profile(user_id)
             assert str(profile.user_id) == str(user_id)
             assert profile.streak_days == 0
             
             # Should fetch existing
             profile.total_xp = 100
             await db.commit()
             
             profile2 = await service.get_or_create_profile(user_id)
             assert profile2.total_xp == 100

@pytest.mark.anyio
async def test_api_endpoints(client):
    """Test Learning API registration."""
    response = await client.get("/openapi.json")
    paths = response.json()["paths"]
    assert "/api/v1/learning/profile" in paths
    assert "/api/v1/learning/vocabulary/daily" in paths
