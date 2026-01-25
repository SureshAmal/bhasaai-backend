"""
BhashaAI Backend - Authentication Service

Business logic for user authentication operations.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.core.exceptions import (
    AuthenticationError,
    NotFoundError,
    ValidationError,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
    verify_refresh_token,
)
from app.models import Role, User, UserSession
from app.schemas import (
    AuthResponse,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)


class AuthService:
    """
    Authentication service handling registration, login, and token management.
    
    Provides methods for:
    - User registration
    - Login with email/password
    - Token refresh
    - Session management
    - Logout
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize auth service with database session.
        
        Args:
            db: Async SQLAlchemy session
        """
        self.db = db
    
    async def register(
        self,
        user_data: UserCreate,
        role_name: str = "student"
    ) -> AuthResponse:
        """
        Register a new user.
        
        Args:
            user_data: User registration data
            role_name: Role to assign (default: student)
        
        Returns:
            AuthResponse with user info and tokens
        
        Raises:
            ValidationError: If email already exists
            NotFoundError: If role not found
        """
        # Check if email already exists
        existing = await self.db.execute(
            select(User).where(User.email == user_data.email)
        )
        if existing.scalar_one_or_none():
            raise ValidationError(
                message="Email already registered",
                message_gu="ઈમેઈલ પહેલેથી રજિસ્ટર્ડ છે",
            )
        
        # Get role
        role_result = await self.db.execute(
            select(Role).where(Role.name == role_name)
        )
        role = role_result.scalar_one_or_none()
        if not role:
            raise NotFoundError(
                message=f"Role '{role_name}' not found",
                message_gu=f"ભૂમિકા '{role_name}' મળી નથી",
            )
        
        # Create user
        user = User(
            email=user_data.email,
            password_hash=get_password_hash(user_data.password),
            full_name=user_data.full_name,
            full_name_gujarati=user_data.full_name_gujarati,
            phone=user_data.phone,
            language_preference=user_data.language_preference,
            grade_level=user_data.grade_level,
            institution_id=user_data.institution_id,
            role_id=role.id,
        )
        
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user, ["role", "institution"])
        
        # Generate tokens
        tokens = await self._create_session(user)
        
        return AuthResponse(
            user=UserResponse.model_validate(user),
            tokens=tokens,
        )
    
    async def login(
        self,
        login_data: UserLogin,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuthResponse:
        """
        Authenticate user and create session.
        
        Args:
            login_data: Email and password
            ip_address: Client IP address
            user_agent: Client user agent
        
        Returns:
            AuthResponse with user info and tokens
        
        Raises:
            AuthenticationError: If credentials are invalid
        """
        # Find user by email
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.role), selectinload(User.institution))
            .where(User.email == login_data.email)
        )
        user = result.scalar_one_or_none()
        
        if not user or not verify_password(login_data.password, user.password_hash):
            raise AuthenticationError(
                message="Invalid email or password",
                message_gu="અમાન્ય ઈમેઈલ અથવા પાસવર્ડ",
            )
        
        if not user.is_active:
            raise AuthenticationError(
                message="Account is deactivated",
                message_gu="ખાતું નિષ્ક્રિય છે",
            )
        
        # Update last login
        user.last_login_at = datetime.now(timezone.utc)
        
        # Generate tokens with session
        tokens = await self._create_session(
            user,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        await self.db.commit()
        
        return AuthResponse(
            user=UserResponse.model_validate(user),
            tokens=tokens,
        )
    
    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_token: JWT refresh token
        
        Returns:
            New TokenResponse with fresh tokens
        
        Raises:
            AuthenticationError: If refresh token is invalid
        """
        # Verify refresh token
        payload = verify_refresh_token(refresh_token)
        if not payload:
            raise AuthenticationError(
                message="Invalid or expired refresh token",
                message_gu="અમાન્ય અથવા સમાપ્ત થયેલ રિફ્રેશ ટોકન",
            )
        
        user_id = payload.get("sub")
        token_id = payload.get("jti")
        
        # Find session
        result = await self.db.execute(
            select(UserSession)
            .options(selectinload(UserSession.user))
            .where(
                UserSession.id == token_id,
                UserSession.user_id == user_id,
                UserSession.is_active == True,
            )
        )
        session = result.scalar_one_or_none()
        
        if not session or not session.is_valid():
            raise AuthenticationError(
                message="Session expired or invalid",
                message_gu="સેશન સમાપ્ત અથવા અમાન્ય",
            )
        
        # Invalidate old session and create new one (token rotation)
        session.is_active = False
        
        # Create new tokens
        new_tokens = await self._create_session(session.user)
        
        await self.db.commit()
        
        return new_tokens
    
    async def logout(self, refresh_token: str) -> bool:
        """
        Logout user by invalidating session.
        
        Args:
            refresh_token: JWT refresh token
        
        Returns:
            True if logout successful
        """
        payload = verify_refresh_token(refresh_token)
        if not payload:
            return False
        
        token_id = payload.get("jti")
        
        # Invalidate session
        result = await self.db.execute(
            select(UserSession).where(UserSession.id == token_id)
        )
        session = result.scalar_one_or_none()
        
        if session:
            session.is_active = False
            await self.db.commit()
        
        return True
    
    async def logout_all(self, user_id: UUID) -> int:
        """
        Logout from all sessions.
        
        Args:
            user_id: User ID
        
        Returns:
            Number of sessions invalidated
        """
        result = await self.db.execute(
            select(UserSession).where(
                UserSession.user_id == user_id,
                UserSession.is_active == True,
            )
        )
        sessions = result.scalars().all()
        
        for session in sessions:
            session.is_active = False
        
        await self.db.commit()
        
        return len(sessions)
    
    async def get_current_user(self, user_id: UUID) -> User:
        """
        Get current user by ID.
        
        Args:
            user_id: User UUID
        
        Returns:
            User model with role and institution
        
        Raises:
            NotFoundError: If user not found
        """
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.role), selectinload(User.institution))
            .where(User.id == user_id, User.is_active == True)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise NotFoundError(
                message="User not found",
                message_gu="વપરાશકર્તા મળ્યો નથી",
            )
        
        return user
    
    async def _create_session(
        self,
        user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> TokenResponse:
        """
        Create new session with tokens.
        
        Args:
            user: User model
            ip_address: Client IP
            user_agent: Client user agent
        
        Returns:
            TokenResponse with access and refresh tokens
        """
        from uuid import uuid4
        
        # Create session ID
        session_id = uuid4()
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.refresh_token_expire_days
        )
        
        # Create tokens
        access_token = create_access_token(
            data={"sub": str(user.id), "role": user.role.name if user.role else None}
        )
        refresh_token = create_refresh_token(
            data={"sub": str(user.id), "jti": str(session_id)}
        )
        
        # Create session record
        session = UserSession(
            id=session_id,
            user_id=user.id,
            refresh_token=refresh_token,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at,
        )
        
        self.db.add(session)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.access_token_expire_minutes * 60,
        )
