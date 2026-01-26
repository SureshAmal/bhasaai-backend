"""
BhashaAI Backend - Teaching Tool Schemas

Pydantic schemas for Mind Maps, Lesson Plans, and Analogies.
"""

from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.teaching_tool import ToolType


# --- Mind Map Structures ---
class MindMapNode(BaseModel):
    """Recursive node structure for Mind Maps."""
    id: str
    label: str
    children: List["MindMapNode"] = []
    
    model_config = {"frozen": False}  # Allow recursion


# --- Lesson Plan Structures ---
class TimelineItem(BaseModel):
    """Single item in lesson timeline."""
    time: str
    activity: str
    description: str


class LessonPlan(BaseModel):
    """Structured lesson plan."""
    topic: str
    duration: str
    objectives: List[str]
    materials_needed: List[str]
    timeline: List[TimelineItem]
    homework: Optional[str] = None


# --- Analogy Structures ---
class ComparisonPoint(BaseModel):
    """Mapping between complex concept and simple analogy."""
    concept_part: str
    analogy_part: str
    explanation: str


class Analogy(BaseModel):
    """Analogy explanation."""
    concept: str
    analogy_story: str
    comparison_points: List[ComparisonPoint]
    takeaway: str


# --- API Request/Response Schemas ---

class ToolGenerateRequest(BaseModel):
    """Request to generate a teaching tool."""
    
    tool_type: ToolType
    topic: str = Field(..., min_length=1, max_length=255)
    subject: Optional[str] = None
    grade_level: Optional[str] = None
    language: str = Field("en", pattern="^(gu|en|gu-en)$")
    additional_instructions: Optional[str] = None


class TeachingToolResponse(BaseModel):
    """Response schema for teaching tool."""
    
    id: UUID
    user_id: UUID
    tool_type: ToolType
    topic: str
    subject: Optional[str] = None
    grade_level: Optional[str] = None
    content: dict[str, Any]  # Contains tool-specific structure
    language: str
    is_public: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class ToolListResponse(BaseModel):
    """Paginated list of tools."""
    
    tools: list[TeachingToolResponse]
    total: int
    page: int
    per_page: int
    pages: int
