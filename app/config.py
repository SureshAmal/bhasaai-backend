"""
BhashaAI Backend - Configuration Module

This module handles all application configuration using Pydantic Settings.
Settings are loaded from environment variables with sensible defaults.
"""

from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Attributes:
        app_env: Current environment (development, staging, production)
        app_debug: Enable debug mode
        app_secret_key: Secret key for cryptographic operations
        database_url: PostgreSQL connection string
        redis_url: Redis connection string
        jwt_secret_key: Secret key for JWT tokens
        cors_origins: List of allowed CORS origins
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # Application
    app_env: str = "development"
    app_debug: bool = True
    app_secret_key: str = "change-this-in-production-min-32-chars"
    app_name: str = "BhashaAI Backend"
    app_version: str = "0.1.0"
    
    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5434/education_ai"
    database_pool_size: int = 10
    
    # Redis
    redis_url: str = "redis://localhost:6381/0"
    celery_broker_url: str = "redis://localhost:6381/1"
    
    # JWT
    jwt_secret_key: str = "change-this-jwt-secret-in-production"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 30
    jwt_algorithm: str = "HS256"
    
    # AI/LLM
    cerebras_api_key: str = ""
    openai_api_key: str = ""
    google_api_key: str = ""
    llm_model: str = "gpt-4-turbo-preview"
    embedding_model: str = "text-embedding-3-small"
    
    # MinIO/S3
    minio_endpoint: str = "localhost:9002"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "education-ai"
    minio_secure: bool = False
    
    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:8000"
    
    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str) -> str:
        """Parse CORS origins from comma-separated string."""
        return v
    
    def get_cors_origins_list(self) -> List[str]:
        """Return CORS origins as a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.app_env == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.app_env == "production"
    
    @property
    def access_token_expire_minutes(self) -> int:
        """Alias for jwt_access_token_expire_minutes."""
        return self.jwt_access_token_expire_minutes
    
    @property
    def refresh_token_expire_days(self) -> int:
        """Alias for jwt_refresh_token_expire_days."""
        return self.jwt_refresh_token_expire_days


@lru_cache
def get_settings() -> Settings:
    """
    Get cached application settings.
    
    Uses lru_cache to ensure settings are only loaded once.
    
    Returns:
        Settings: Application settings instance
    """
    return Settings()


# Export settings instance for convenience
settings = get_settings()
