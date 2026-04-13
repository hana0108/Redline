import json
import logging
from typing import Any, Optional

import redis.asyncio as redis
from redis.asyncio import Redis

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisCache:
    """Async Redis cache implementation for FastAPI"""

    def __init__(self):
        self._redis: Optional[Redis] = None
        self._enabled = settings.CACHE_ENABLED

    async def connect(self) -> None:
        """Initialize Redis connection"""
        if not self._enabled:
            logger.info("Redis caching is disabled")
            return

        try:
            self._redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
            await self._redis.ping()
            logger.info("Connected to Redis cache")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._redis = None

    async def disconnect(self) -> None:
        """Close Redis connection"""
        if self._redis:
            await self._redis.close()
            logger.info("Disconnected from Redis cache")

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self._is_available():
            return None

        try:
            value = await self._redis.get(key)
            if value:
                # Parse JSON for complex objects
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return value
            return None
        except Exception as e:
            logger.warning(f"Cache get error for key '{key}': {e}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL"""
        if not self._is_available():
            return False

        try:
            # Serialize complex objects to JSON
            if isinstance(value, (dict, list, tuple)):
                serialized_value = json.dumps(value)
            else:
                serialized_value = str(value)

            if ttl:
                await self._redis.setex(key, ttl, serialized_value)
            else:
                await self._redis.set(key, serialized_value)

            return True
        except Exception as e:
            logger.warning(f"Cache set error for key '{key}': {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self._is_available():
            return False

        try:
            await self._redis.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Cache delete error for key '{key}': {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        if not self._is_available():
            return 0

        try:
            # Get all keys matching pattern
            keys = await self._redis.keys(pattern)
            if keys:
                await self._redis.delete(*keys)
                logger.debug(f"Deleted {len(keys)} cache keys matching '{pattern}'")
                return len(keys)
            return 0
        except Exception as e:
            logger.warning(f"Cache delete pattern error for '{pattern}': {e}")
            return 0

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self._is_available():
            return False

        try:
            return bool(await self._redis.exists(key))
        except Exception as e:
            logger.warning(f"Cache exists error for key '{key}': {e}")
            return False

    async def clear_all(self) -> bool:
        """Clear all cache data"""
        if not self._is_available():
            return False

        try:
            await self._redis.flushdb()
            logger.info("Cleared all cache data")
            return True
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False

    async def get_stats(self) -> dict:
        """Get cache statistics"""
        if not self._is_available():
            return {"status": "disabled"}

        try:
            info = await self._redis.info()
            db_size = await self._redis.dbsize()

            return {
                "status": "connected",
                "url": settings.REDIS_URL.split("@")[-1] if "@" in settings.REDIS_URL else "localhost",
                "keys_count": db_size,
                "memory_used": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "uptime_seconds": info.get("uptime_in_seconds", 0),
            }
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {"status": "error", "error": str(e)}

    def _is_available(self) -> bool:
        """Check if Redis is available and enabled"""
        return self._enabled and self._redis is not None


# Global cache instance
cache = RedisCache()


async def get_cache() -> RedisCache:
    """Dependency injection for cache"""
    return cache