"""
BhashaAI Backend - Database Session Management

Provides async database session management using SQLAlchemy 2.0.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import settings

# Create async engine
# Using NullPool for development; switch to pool for production
engine = create_async_engine(
    settings.database_url,
    echo=settings.app_debug,
    pool_pre_ping=True,
    # Use NullPool in development for easier debugging
    # In production, use default pool with settings.database_pool_size
    poolclass=NullPool if settings.is_development else None,
)

# Create async session factory
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides an async database session.
    
    Yields a session and ensures it's properly closed after use.
    
    Yields:
        AsyncSession: Database session
    
    Example:
        @router.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database with required extensions and initial data.
    
    This should be called during application startup to ensure
    the database is properly configured.
    """
    async with engine.begin() as conn:
        # Enable required PostgreSQL extensions
        await conn.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")
        await conn.execute("CREATE EXTENSION IF NOT EXISTS \"vector\"")
        
    print("✅ Database initialized with required extensions")


async def close_db() -> None:
    """
    Close database connections.
    
    Should be called during application shutdown.
    """
    await engine.dispose()
    print("✅ Database connections closed")
