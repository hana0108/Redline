import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import os

from sqlalchemy import text, select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings

logger = logging.getLogger(__name__)
from app.db.session import SessionLocal
from app.models.audit import AuditLog
from app.schemas.health import HealthCheckResult, HealthStatus, DetailedHealthStatus


class HealthService:
    """Service for performing health checks on system components"""

    def __init__(self):
        self.start_time = time.time()

    async def perform_health_check(self, detailed: bool = False) -> HealthStatus:
        """Perform comprehensive health check"""
        logger.debug(f"Starting health check (detailed={detailed})")
        checks = {}

        # Database connectivity check
        checks["database"] = await self._check_database()

        # Schema accessibility check
        checks["schema"] = await self._check_schema()

        # Determine overall status
        overall_status = self._calculate_overall_status(checks)

        # Calculate uptime
        uptime_seconds = time.time() - self.start_time

        logger.info(f"Health check completed: status={overall_status}")

        if detailed:
            health_status = DetailedHealthStatus(
                status=overall_status,
                uptime_seconds=uptime_seconds,
                version=self._get_version(),
                checks=checks
            )
            # Add system metrics if available
            try:
                health_status.metrics = self._get_system_metrics()
                health_status.database_pool = self._get_database_pool_stats()
            except ImportError:
                # psutil not available, skip system metrics
                pass
            return health_status
        else:
            return HealthStatus(
                status=overall_status,
                uptime_seconds=uptime_seconds,
                version=self._get_version(),
                checks=checks
            )

    async def _check_database(self) -> HealthCheckResult:
        """Check database connectivity"""
        start_time = time.time()
        try:
            # Use a separate session for health checks
            db = SessionLocal()
            try:
                # Simple connectivity test
                result = db.execute(text("SELECT 1"))
                result.fetchone()
                response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
                if response_time > 100:
                    logger.warning(f"Database check slow: {response_time:.2f}ms")
                return HealthCheckResult(
                    status="ok",
                    response_time_ms=round(response_time, 2),
                    message="Database connection successful"
                )
            finally:
                db.close()
        except SQLAlchemyError as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"Database connectivity check failed: {str(e)}", exc_info=True)
            return HealthCheckResult(
                status="error",
                response_time_ms=round(response_time, 2),
                message=f"Database connection failed: {str(e)}"
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"Unexpected error in database check: {str(e)}", exc_info=True)
            return HealthCheckResult(
                status="error",
                response_time_ms=round(response_time, 2),
                message=f"Unexpected error: {str(e)}"
            )

    async def _check_schema(self) -> HealthCheckResult:
        """Check schema accessibility and basic functionality"""
        start_time = time.time()
        try:
            db = SessionLocal()
            try:
                # Check if we can access the audit_logs table (basic schema test)
                result = db.execute(
                    select(AuditLog.id).limit(1)
                )
                result.first()
                response_time = (time.time() - start_time) * 1000
                if response_time > 100:
                    logger.warning(f"Schema check slow: {response_time:.2f}ms")
                return HealthCheckResult(
                    status="ok",
                    response_time_ms=round(response_time, 2),
                    message="Schema access successful"
                )
            finally:
                db.close()
        except SQLAlchemyError as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"Schema accessibility check failed: {str(e)}", exc_info=True)
            return HealthCheckResult(
                status="error",
                response_time_ms=round(response_time, 2),
                message=f"Schema access failed: {str(e)}"
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"Unexpected error in schema check: {str(e)}", exc_info=True)
            return HealthCheckResult(
                status="error",
                response_time_ms=round(response_time, 2),
                message=f"Unexpected error: {str(e)}"
            )

    def _calculate_overall_status(self, checks: Dict[str, HealthCheckResult]) -> str:
        """Calculate overall health status from individual checks"""
        if not checks:
            return "unhealthy"

        has_errors = any(check.status == "error" for check in checks.values())
        has_warnings = any(check.status == "warning" for check in checks.values())

        if has_errors:
            return "unhealthy"
        elif has_warnings:
            return "degraded"
        else:
            return "healthy"

    def _get_version(self) -> Optional[str]:
        """Get application version from environment or git"""
        # Try to get version from environment variable
        version = os.getenv("APP_VERSION")
        if version:
            return version

        # Try to get from git (if available)
        try:
            import subprocess
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            )
            if result.returncode == 0:
                return f"git-{result.stdout.strip()}"
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

        return None

    def _get_system_metrics(self) -> Optional[Dict[str, Any]]:
        """Get basic system metrics if psutil is available"""
        try:
            import psutil
            disk = psutil.disk_usage('/')
            return {
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_free_gb": round(disk.free / (1024**3), 2),
                "disk_total_gb": round(disk.total / (1024**3), 2)
            }
        except ImportError:
            return None

    def _get_database_pool_stats(self) -> Optional[Dict[str, Any]]:
        """Get database connection pool statistics"""
        try:
            # This is a simplified version - in production you'd want more detailed stats
            # SQLAlchemy 2.0 has better pool introspection
            return {
                "pool_size": getattr(SessionLocal, '_pool', {}).get('size', 'unknown'),
                "checked_out": getattr(SessionLocal, '_pool', {}).get('checked_out', 'unknown')
            }
        except Exception:
            return None


# Global health service instance
health_service = HealthService()