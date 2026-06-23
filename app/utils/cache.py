"""
Redis cache layer with in-memory fallback.

Used for caching:
- Problem statements and constraints
- Contest details and problem lists
- Submission history and statuses
"""

import json
from typing import Any, Optional
import redis
from app.config import config
from app.utils.logger import logger

# Global Redis client
_redis_client: Optional[redis.Redis] = None
# In-memory backup dictionary if Redis is not available
_memory_cache: dict[str, Any] = {}


def _get_redis() -> Optional[redis.Redis]:
    """Initialize or return the Redis client if available."""
    global _redis_client
    if _redis_client is not None:
        return _redis_client

    if not config.REDIS_URL:
        return None

    try:
        # Convert redis:// to options
        _redis_client = redis.Redis.from_url(config.REDIS_URL, socket_timeout=2.0)
        # Test connection
        _redis_client.ping()
        logger.info("Successfully connected to Redis cache")
        return _redis_client
    except Exception as e:
        logger.warning(f"Redis connection failed ({e}). Falling back to in-memory cache.")
        _redis_client = None
        return None


def get_cache(key: str) -> Optional[Any]:
    """Retrieve an item from the cache.

    Args:
        key: The unique cache key.

    Returns:
        The cached value (deserialized from JSON), or None if not found/expired.
    """
    client = _get_redis()
    if client:
        try:
            val = client.get(key)
            if val:
                return json.loads(val)
        except Exception as e:
            logger.warning(f"Failed to read from Redis cache: {e}")
    
    # Fallback to in-memory cache
    return _memory_cache.get(key)


def set_cache(key: str, value: Any, expire_seconds: int = 3600) -> bool:
    """Store an item in the cache.

    Args:
        key: The unique cache key.
        value: The value to store (must be JSON-serializable).
        expire_seconds: Time to live in seconds.

    Returns:
        True if successfully cached, False otherwise.
    """
    client = _get_redis()
    if client:
        try:
            client.setex(key, expire_seconds, json.dumps(value))
            return True
        except Exception as e:
            logger.warning(f"Failed to write to Redis cache: {e}")
    
    # Fallback to in-memory cache
    _memory_cache[key] = value
    # Simple in-memory expiry is not fully implemented for simplicity,
    # but we store the value to ensure correct fallback functionality.
    return True


def delete_cache(key: str) -> bool:
    """Delete an item from the cache."""
    client = _get_redis()
    if client:
        try:
            client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Failed to delete from Redis cache: {e}")
    
    if key in _memory_cache:
        del _memory_cache[key]
        return True
    return False


def clear_cache() -> None:
    """Clear all items from the cache."""
    global _memory_cache
    client = _get_redis()
    if client:
        try:
            client.flushdb()
            logger.info("Flushed Redis database")
        except Exception as e:
            logger.warning(f"Failed to flush Redis: {e}")
    
    _memory_cache.clear()
    logger.info("Cleared in-memory cache")
