"""
BhashaAI Backend - Database Enums

Python Enums matching the database enums from database.dbml.
These are used with SQLAlchemy's Enum type for type safety.
"""

import enum


class InstitutionType(str, enum.Enum):
    """Type of educational institution."""
    SCHOOL = "school"
    COLLEGE = "college"
    COACHING = "coaching"
    SELF = "self"


class SubscriptionPlan(str, enum.Enum):
    """Institution subscription plan levels."""
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"


class LanguagePreference(str, enum.Enum):
    """User language preference for AI responses."""
    GUJARATI = "gu"
    ENGLISH = "en"
    BILINGUAL = "gu-en"


class ProcessingStatus(str, enum.Enum):
    """Status for async processing tasks."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentStatus(str, enum.Enum):
    """Status for document processing."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class FileType(str, enum.Enum):
    """Uploaded file types."""
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    IMAGE = "image"


class PaperStatus(str, enum.Enum):
    """Question paper status."""
    DRAFT = "draft"
    GENERATED = "generated"
    PUBLISHED = "published"


class QuestionType(str, enum.Enum):
    """Types of questions in papers."""
    MCQ = "mcq"
    SHORT_ANSWER = "short_answer"
    LONG_ANSWER = "long_answer"
    TRUE_FALSE = "true_false"
    FILL_BLANK = "fill_blank"


class DifficultyLevel(str, enum.Enum):
    """Question difficulty levels."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class BloomLevel(str, enum.Enum):
    """Bloom's taxonomy levels."""
    REMEMBER = "remember"
    UNDERSTAND = "understand"
    APPLY = "apply"
    ANALYZE = "analyze"
    EVALUATE = "evaluate"
    CREATE = "create"


class InputType(str, enum.Enum):
    """Assignment input types."""
    TEXT = "text"
    IMAGE = "image"
    PDF = "pdf"


class AssignmentMode(str, enum.Enum):
    """Assignment solving mode."""
    SOLVE = "solve"
    HELP = "help"


class InteractionType(str, enum.Enum):
    """Help session interaction types."""
    QUESTION = "question"
    ANSWER = "answer"
    HINT_REQUEST = "hint_request"
    HINT = "hint"
    GUIDANCE = "guidance"
    FORMULA = "formula"
    SUBMISSION = "submission"
    FEEDBACK = "feedback"


class MaterialType(str, enum.Enum):
    """Types of teaching materials."""
    LESSON_PLAN = "lesson_plan"
    STUDY_MATERIAL = "study_material"
    WORKSHEET = "worksheet"
    REFERENCE_NOTES = "reference_notes"


class ExportFormat(str, enum.Enum):
    """Export file formats."""
    HTML = "html"
    PPTX = "pptx"
    PDF = "pdf"


class FileFormat(str, enum.Enum):
    """Document file formats."""
    PDF = "pdf"
    DOCX = "docx"
    HTML = "html"
    MD = "md"


class CheckedPaperStatus(str, enum.Enum):
    """Status for checked papers."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    REVIEWED = "reviewed"
    APPROVED = "approved"


class LearningLevel(str, enum.Enum):
    """Gujarati learning proficiency levels."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class PartOfSpeech(str, enum.Enum):
    """Parts of speech for vocabulary."""
    NOUN = "noun"
    VERB = "verb"
    ADJECTIVE = "adjective"
    ADVERB = "adverb"
    PRONOUN = "pronoun"
    PREPOSITION = "preposition"
    CONJUNCTION = "conjunction"
    INTERJECTION = "interjection"


class AchievementCategory(str, enum.Enum):
    """Achievement/badge categories."""
    LEARNING = "learning"
    STREAK = "streak"
    VOCABULARY = "vocabulary"
    GRAMMAR = "grammar"
    GAMES = "games"
    SPECIAL = "special"


class GameType(str, enum.Enum):
    """Learning game types."""
    FLASHCARD = "flashcard"
    WORD_MATCH = "word_match"
    PICTURE_WORD = "picture_word"
    SPELLING = "spelling"
    SENTENCE_BUILDER = "sentence_builder"
    VERB_CONJUGATION = "verb_conjugation"
    FILL_BLANKS = "fill_blanks"
    AUDIO_QUIZ = "audio_quiz"
    SPEED_READING = "speed_reading"


class LeaderboardType(str, enum.Enum):
    """Leaderboard time periods."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    ALL_TIME = "all_time"


class LeaderboardCategory(str, enum.Enum):
    """Leaderboard ranking categories."""
    POINTS = "points"
    STREAK = "streak"
    VOCABULARY = "vocabulary"
    GAMES = "games"


class AudioFileType(str, enum.Enum):
    """Audio file formats."""
    MP3 = "mp3"
    WAV = "wav"
    WEBM = "webm"
    OGG = "ogg"


class AudioType(str, enum.Enum):
    """Types of audio content."""
    PRONUNCIATION = "pronunciation"
    TTS_OUTPUT = "tts_output"
    STT_INPUT = "stt_input"
    USER_RECORDING = "user_recording"
    VOCABULARY = "vocabulary"


class AudioRequestType(str, enum.Enum):
    """Audio service request types."""
    TTS = "tts"
    STT = "stt"
    PRONUNCIATION = "pronunciation"
