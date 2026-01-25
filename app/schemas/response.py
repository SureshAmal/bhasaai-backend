"""
BhashaAI Backend - Standard API Response Schemas

This module defines the standard response envelope used across all API endpoints.
All responses include bilingual message support (English and Gujarati).
"""

from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, Field

# Generic type for response data
T = TypeVar("T")


class PaginationMeta(BaseModel):
    """
    Pagination metadata for list responses.
    
    Attributes:
        page: Current page number (1-indexed)
        per_page: Number of items per page
        total_items: Total number of items across all pages
        total_pages: Total number of pages
        has_next: Whether there's a next page
        has_prev: Whether there's a previous page
    """
    
    page: int = Field(..., ge=1, description="Current page number")
    per_page: int = Field(..., ge=1, le=100, description="Items per page")
    total_items: int = Field(..., ge=0, description="Total items count")
    total_pages: int = Field(..., ge=0, description="Total pages count")
    has_next: bool = Field(..., description="Has next page")
    has_prev: bool = Field(..., description="Has previous page")


class APIResponse(BaseModel, Generic[T]):
    """
    Standard API response envelope.
    
    All API responses follow this structure for consistency.
    
    Attributes:
        success: Whether the operation was successful
        data: Response payload (type varies by endpoint)
        message: Human-readable message in English
        message_gu: Human-readable message in Gujarati
    
    Example:
        ```json
        {
            "success": true,
            "data": {"id": "uuid-here", "name": "Example"},
            "message": "Operation successful",
            "message_gu": "કામગીરી સફળ"
        }
        ```
    """
    
    success: bool = Field(
        ...,
        description="Whether the operation was successful"
    )
    data: Optional[T] = Field(
        default=None,
        description="Response data payload"
    )
    message: Optional[str] = Field(
        default=None,
        description="Human-readable message (English)"
    )
    message_gu: Optional[str] = Field(
        default=None,
        description="Human-readable message (Gujarati / ગુજરાતી)"
    )


class PaginatedResponse(APIResponse[T]):
    """
    Paginated API response with pagination metadata.
    
    Used for list endpoints that support pagination.
    
    Attributes:
        pagination: Pagination metadata
    """
    
    pagination: Optional[PaginationMeta] = Field(
        default=None,
        description="Pagination metadata"
    )


class ErrorDetail(BaseModel):
    """
    Error detail for validation and other errors.
    
    Attributes:
        loc: Location of the error (field path)
        msg: Error message
        type: Error type identifier
    """
    
    loc: list[str] = Field(..., description="Error location path")
    msg: str = Field(..., description="Error message")
    type: str = Field(..., description="Error type")


class ErrorResponse(BaseModel):
    """
    Standard error response structure.
    
    Attributes:
        success: Always False for errors
        error_code: Machine-readable error code
        message: Human-readable error message (English)
        message_gu: Human-readable error message (Gujarati)
        details: Additional error details (for validation errors)
    """
    
    success: bool = Field(default=False, description="Always false for errors")
    error_code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Error message (English)")
    message_gu: Optional[str] = Field(
        default=None,
        description="Error message (Gujarati / ગુજરાતી)"
    )
    details: Optional[list[ErrorDetail]] = Field(
        default=None,
        description="Detailed error information"
    )


class HealthResponse(BaseModel):
    """
    Health check response schema.
    
    Attributes:
        status: Service status (healthy, degraded, unhealthy)
        version: Application version
        environment: Current environment
        services: Status of dependent services
    """
    
    status: str = Field(..., description="Service health status")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Current environment")
    services: dict[str, Any] = Field(
        default_factory=dict,
        description="Status of dependent services"
    )


class TaskResponse(BaseModel):
    """
    Async task response for long-running operations.
    
    Attributes:
        task_id: Unique task identifier
        status: Current task status (pending, processing, completed, failed)
        estimated_seconds: Estimated time to completion
    """
    
    task_id: str = Field(..., description="Async task ID")
    status: str = Field(..., description="Task status")
    estimated_seconds: Optional[int] = Field(
        default=None,
        description="Estimated seconds to completion"
    )
