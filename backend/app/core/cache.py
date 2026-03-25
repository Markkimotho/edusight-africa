import json
import logging
from typing import Any
from functools import wraps

import redis.asyncio as aioredis

from app.config import settings

logger = logging.getLogger(__name__)

_redis_client: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """Return a shared async Redis client, initialised lazily."""
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


async def cache_get(key: str) -> Any | None:
    """Retrieve a JSON-serialised value from Redis, or None on miss/error."""
    try:
        client = await get_redis()
        raw = await client.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception as exc:
        logger.warning("Redis GET error for key '%s': %s", key, exc)
        return None


async def cache_set(key: str, value: Any, ttl: int = settings.CACHE_TTL_SECONDS) -> None:
    """Serialise value as JSON and store in Redis with a TTL."""
    try:
        client = await get_redis()
        await client.setex(key, ttl, json.dumps(value, default=str))
    except Exception as exc:
        logger.warning("Redis SET error for key '%s': %s", key, exc)


async def cache_delete(key: str) -> None:
    """Delete a key from Redis."""
    try:
        client = await get_redis()
        await client.delete(key)
    except Exception as exc:
        logger.warning("Redis DELETE error for key '%s': %s", key, exc)


async def cache_delete_pattern(pattern: str) -> None:
    """Delete all keys matching a glob pattern."""
    try:
        client = await get_redis()
        keys = await client.keys(pattern)
        if keys:
            await client.delete(*keys)
    except Exception as exc:
        logger.warning("Redis pattern DELETE error for '%s': %s", pattern, exc)


async def close_redis() -> None:
    """Gracefully close the Redis connection."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None
