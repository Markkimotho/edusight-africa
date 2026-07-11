"""
Tests for app.core.cache — Redis caching helpers.

These tests mock the Redis client so no running Redis instance is required.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

from app.core import cache


@pytest.fixture(autouse=True)
def reset_redis_client():
    """Ensure each test starts with a clean module-level client."""
    cache._redis_client = None
    yield
    cache._redis_client = None


# ---------------------------------------------------------------------------
# get_redis
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_redis_creates_client_lazily():
    """get_redis should initialise the client on first call."""
    with patch("app.core.cache.aioredis.from_url") as mock_from_url:
        mock_client = AsyncMock()
        mock_from_url.return_value = mock_client

        client = await cache.get_redis()

        assert client is mock_client
        mock_from_url.assert_called_once()


@pytest.mark.asyncio
async def test_get_redis_reuses_existing_client():
    """Subsequent calls should return the same client instance."""
    mock_client = AsyncMock()
    cache._redis_client = mock_client

    client = await cache.get_redis()
    assert client is mock_client


# ---------------------------------------------------------------------------
# cache_get
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cache_get_returns_parsed_json():
    """cache_get should parse stored JSON and return it."""
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=json.dumps({"key": "value"}))
    cache._redis_client = mock_client

    result = await cache.cache_get("test-key")
    assert result == {"key": "value"}
    mock_client.get.assert_called_once_with("test-key")


@pytest.mark.asyncio
async def test_cache_get_returns_none_on_miss():
    """cache_get should return None when the key doesn't exist."""
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=None)
    cache._redis_client = mock_client

    result = await cache.cache_get("missing-key")
    assert result is None


@pytest.mark.asyncio
async def test_cache_get_returns_none_on_error():
    """cache_get should return None and log warning on Redis errors."""
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=ConnectionError("connection lost"))
    cache._redis_client = mock_client

    result = await cache.cache_get("error-key")
    assert result is None


# ---------------------------------------------------------------------------
# cache_set
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cache_set_stores_json_with_ttl():
    """cache_set should serialise value as JSON with the configured TTL."""
    mock_client = AsyncMock()
    mock_client.setex = AsyncMock()
    cache._redis_client = mock_client

    await cache.cache_set("my-key", {"hello": "world"}, ttl=120)

    mock_client.setex.assert_called_once_with(
        "my-key", 120, json.dumps({"hello": "world"}, default=str)
    )


@pytest.mark.asyncio
async def test_cache_set_handles_error_gracefully():
    """cache_set should not raise on Redis errors."""
    mock_client = AsyncMock()
    mock_client.setex = AsyncMock(side_effect=ConnectionError("refused"))
    cache._redis_client = mock_client

    # Should not raise
    await cache.cache_set("key", "value")


# ---------------------------------------------------------------------------
# cache_delete
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cache_delete_removes_key():
    """cache_delete should call Redis delete."""
    mock_client = AsyncMock()
    mock_client.delete = AsyncMock()
    cache._redis_client = mock_client

    await cache.cache_delete("del-key")
    mock_client.delete.assert_called_once_with("del-key")


@pytest.mark.asyncio
async def test_cache_delete_handles_error_gracefully():
    """cache_delete should not raise on Redis errors."""
    mock_client = AsyncMock()
    mock_client.delete = AsyncMock(side_effect=ConnectionError("refused"))
    cache._redis_client = mock_client

    await cache.cache_delete("key")


# ---------------------------------------------------------------------------
# cache_delete_pattern
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cache_delete_pattern_deletes_matching_keys():
    """cache_delete_pattern should find and delete all matching keys."""
    mock_client = AsyncMock()
    mock_client.keys = AsyncMock(return_value=["prefix:a", "prefix:b"])
    mock_client.delete = AsyncMock()
    cache._redis_client = mock_client

    await cache.cache_delete_pattern("prefix:*")

    mock_client.keys.assert_called_once_with("prefix:*")
    mock_client.delete.assert_called_once_with("prefix:a", "prefix:b")


@pytest.mark.asyncio
async def test_cache_delete_pattern_noop_when_no_keys():
    """cache_delete_pattern should not call delete when no keys match."""
    mock_client = AsyncMock()
    mock_client.keys = AsyncMock(return_value=[])
    mock_client.delete = AsyncMock()
    cache._redis_client = mock_client

    await cache.cache_delete_pattern("nothing:*")

    mock_client.keys.assert_called_once_with("nothing:*")
    mock_client.delete.assert_not_called()


@pytest.mark.asyncio
async def test_cache_delete_pattern_handles_error():
    """cache_delete_pattern should not raise on Redis errors."""
    mock_client = AsyncMock()
    mock_client.keys = AsyncMock(side_effect=ConnectionError("timeout"))
    cache._redis_client = mock_client

    await cache.cache_delete_pattern("err:*")


# ---------------------------------------------------------------------------
# close_redis
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_close_redis_closes_client():
    """close_redis should call aclose on the client and reset the global."""
    mock_client = AsyncMock()
    mock_client.aclose = AsyncMock()
    cache._redis_client = mock_client

    await cache.close_redis()

    mock_client.aclose.assert_called_once()
    assert cache._redis_client is None


@pytest.mark.asyncio
async def test_close_redis_noop_when_no_client():
    """close_redis should do nothing if no client was created."""
    cache._redis_client = None
    await cache.close_redis()
    assert cache._redis_client is None
