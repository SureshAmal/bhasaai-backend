"""
BhashaAI Backend - Document Model

SQLAlchemy model for storing uploaded educational documents.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import DocumentStatus, FileType

if TYPE_CHECKING:
    from app.models.institution import Institution
    from app.models.user import User


class Document(Base):
    """
    Document model for educational content uploads.
    
    Stores metadata about uploaded documents (PDF, DOCX, TXT)
    that are used as source material for question generation.
    
    Attributes:
        id: UUID primary key
        user_id: Owner of the document
        institution_id: Associated institution (optional)
        filename: Original filename
        file_url: MinIO storage URL
        file_type: pdf, docx, txt
        file_size: Size in bytes
        mime_type: MIME type
        text_content: Extracted text (for search)
        metadata: Additional document metadata (JSON)
        processing_status: pending, processing, completed, failed
        page_count: Number of pages (for PDF/DOCX)
        language: Detected language (gu, en, gu-en)
        subject: Subject category
        grade_level: Grade level if applicable
        is_active: Soft delete flag
        created_at: Upload timestamp
        updated_at: Last update timestamp
    """
    
    __tablename__ = "documents"
    
    # Primary key
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.uuid_generate_v4(),
        nullable=False,
    )
    
    # Foreign keys
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="Document owner"
    )
    institution_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="SET NULL"),
        nullable=True,
        comment="Associated institution"
    )
    
    # File information
    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Original filename"
    )
    file_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="MinIO storage URL"
    )
    file_type: Mapped[FileType] = mapped_column(
        Enum(FileType, name="file_type"),
        nullable=False,
        comment="pdf, docx, txt"
    )
    file_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Size in bytes"
    )
    mime_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="application/octet-stream"
    )
    
    # Content
    text_content: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Extracted text content"
    )
    extra_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
        comment="Additional document metadata"
    )
    
    # Processing
    processing_status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, name="document_status"),
        nullable=False,
        default=DocumentStatus.PENDING,
        comment="Processing status"
    )
    page_count: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Number of pages"
    )
    
    # Classification
    language: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="Detected language (gu, en, gu-en)"
    )
    subject: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Subject category"
    )
    grade_level: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Grade level"
    )
    
    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    
    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="documents",
        lazy="selectin"
    )
    institution: Mapped[Optional["Institution"]] = relationship(
        "Institution",
        lazy="selectin"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_documents_user", "user_id"),
        Index("idx_documents_status", "processing_status"),
        Index("idx_documents_active", "is_active"),
        Index("idx_documents_created", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<Document(id={self.id}, filename={self.filename}, status={self.processing_status})>"
