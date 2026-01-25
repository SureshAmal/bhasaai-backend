"""
BhashaAI Backend - Authentication API

API endpoints for user authentication.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models import User
from app.schemas import (
    APIResponse,
    AuthResponse,
    TokenRefresh,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from app.services import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=APIResponse[AuthResponse],
    status_code=201,
    summary="Register a new user",
    description="Create a new user account. Default role is 'student'.",
)
async def register(
    user_data: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    role: str = "student",
) -> APIResponse[AuthResponse]:
    """
    Register a new user account.
    
    - **email**: Valid email address (unique)
    - **password**: Min 8 chars, must include uppercase, lowercase, digit
    - **full_name**: User's name in English
    - **full_name_gujarati**: Optional Gujarati name
    - **language_preference**: gu, en, or gu-en (default: gu)
    
    Returns user info and JWT tokens.
    """
    auth_service = AuthService(db)
    result = await auth_service.register(user_data, role_name=role)
    
    return APIResponse(
        success=True,
        data=result,
        message="Registration successful",
        message_gu="નોંધણી સફળ",
    )


@router.post(
    "/login",
    response_model=APIResponse[AuthResponse],
    summary="Login with email and password",
    description="Authenticate user and receive JWT tokens.",
)
async def login(
    login_data: UserLogin,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    user_agent: Annotated[str | None, Header()] = None,
) -> APIResponse[AuthResponse]:
    """
    Login with email and password.
    
    Returns user info and JWT tokens (access + refresh).
    Access token expires in 30 minutes (configurable).
    Refresh token expires in 7 days.
    """
    auth_service = AuthService(db)
    
    # Get client IP
    ip_address = request.client.host if request.client else None
    
    result = await auth_service.login(
        login_data,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    
    return APIResponse(
        success=True,
        data=result,
        message="Login successful",
        message_gu="લૉગિન સફળ",
    )


@router.post(
    "/refresh",
    response_model=APIResponse[TokenResponse],
    summary="Refresh access token",
    description="Get new access token using refresh token.",
)
async def refresh_token(
    token_data: TokenRefresh,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> APIResponse[TokenResponse]:
    """
    Refresh the access token.
    
    Send the refresh token to get a new access token.
    The old refresh token is invalidated (token rotation).
    """
    auth_service = AuthService(db)
    result = await auth_service.refresh_token(token_data.refresh_token)
    
    return APIResponse(
        success=True,
        data=result,
        message="Token refreshed",
        message_gu="ટોકન રિફ્રેશ થયું",
    )


@router.post(
    "/logout",
    response_model=APIResponse[dict],
    summary="Logout current session",
    description="Invalidate the current refresh token.",
)
async def logout(
    token_data: TokenRefresh,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> APIResponse[dict]:
    """
    Logout from current session.
    
    Invalidates the refresh token. Access tokens remain valid
    until they expire (stateless).
    """
    auth_service = AuthService(db)
    await auth_service.logout(token_data.refresh_token)
    
    return APIResponse(
        success=True,
        data={"logged_out": True},
        message="Logged out successfully",
        message_gu="સફળતાપૂર્વક લૉગઆઉટ થયું",
    )


@router.get(
    "/me",
    response_model=APIResponse[UserResponse],
    summary="Get current user",
    description="Get the currently authenticated user's profile.",
)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> APIResponse[UserResponse]:
    """
    Get current authenticated user's profile.
    
    Requires valid JWT access token in Authorization header.
    """
    return APIResponse(
        success=True,
        data=UserResponse.model_validate(current_user),
        message="User profile retrieved",
        message_gu="વપરાશકર્તા પ્રોફાઇલ મેળવ્યું",
    )


@router.post(
    "/logout-all",
    response_model=APIResponse[dict],
    summary="Logout from all devices",
    description="Invalidate all refresh tokens for the current user.",
)
async def logout_all(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> APIResponse[dict]:
    """
    Logout from all devices/sessions.
    
    Invalidates all refresh tokens for the authenticated user.
    """
    auth_service = AuthService(db)
    count = await auth_service.logout_all(current_user.id)
    
    return APIResponse(
        success=True,
        data={"sessions_invalidated": count},
        message=f"Logged out from {count} session(s)",
        message_gu=f"{count} સેશન(s)માંથી લૉગઆઉટ થયું",
    )
