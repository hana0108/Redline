from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_permissions
from app.cache.redis_cache import cache
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.services.cache_service import cache_service

router = APIRouter(prefix="/cache", tags=["cache"])


@router.get("/stats")
async def get_cache_stats(
    _: Annotated[User, Depends(require_permissions("settings.read"))],
):
    """Get cache statistics and health information"""
    stats = await cache.get_stats()
    return stats


@router.post("/clear")
async def clear_cache(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("settings.write"))],
):
    """Clear all cache data"""
    success = await cache.clear_all()
    if success:
        return {"message": "Cache cleared successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to clear cache")


@router.post("/warmup")
async def warmup_cache(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("settings.write"))],
):
    """Warm up cache with commonly accessed data"""
    if not settings.CACHE_ENABLED:
        return {"message": "Cache is disabled"}

    try:
        await cache_service.get_settings(force_refresh=True)
        return {"message": "Cache warmup completed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache warmup failed: {str(e)}") from e


async def list_cache_keys(
    _: Annotated[User, Depends(require_permissions("settings.read"))],
    pattern: str = "*",
):
    """List cache keys matching pattern"""
    try:
        if not cache._redis:
            return {"keys": [], "message": "Cache not available"}

        keys = await cache._redis.keys(pattern)
        return {"keys": keys, "count": len(keys)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list keys: {str(e)}") from e
