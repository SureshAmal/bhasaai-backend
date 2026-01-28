"""
BhashaAI Backend - Documents API

Endpoints for document upload and management.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from urllib.parse import quote
from sqlalchemy.ext.asyncio import AsyncSession
from io import BytesIO

from app.api.deps import get_current_user, get_db
from app.models import User
from app.schemas.document import (
    DocumentListResponse,
    DocumentResponse,
    DocumentUploadResponse,
)
from app.schemas.response import APIResponse
from app.services.document_service import DocumentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])


# Max file size: 50MB
MAX_FILE_SIZE = 50 * 1024 * 1024
ALLOWED_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "text/plain": "txt",
}


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload Document",
    description="Upload a PDF, DOCX, or TXT document for question generation.",
)
async def upload_document(
    file: UploadFile = File(...),
    subject: Optional[str] = Form(None),
    grade_level: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload an educational document.
    
    - **file**: PDF, DOCX, or TXT file (max 50MB)
    - **subject**: Subject category (optional)
    - **grade_level**: Target grade level (optional)
    """
    # Validate content type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "message": f"Unsupported file type: {file.content_type}",
                "message_gu": f"અસમર્થિત ફાઇલ પ્રકાર: {file.content_type}",
            }
        )
    
    # Read file content
    content = await file.read()
    
    # Validate size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "message": "File size exceeds 50MB limit",
                "message_gu": "ફાઇલનું કદ 50MB મર્યાદા કરતાં વધુ છે",
            }
        )
    
    # Upload document
    doc_service = DocumentService(db)
    document = await doc_service.upload_document(
        user_id=UUID(str(current_user.id)),
        file_data=content,
        filename=file.filename or "document",
        content_type=file.content_type,
        institution_id=UUID(str(current_user.institution_id)) if current_user.institution_id else None,
        subject=subject,
        grade_level=grade_level,
    )
    
    # Get download URL
    download_url = doc_service.get_download_url(document)
    
    return DocumentUploadResponse(
        data=DocumentResponse(
            id=UUID(str(document.id)),
            user_id=UUID(str(document.user_id)),
            institution_id=UUID(str(document.institution_id)) if document.institution_id else None,
            filename=document.filename,
            file_url=document.file_url,
            file_type=document.file_type.value,
            file_size=document.file_size,
            mime_type=document.mime_type,
            text_content=document.text_content,
            extra_metadata=document.extra_metadata,
            processing_status=document.processing_status.value,
            page_count=document.page_count,
            language=document.language,
            subject=document.subject,
            grade_level=document.grade_level,
            is_active=document.is_active,
            created_at=document.created_at,
            updated_at=document.updated_at,
            download_url=download_url,
        )
    )


@router.get(
    "",
    response_model=APIResponse,
    summary="List Documents",
    description="List all documents for the current user.",
)
async def list_documents(
    page: int = 1,
    per_page: int = 20,
    search: Optional[str] = None,
    file_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List user's documents with pagination and filtering.
    
    - **page**: Page number (default: 1)
    - **per_page**: Items per page (default: 20, max: 100)
    - **search**: Search by filename
    - **file_type**: Filter by file type
    """
    per_page = min(per_page, 100)
    
    doc_service = DocumentService(db)
    documents, total = await doc_service.list_documents(
        user_id=UUID(str(current_user.id)),
        page=page,
        per_page=per_page,
        search=search,
        file_type=file_type,
    )
    
    pages = (total + per_page - 1) // per_page if per_page > 0 else 0
    
    return APIResponse(
        success=True,
        data=DocumentListResponse(
            documents=[
                DocumentResponse(
                    id=UUID(str(doc.id)),
                    user_id=UUID(str(doc.user_id)),
                    institution_id=UUID(str(doc.institution_id)) if doc.institution_id else None,
                    filename=doc.filename,
                    file_url=doc.file_url,
                    file_type=doc.file_type.value,
                    file_size=doc.file_size,
                    mime_type=doc.mime_type,
                    processing_status=doc.processing_status.value,
                    page_count=doc.page_count,
                    language=doc.language,
                    subject=doc.subject,
                    grade_level=doc.grade_level,
                    is_active=doc.is_active,
                    created_at=doc.created_at,
                    updated_at=doc.updated_at,
                )
                for doc in documents
            ],
            total=total,
            page=page,
            per_page=per_page,
            pages=pages,
        )
    )


@router.get(
    "/{document_id}",
    response_model=APIResponse,
    summary="Get Document",
    description="Get document details by ID.",
)
async def get_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific document."""
    doc_service = DocumentService(db)
    document = await doc_service.get_document(
        document_id=document_id,
        user_id=UUID(str(current_user.id)),
    )
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "message": "Document not found",
                "message_gu": "ડોક્યુમેન્ટ મળ્યું નથી",
            }
        )
    
    download_url = doc_service.get_download_url(document)
    
    return APIResponse(
        success=True,
        data=DocumentResponse(
            id=UUID(str(document.id)),
            user_id=UUID(str(document.user_id)),
            institution_id=UUID(str(document.institution_id)) if document.institution_id else None,
            filename=document.filename,
            file_url=document.file_url,
            file_type=document.file_type.value,
            file_size=document.file_size,
            mime_type=document.mime_type,
            text_content=document.text_content,
            extra_metadata=document.extra_metadata,
            processing_status=document.processing_status.value,
            page_count=document.page_count,
            language=document.language,
            subject=document.subject,
            grade_level=document.grade_level,
            is_active=document.is_active,
            created_at=document.created_at,
            updated_at=document.updated_at,
            download_url=download_url,
        )
    )


@router.post(
    "/{document_id}/summary",
    response_model=APIResponse,
    summary="Generate Document Summary",
    description="Generate AI summary of the document content.",
)
async def summarize_document(
    document_id: UUID,
    language: Optional[str] = "gu",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate summary for a document.
    
    Args:
        document_id: Document UUID
        language: Output language ('gu' or 'en')
        
    Returns:
        Structured summary
    """
    doc_service = DocumentService(db)
    
    try:
        summary = await doc_service.summarize_document(
            document_id=document_id,
            user_id=UUID(str(current_user.id)),
            language=language or "gu",
        )
        
        return APIResponse(
            success=True,
            message="Summary generated successfully",
            message_gu="સારાંશ સફળતાપૂર્વક બનાવવામાં આવ્યો",
            data=summary
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "message": str(e),
                "message_gu": "સારાંશ બનાવવામાં નિષ્ફળ",
            }
        )
    except Exception as e:
        logger.error(f"Summary generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error"
        )


@router.delete(
    "/{document_id}",
    response_model=APIResponse,
    summary="Delete Document",
    description="Delete a document (soft delete).",
)
async def delete_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a document."""
    doc_service = DocumentService(db)
    deleted = await doc_service.delete_document(
        document_id=document_id,
        user_id=UUID(str(current_user.id)),
    )
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "message": "Document not found",
                "message_gu": "ડોક્યુમેન્ટ મળ્યું નથી",
            }
        )
    
    return APIResponse(
        success=True,
        message="Document deleted successfully",
        message_gu="ડોક્યુમેન્ટ સફળતાપૂર્વક કાઢી નાખ્યું",
    )


@router.get(
    "/{document_id}/download",
    status_code=status.HTTP_200_OK,
    summary="Download Document",
    description="Download the document file.",
)
async def download_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download document file."""
    doc_service = DocumentService(db)
    
    # Check access
    document = await doc_service.get_document(
        document_id=document_id,
        user_id=UUID(str(current_user.id)),
    )
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "message": "Document not found",
                "message_gu": "ડોક્યુમેન્ટ મળ્યું નથી",
            }
        )

    # Get file content
    try:
        file_content = doc_service.download_document_file(document)
        
        # Determine filename (encode for safe HTTP headers)
        filename = quote(document.filename)
        
        return StreamingResponse(
            BytesIO(file_content),
            media_type=document.mime_type,
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{filename}"
            }
        )
    except Exception as e:
        logger.error(f"Download failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Failed to retrieve file",
                "message_gu": "ફાઇલ પુનઃપ્રાપ્ત કરવામાં નિષ્ફળ",
            }
        )
