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
    DocumentStatus,
    ExportFormat,
    FileFormat,
    FileType,
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
    TranslationDirection,
)
from app.models.institution import Institution
from app.models.role import Role
from app.models.user import User
from app.models.user_session import UserSession
from app.models.document import Document
from app.models.question_paper import QuestionPaper, Question
from app.models.assignment import Assignment, AssignmentSolution, HelpSession
from app.models.teaching_tool import TeachingTool, ToolType
from app.models.paper_checking import (
    AnswerKey,
    CheckedPaper,
    CheckedPaperStatus as CheckedPaperStatusModel,
    Submission,
    SubmissionStatus,
    GradedAnswer,
)
from app.models.learning import (
    LearningProfile,
    VocabularyItem,
    UserWordProgress,
    GrammarTopic,
    Exercise,
    LearningDifficulty,
    ExerciseType,
)
from app.models.worksheet import Worksheet, WorksheetQuestion, WorksheetAttempt, WorksheetStatus, AttemptStatus
from app.models.dictionary import DictionaryEntry, UserDictionaryHistory

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
    "DocumentStatus",
    "FileType",
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
    # Phase 3 Models
    "Document",
    "QuestionPaper",
    "Question",
    # Phase 4 Models
    "Assignment",
    "AssignmentSolution",
    "HelpSession",
    # Phase 5 Models
    "TeachingTool",
    "ToolType",
    # Phase 6 Models
    "AnswerKey",
    "CheckedPaper",
    "CheckedPaperStatusModel",
    "Submission",
    "SubmissionStatus",
    "GradedAnswer",
    # Phase 7 Models
    "LearningProfile",
    "VocabularyItem",
    "UserWordProgress",
    "GrammarTopic",
    "Exercise",
    "DifficultyLevel",
    "ExerciseType",
    # Phase 8 Models
    "Worksheet",
    "WorksheetQuestion",
    "WorksheetAttempt",
    "WorksheetStatus",
    "AttemptStatus",
    # Phase 9 Models - Dictionary
    "DictionaryEntry",
    "UserDictionaryHistory",
    "TranslationDirection",
]
