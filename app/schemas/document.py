"""
BhashaAI Backend - Document Schemas

Pydantic schemas for document upload and management.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentBase(BaseModel):
    """Base document schema."""
    
    filename: str = Field(..., min_length=1, max_length=255)
    subject: Optional[str] = Field(None, max_length=100)
    grade_level: Optional[str] = Field(None, max_length=20)


class DocumentCreate(DocumentBase):
    """Schema for document creation (after upload)."""
    
    file_url: str = Field(..., max_length=500)
    file_type: str = Field(..., description="pdf, docx, txt")
    file_size: int = Field(..., gt=0)
    mime_type: str = Field(..., max_length=100)


class DocumentUpdate(BaseModel):
    """Schema for document update."""
    
    subject: Optional[str] = Field(None, max_length=100)
    grade_level: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None


class DocumentResponse(BaseModel):
    """Schema for document response."""
    
    id: UUID
    user_id: UUID
    institution_id: Optional[UUID] = None
    filename: str
    file_url: str
    file_type: str
    file_size: int
    mime_type: str
    text_content: Optional[str] = None
    extra_metadata: dict[str, Any] = {}
    processing_status: str
    page_count: Optional[int] = None
    language: Optional[str] = None
    subject: Optional[str] = None
    grade_level: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    # Computed fields
    download_url: Optional[str] = None
    
    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    """Schema for paginated document list."""
    
    documents: list[DocumentResponse]
    total: int
    page: int
    per_page: int
    pages: int


class DocumentUploadResponse(BaseModel):
    """Schema for document upload response."""
    
    success: bool = True
    message: str = "Document uploaded successfully"
    message_gu: str = "ડોક્યુમેન્ટ સફળતાપૂર્વક અપલોડ થયું"
    data: DocumentResponse
