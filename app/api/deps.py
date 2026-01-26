"""
BhashaAI Backend - API Dependencies

Common dependencies used across API endpoints.
"""

from typing import Annotated, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import verify_access_token
from app.db.session import get_db
from app.models import User

# Security scheme for JWT authentication
security = HTTPBearer(auto_error=False)


async def get_current_user_optional(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Optional[User]:
    """
    Get current user from JWT token (optional).
    
    Returns None if no valid token is provided.
    Used for endpoints that work with or without authentication.
    
    Args:
        credentials: HTTP Bearer credentials
        db: Database session
    
    Returns:
        Optional[User]: User model or None
    """
    if credentials is None:
        return None
    
    try:
        token = credentials.credentials
        payload = verify_access_token(token)
        
        if not payload:
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        result = await db.execute(
            select(User)
            .options(selectinload(User.role), selectinload(User.institution))
            .where(User.id == UUID(user_id), User.is_active == True)
        )
        return result.scalar_one_or_none()
        
    except Exception:
        return None


async def get_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    Get current user from JWT token (required).
    
    Raises HTTPException if no valid token is provided.
    Used for protected endpoints that require authentication.
    
    Args:
        credentials: HTTP Bearer credentials
        db: Database session
    
    Returns:
        User: User model
    
    Raises:
        HTTPException: If token is missing or invalid
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "error_code": "UNAUTHORIZED",
                "message": "Authentication required",
                "message_gu": "પ્રમાણીકરણ જરૂરી છે"
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        token = credentials.credentials
        payload = verify_access_token(token)
        
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "success": False,
                    "error_code": "INVALID_TOKEN",
                    "message": "Invalid or expired token",
                    "message_gu": "અમાન્ય અથવા સમાપ્ત ટોકન"
                },
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "success": False,
                    "error_code": "INVALID_TOKEN",
                    "message": "Invalid token payload",
                    "message_gu": "અમાન્ય ટોકન પેલોડ"
                },
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        result = await db.execute(
            select(User)
            .options(selectinload(User.role), selectinload(User.institution))
            .where(User.id == UUID(user_id), User.is_active == True)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "success": False,
                    "error_code": "USER_NOT_FOUND",
                    "message": "User not found or inactive",
                    "message_gu": "વપરાશકર્તા મળ્યો નથી અથવા નિષ્ક્રિય"
                },
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "error_code": "AUTH_ERROR",
                "message": str(e),
                "message_gu": "પ્રમાણીકરણ ભૂલ"
            },
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Get current active user.
    
    Verifies that the user account is active.
    
    Args:
        current_user: User from token
    
    Returns:
        User: Active user model
    
    Raises:
        HTTPException: If user account is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error_code": "ACCOUNT_INACTIVE",
                "message": "User account is inactive",
                "message_gu": "વપરાશકર્તા ખાતું નિષ્ક્રિય છે"
            }
        )
    return current_user


def require_permissions(*permissions: str):
    """
    Dependency factory to require specific permissions.
    
    Args:
        permissions: Required permission strings
    
    Returns:
        Dependency function that checks permissions
    
    Example:
        @router.get("/admin", dependencies=[Depends(require_permissions("admin:read"))])
        async def admin_endpoint():
            ...
    """
    async def check_permissions(
        current_user: Annotated[User, Depends(get_current_active_user)],
    ) -> User:
        required = set(permissions)
        
        # Check if user has required permissions via role
        for perm in required:
            if not current_user.has_permission(perm):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "success": False,
                        "error_code": "INSUFFICIENT_PERMISSIONS",
                        "message": f"Missing permission: {perm}",
                        "message_gu": f"પરવાનગી ખૂટે છે: {perm}"
                    }
                )
        return current_user
    
    return check_permissions


def require_role(*roles: str):
    """
    Dependency factory to require specific roles.
    
    Args:
        roles: Allowed role names
    
    Returns:
        Dependency function that checks role
    """
    async def check_role(
        current_user: Annotated[User, Depends(get_current_active_user)],
    ) -> User:
        if current_user.role and current_user.role.name in roles:
            return current_user
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error_code": "ROLE_REQUIRED",
                "message": f"Required role: {', '.join(roles)}",
                "message_gu": f"જરૂરી ભૂમિકા: {', '.join(roles)}"
            }
        )
    
    return check_role
