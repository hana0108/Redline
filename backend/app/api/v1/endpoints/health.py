from typing import Annotated

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.health import HealthStatus, DetailedHealthStatus
from app.services.health_service import health_service

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthStatus)
async def health_check(
    detailed: Annotated[bool, Query(description="Include detailed system information")] = False
) -> HealthStatus:
    """Basic health check endpoint"""
    return await health_service.perform_health_check(detailed=detailed)


@router.get("/detailed", response_model=DetailedHealthStatus)
async def detailed_health_check() -> DetailedHealthStatus:
    """Detailed health check with system metrics and database pool stats"""
    return await health_service.perform_health_check(detailed=True)


@router.get("/ready")
async def readiness_check(db: Annotated[Session, Depends(get_db)]):
    """Kubernetes-style readiness probe - checks if app can serve traffic"""
    try:
        # Quick database connectivity check
        result = db.execute(text("SELECT 1"))
        result.fetchone()
        return {"status": "ready", "message": "Application is ready to serve traffic"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Application not ready: {str(e)}")


@router.get("/live")
async def liveness_check():
    """Kubernetes-style liveness probe - checks if app is running"""
    return {"status": "alive", "message": "Application is running"}