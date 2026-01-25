"""
BhashaAI Backend - Database Initialization

Script to initialize database with default data.
Run with: uv run python -m app.db.init_db
"""

import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_maker
from app.models import Role

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default system roles with permissions
DEFAULT_ROLES = [
    {
        "name": "super_admin",
        "display_name": "Super Admin",
        "display_name_gujarati": "સુપર એડમિન",
        "permissions": {"all": True},
        "is_system_role": True,
    },
    {
        "name": "institution_admin",
        "display_name": "Institution Admin",
        "display_name_gujarati": "સંસ્થા એડમિન",
        "permissions": {
            "manage_users": True,
            "manage_content": True,
            "view_analytics": True,
        },
        "is_system_role": True,
    },
    {
        "name": "teacher",
        "display_name": "Teacher",
        "display_name_gujarati": "શિક્ષક",
        "permissions": {
            "create_papers": True,
            "check_papers": True,
            "create_materials": True,
            "view_student_progress": True,
        },
        "is_system_role": True,
    },
    {
        "name": "student",
        "display_name": "Student",
        "display_name_gujarati": "વિદ્યાર્થી",
        "permissions": {
            "solve_assignments": True,
            "use_help_mode": True,
            "learn_gujarati": True,
            "view_own_progress": True,
        },
        "is_system_role": True,
    },
    {
        "name": "parent",
        "display_name": "Parent",
        "display_name_gujarati": "વાલી",
        "permissions": {
            "view_progress": True,
            "view_reports": True,
        },
        "is_system_role": True,
    },
]


async def seed_roles(db: AsyncSession) -> None:
    """
    Seed default roles into the database.
    
    Args:
        db: Async database session
    """
    logger.info("Seeding default roles...")
    
    for role_data in DEFAULT_ROLES:
        # Check if role exists
        result = await db.execute(
            select(Role).where(Role.name == role_data["name"])
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            logger.info(f"  Role '{role_data['name']}' already exists, skipping")
            continue
        
        # Create role
        role = Role(**role_data)
        db.add(role)
        logger.info(f"  Created role: {role_data['name']}")
    
    await db.commit()
    logger.info("Roles seeded successfully!")


async def init_db() -> None:
    """
    Initialize the database with required data.
    
    Creates default roles and any other required initial data.
    """
    logger.info("Initializing database...")
    
    async with async_session_maker() as db:
        await seed_roles(db)
    
    logger.info("Database initialization complete!")


def main() -> None:
    """Entry point for running initialization."""
    asyncio.run(init_db())


if __name__ == "__main__":
    main()
