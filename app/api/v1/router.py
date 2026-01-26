"""
BhashaAI Backend - API v1 Router

Main router that aggregates all API v1 endpoints.
"""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.documents import router as documents_router
from app.api.v1.health import router as health_router
from app.api.v1.question_papers import router as papers_router
from app.api.v1.assignments import router as assignments_router
from app.api.v1.teaching_tools import router as tools_router
from app.api.v1.paper_checking import router as checking_router
from app.api.v1.learning import router as learning_router

# Create main v1 router
api_v1_router = APIRouter()

# Include sub-routers
api_v1_router.include_router(
    health_router,
    prefix="/health",
    tags=["Health"],
)

api_v1_router.include_router(
    auth_router,
    tags=["Authentication"],
)

api_v1_router.include_router(
    documents_router,
    tags=["Documents"],
)

api_v1_router.include_router(
    papers_router,
    tags=["Question Papers"],
)

api_v1_router.include_router(
    assignments_router,
    tags=["Assignments"],
)

api_v1_router.include_router(
    tools_router,
    tags=["Teaching Tools"],
)

api_v1_router.include_router(
    checking_router,
    tags=["Paper Checking"],
)

api_v1_router.include_router(
    learning_router,
    tags=["Learning"],
)

# Placeholder routers for future implementation:
# api_v1_router.include_router(help_router, prefix="/help-sessions", tags=["Help Sessions"])
# api_v1_router.include_router(audio_router, prefix="/audio", tags=["Audio"])

