"""
BhashaAI Backend - SQLAlchemy Models Package

Exports all database models for use in the application.
"""

from app.models.base import Base, BaseModel, TimestampMixin, UUIDMixin
from app.models.enums import (
    AchievementCategory,
    AssignmentMode,
    AudioFileType,
    AudioRequestType,
    AudioType,
    BloomLevel,
    CheckedPaperStatus,
    DifficultyLevel,
    ExportFormat,
    FileFormat,
    GameType,
    InputType,
    InstitutionType,
    InteractionType,
    LanguagePreference,
    LeaderboardCategory,
    LeaderboardType,
    LearningLevel,
    MaterialType,
    PaperStatus,
    PartOfSpeech,
    ProcessingStatus,
    QuestionType,
    SubscriptionPlan,
)
from app.models.institution import Institution
from app.models.role import Role
from app.models.user import User
from app.models.user_session import UserSession

__all__ = [
    # Base
    "Base",
    "BaseModel",
    "UUIDMixin",
    "TimestampMixin",
    # Enums
    "InstitutionType",
    "SubscriptionPlan",
    "LanguagePreference",
    "ProcessingStatus",
    "PaperStatus",
    "QuestionType",
    "DifficultyLevel",
    "BloomLevel",
    "InputType",
    "AssignmentMode",
    "InteractionType",
    "MaterialType",
    "ExportFormat",
    "FileFormat",
    "CheckedPaperStatus",
    "LearningLevel",
    "PartOfSpeech",
    "AchievementCategory",
    "GameType",
    "LeaderboardType",
    "LeaderboardCategory",
    "AudioFileType",
    "AudioType",
    "AudioRequestType",
    # Core Models
    "Institution",
    "Role",
    "User",
    "UserSession",
]
