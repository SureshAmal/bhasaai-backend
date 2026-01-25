"""
BhashaAI Backend - Health Check Endpoints

Provides health check endpoints for monitoring and service discovery.
"""

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.response import APIResponse, HealthResponse
from app.config import settings
from app.db.session import get_db

router = APIRouter()


@router.get(
    "",
    response_model=APIResponse[HealthResponse],
    summary="Health Check",
    description="Check the health status of the API and its dependencies.",
    responses={
        200: {
            "description": "Service is healthy",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {
                            "status": "healthy",
                            "version": "0.1.0",
                            "environment": "development",
                            "services": {
                                "database": "connected",
                                "redis": "connected",
                                "minio": "connected"
                            }
                        },
                        "message": "Service is healthy",
                        "message_gu": "સેવા સ્વસ્થ છે"
                    }
                }
            }
        },
        503: {
            "description": "Service is unhealthy or degraded"
        }
    }
)
async def health_check() -> APIResponse[HealthResponse]:
    """
    Perform a health check of the API.
    
    Returns the current status of the service and its dependencies.
    This endpoint is used by load balancers and orchestration tools
    to determine if the service is ready to receive traffic.
    
    Returns:
        APIResponse[HealthResponse]: Health status with service details
    """
    # Basic health response without DB check for now
    health_data = HealthResponse(
        status="healthy",
        version=settings.app_version,
        environment=settings.app_env,
        services={
            "api": "operational",
        }
    )
    
    return APIResponse(
        success=True,
        data=health_data,
        message="Service is healthy",
        message_gu="સેવા સ્વસ્થ છે"
    )


@router.get(
    "/ready",
    response_model=APIResponse[dict[str, Any]],
    summary="Readiness Check",
    description="Check if the service is ready to handle requests (includes DB check).",
)
async def readiness_check(
    db: AsyncSession = Depends(get_db)
) -> APIResponse[dict[str, Any]]:
    """
    Check if the service is ready to handle requests.
    
    This endpoint verifies that all dependencies (database, cache, etc.)
    are accessible and the service is ready to process requests.
    
    Args:
        db: Database session (injected via dependency)
    
    Returns:
        APIResponse: Readiness status with dependency checks
    """
    checks: dict[str, Any] = {
        "database": "unknown",
        "redis": "unknown",
        "minio": "unknown",
    }
    
    # Check database connection
    try:
        await db.execute("SELECT 1")
        checks["database"] = "connected"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"
    
    # Redis and MinIO checks will be added when those services are integrated
    checks["redis"] = "not_configured"
    checks["minio"] = "not_configured"
    
    all_healthy = all(
        status in ("connected", "not_configured") 
        for status in checks.values()
    )
    
    return APIResponse(
        success=all_healthy,
        data={
            "ready": all_healthy,
            "checks": checks,
        },
        message="Readiness check completed" if all_healthy else "Service not ready",
        message_gu="તૈયારી તપાસ પૂર્ણ" if all_healthy else "સેવા તૈયાર નથી"
    )


@router.get(
    "/live",
    response_model=dict[str, str],
    summary="Liveness Check",
    description="Simple liveness probe for container orchestration.",
)
async def liveness_check() -> dict[str, str]:
    """
    Simple liveness check for Kubernetes/Docker health probes.
    
    Returns a minimal response indicating the service process is alive.
    This should be as lightweight as possible and not depend on
    external services.
    
    Returns:
        dict: Simple status response
    """
    return {"status": "alive"}
