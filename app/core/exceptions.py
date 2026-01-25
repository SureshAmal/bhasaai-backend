"""
BhashaAI Backend - Custom Exceptions

Defines custom exceptions with bilingual error messages.
"""

from typing import Any, Optional

from fastapi import HTTPException, status


class BhashaAIException(Exception):
    """
    Base exception for BhashaAI application.
    
    Attributes:
        message: Error message in English
        message_gu: Error message in Gujarati
        error_code: Machine-readable error code
    """
    
    def __init__(
        self,
        message: str,
        message_gu: Optional[str] = None,
        error_code: str = "INTERNAL_ERROR",
    ):
        self.message = message
        self.message_gu = message_gu or message
        self.error_code = error_code
        super().__init__(message)


class NotFoundException(BhashaAIException):
    """Exception raised when a resource is not found."""
    
    def __init__(
        self,
        resource: str = "Resource",
        resource_gu: Optional[str] = None,
    ):
        resource_gu = resource_gu or resource
        super().__init__(
            message=f"{resource} not found",
            message_gu=f"{resource_gu} મળ્યું નથી",
            error_code="NOT_FOUND",
        )


class UnauthorizedException(BhashaAIException):
    """Exception raised for authentication failures."""
    
    def __init__(
        self,
        message: str = "Authentication required",
        message_gu: Optional[str] = None,
    ):
        super().__init__(
            message=message,
            message_gu=message_gu or "પ્રમાણીકરણ જરૂરી છે",
            error_code="UNAUTHORIZED",
        )


class ForbiddenException(BhashaAIException):
    """Exception raised for authorization failures."""
    
    def __init__(
        self,
        message: str = "Access denied",
        message_gu: Optional[str] = None,
    ):
        super().__init__(
            message=message,
            message_gu=message_gu or "ઍક્સેસ નકારવામાં આવી",
            error_code="FORBIDDEN",
        )


class ValidationException(BhashaAIException):
    """Exception raised for validation errors."""
    
    def __init__(
        self,
        message: str,
        message_gu: Optional[str] = None,
        details: Optional[list[dict[str, Any]]] = None,
    ):
        super().__init__(
            message=message,
            message_gu=message_gu or "માન્યતા ભૂલ",
            error_code="VALIDATION_ERROR",
        )
        self.details = details or []


class ConflictException(BhashaAIException):
    """Exception raised for resource conflicts (e.g., duplicate entries)."""
    
    def __init__(
        self,
        message: str = "Resource already exists",
        message_gu: Optional[str] = None,
    ):
        super().__init__(
            message=message,
            message_gu=message_gu or "સંસાધન પહેલેથી અસ્તિત્વમાં છે",
            error_code="CONFLICT",
        )


class ServiceUnavailableException(BhashaAIException):
    """Exception raised when an external service is unavailable."""
    
    def __init__(
        self,
        service: str = "Service",
        service_gu: Optional[str] = None,
    ):
        service_gu = service_gu or service
        super().__init__(
            message=f"{service} is currently unavailable",
            message_gu=f"{service_gu} હાલમાં અનુપલબ્ધ છે",
            error_code="SERVICE_UNAVAILABLE",
        )


class RateLimitException(BhashaAIException):
    """Exception raised when rate limit is exceeded."""
    
    def __init__(
        self,
        retry_after: int = 60,
    ):
        super().__init__(
            message=f"Rate limit exceeded. Please retry after {retry_after} seconds",
            message_gu=f"દર મર્યાદા ઓળંગી. કૃપા કરીને {retry_after} સેકન્ડ પછી ફરી પ્રયાસ કરો",
            error_code="RATE_LIMIT_EXCEEDED",
        )
        self.retry_after = retry_after


def raise_http_exception(
    exception: BhashaAIException,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    headers: Optional[dict[str, str]] = None,
) -> None:
    """
    Convert BhashaAIException to HTTPException and raise it.
    
    Args:
        exception: Custom exception instance
        status_code: HTTP status code
        headers: Optional response headers
    
    Raises:
        HTTPException: FastAPI HTTP exception
    """
    detail = {
        "success": False,
        "error_code": exception.error_code,
        "message": exception.message,
        "message_gu": exception.message_gu,
    }
    
    if isinstance(exception, ValidationException):
        detail["details"] = exception.details
    
    raise HTTPException(
        status_code=status_code,
        detail=detail,
        headers=headers,
    )


# Aliases for compatibility
AuthenticationError = UnauthorizedException
NotFoundError = NotFoundException
ValidationError = ValidationException
