from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class HealthCheckResult(BaseModel):
    """Result of a single health check"""
    status: str = Field(..., description="Status: 'ok', 'warning', 'error'")
    response_time_ms: Optional[float] = Field(None, description="Response time in milliseconds")
    message: Optional[str] = Field(None, description="Optional status message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional check details")


class HealthStatus(BaseModel):
    """Overall health status response"""
    status: str = Field(..., description="Overall status: 'healthy', 'degraded', 'unhealthy'")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")
    uptime_seconds: Optional[float] = Field(None, description="Application uptime in seconds")
    version: Optional[str] = Field(None, description="Application version")
    checks: Dict[str, HealthCheckResult] = Field(default_factory=dict, description="Individual check results")


class SystemMetrics(BaseModel):
    """System resource metrics"""
    cpu_percent: Optional[float] = Field(None, description="CPU usage percentage")
    memory_percent: Optional[float] = Field(None, description="Memory usage percentage")
    disk_free_gb: Optional[float] = Field(None, description="Free disk space in GB")
    disk_total_gb: Optional[float] = Field(None, description="Total disk space in GB")
    active_connections: Optional[int] = Field(None, description="Active database connections")


class DetailedHealthStatus(HealthStatus):
    """Extended health status with system metrics"""
    metrics: Optional[SystemMetrics] = Field(None, description="System resource metrics")
    database_pool: Optional[Dict[str, Any]] = Field(None, description="Database connection pool stats")