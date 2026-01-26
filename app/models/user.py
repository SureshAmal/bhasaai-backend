"""
BhashaAI Backend - User Model

SQLAlchemy model for the users table.
"""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import LanguagePreference

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.institution import Institution
    from app.models.role import Role
    from app.models.user_session import UserSession
    from app.models.learning import LearningProfile


class User(Base):
    """
    User model for all system users.
    
    Represents admins, teachers, students, and parents.
    Supports bilingual profiles (English and Gujarati).
    
    Attributes:
        id: UUID primary key
        institution_id: FK to institution (optional for self-learners)
        role_id: FK to role (required)
        email: Unique login email
        password_hash: Bcrypt hashed password
        full_name: Full name in English
        full_name_gujarati: Full name in Gujarati
        phone: Contact phone number
        profile_image_url: Profile picture URL (MinIO)
        language_preference: Preferred language for AI responses
        grade_level: Student's grade (1-12, UG)
        subjects: Teacher's subjects array
        is_active: Account active status
        is_email_verified: Email verification status
        last_login_at: Last login timestamp
    """
    
    __tablename__ = "users"
    
    # Primary key
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.uuid_generate_v4(),
        nullable=False,
    )
    
    # Foreign keys
    institution_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="SET NULL"),
        nullable=True,
        comment="Associated institution"
    )
    role_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="RESTRICT"),
        nullable=False,
        comment="User's role"
    )
    
    # Authentication
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="Login email"
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Bcrypt hashed password"
    )
    
    # Profile info
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Full name in English"
    )
    full_name_gujarati: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Full name in Gujarati"
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True
    )
    profile_image_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Profile picture URL (MinIO)"
    )
    
    # Preferences
    language_preference: Mapped[LanguagePreference] = mapped_column(
        Enum(LanguagePreference, name="language_preference", create_type=True),
        nullable=False,
        default=LanguagePreference.GUJARATI,
        comment="gu, en, or gu-en"
    )
    
    # Educational info
    grade_level: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Student's grade (1-12, UG)"
    )
    subjects: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String),
        nullable=True,
        comment="Teacher's subjects array"
    )
    
    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True
    )
    is_email_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
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
    institution: Mapped[Optional["Institution"]] = relationship(
        "Institution",
        back_populates="users",
        lazy="selectin"
    )
    role: Mapped["Role"] = relationship(
        "Role",
        back_populates="users",
        lazy="selectin"
    )
    sessions: Mapped[List["UserSession"]] = relationship(
        "UserSession",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    documents: Mapped[List["Document"]] = relationship(
        "Document",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="noload"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_users_institution", "institution_id"),
        Index("idx_users_role", "role_id"),
        Index("idx_users_active", "is_active"),
    )
    
    learning_profile: Mapped[Optional["LearningProfile"]] = relationship(
        "LearningProfile",
        back_populates="user",
        uselist=False,
        lazy="selectin"
    )

    def has_permission(self, permission: str) -> bool:
        """
        Check if user has a specific permission via their role.
        
        Args:
            permission: Permission string to check
        
        Returns:
            bool: True if user has the permission
        """
        return self.role.has_permission(permission) if self.role else False
    
    def __repr__(self) -> str:
        return f"<User(email={self.email}, role={self.role.name if self.role else None})>"
