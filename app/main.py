"""
BhashaAI Backend - FastAPI Application Entry Point

This module initializes the FastAPI application with all middleware,
routers, and configuration. It also sets up OpenAPI documentation
and exports swagger.json automatically.
"""

import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

from app.api.v1.router import api_v1_router
from app.config import settings
from app.core.exceptions import (
    BhashaAIException,
    ForbiddenException,
    NotFoundException,
    UnauthorizedException,
    ValidationException,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifespan context manager for startup and shutdown events.
    
    Handles:
        - Database connection pool initialization
        - Cache warming
        - Resource cleanup on shutdown
    
    Args:
        app: FastAPI application instance
    
    Yields:
        None
    """
    # Startup
    print(f"Starting {settings.app_name} v{settings.app_version}")
    print(f"Environment: {settings.app_env}")
    print(f"Debug mode: {settings.app_debug}")
    
    # Generate OpenAPI spec file on startup
    generate_openapi_spec(app)
    
    yield
    
    # Shutdown
    print("Shutting down application...")


def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        FastAPI: Configured FastAPI application instance
    """
    app = FastAPI(
        title=settings.app_name,
        description="""
## BhashaAI - Generative AI for Education & Gujarati Language Technologies

A comprehensive API for educational AI services supporting:

- **Question Paper Generation** - AI-powered question paper creation from educational content
- **Assignment Help** - Socratic tutoring and step-by-step solutions
- **Teaching Tools** - Mind maps, slides, and study materials generation
- **Paper Checking** - OCR-based automated evaluation with Gujarati support
- **Gujarati Learning** - Vocabulary, grammar, and gamified learning
- **Audio Services** - STT/TTS for Gujarati language

### Authentication
All protected endpoints require JWT Bearer token authentication.

### Bilingual Support
Responses include both English and Gujarati (ગુજરાતી) messages.
        """,
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
        contact={
            "name": "BhashaAI Team",
            "email": "support@bhashaai.com",
        },
        license_info={
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT",
        },
        openapi_tags=[
            {
                "name": "Health",
                "description": "Health check and service status endpoints",
            },
            {
                "name": "Authentication",
                "description": "User registration, login, and token management",
            },
            {
                "name": "Question Papers",
                "description": "AI-powered question paper generation and management",
            },
            {
                "name": "Assignments",
                "description": "Assignment submission and AI-generated solutions",
            },
            {
                "name": "Help Sessions",
                "description": "Socratic tutoring and interactive help",
            },
            {
                "name": "Teaching Tools",
                "description": "Mind maps, slides, and educational materials",
            },
            {
                "name": "Paper Checking",
                "description": "OCR-based paper evaluation and grading",
            },
            {
                "name": "Learning",
                "description": "Gujarati language learning features",
            },
            {
                "name": "Audio",
                "description": "Speech-to-text and text-to-speech services",
            },
        ],
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.get_cors_origins_list(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API routers
    app.include_router(api_v1_router, prefix="/api/v1")
    
    # Exception handlers
    @app.exception_handler(ValidationException)
    async def validation_exception_handler(request: Request, exc: ValidationException):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "error_code": exc.error_code,
                "message": exc.message,
                "message_gu": exc.message_gu,
            },
        )
    
    @app.exception_handler(UnauthorizedException)
    async def unauthorized_exception_handler(request: Request, exc: UnauthorizedException):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "success": False,
                "error_code": exc.error_code,
                "message": exc.message,
                "message_gu": exc.message_gu,
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    @app.exception_handler(NotFoundException)
    async def not_found_exception_handler(request: Request, exc: NotFoundException):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "success": False,
                "error_code": exc.error_code,
                "message": exc.message,
                "message_gu": exc.message_gu,
            },
        )
    
    @app.exception_handler(ForbiddenException)
    async def forbidden_exception_handler(request: Request, exc: ForbiddenException):
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "success": False,
                "error_code": exc.error_code,
                "message": exc.message,
                "message_gu": exc.message_gu,
            },
        )
    
    @app.exception_handler(BhashaAIException)
    async def bhashaai_exception_handler(request: Request, exc: BhashaAIException):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "error_code": exc.error_code,
                "message": exc.message,
                "message_gu": exc.message_gu,
            },
        )
    
    return app


def generate_openapi_spec(app: FastAPI) -> None:
    """
    Generate OpenAPI specification and save as swagger.json.
    
    This function creates a proper swagger.json file that can be used
    with external tools, API documentation generators, and client SDK generators.
    
    Args:
        app: FastAPI application instance
    """
    try:
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
            tags=app.openapi_tags,
            contact=app.contact,
            license_info=app.license_info,
        )
        
        # Add server URLs
        openapi_schema["servers"] = [
            {
                "url": "http://localhost:8000",
                "description": "Development server",
            },
            {
                "url": "https://api.bhashaai.com",
                "description": "Production server",
            },
        ]
        
        # Add security schemes
        openapi_schema["components"] = openapi_schema.get("components", {})
        openapi_schema["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "JWT access token obtained from /api/v1/auth/login",
            },
            "RefreshToken": {
                "type": "apiKey",
                "in": "header",
                "name": "X-Refresh-Token",
                "description": "JWT refresh token for obtaining new access tokens",
            },
        }
        
        # Save to file
        spec_path = Path(__file__).parent.parent / "openapi" / "swagger.json"
        spec_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(spec_path, "w", encoding="utf-8") as f:
            json.dump(openapi_schema, f, indent=2, ensure_ascii=False)
        
        print(f"OpenAPI spec generated: {spec_path}")
        
    except Exception as e:
        print(f"Warning: Could not generate OpenAPI spec: {e}")


# Create the application instance
app = create_application()


# Custom OpenAPI schema override for additional customization
def custom_openapi():
    """
    Generate custom OpenAPI schema with additional fields.
    
    This function caches the schema after first generation.
    
    Returns:
        dict: OpenAPI schema dictionary
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=app.openapi_tags,
        contact=app.contact,
        license_info=app.license_info,
    )
    
    # Add external docs
    openapi_schema["externalDocs"] = {
        "description": "BhashaAI Documentation",
        "url": "https://docs.bhashaai.com",
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
