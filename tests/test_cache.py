import asyncio

import pytest

from bot.storage.cache import AsyncTTLCache


@pytest.mark.asyncio
async def test_recent_link_expiration():
    cache = AsyncTTLCache(cleanup_interval=0.05)
    await cache.set_recent_link(123, "http://example.com", ttl_seconds=0.05)
    assert await cache.is_recent_link(123, "http://example.com") is True
    await asyncio.sleep(0.1)
    assert await cache.is_recent_link(123, "http://example.com") is False
    await cache.close()


@pytest.mark.asyncio
async def test_reaction_counts():
    cache = AsyncTTLCache(cleanup_interval=0.05)
    await cache.init_reaction(1, 42, ttl_seconds=1)
    assert await cache.get_reaction(1, 42) == {"likes": 0, "dislikes": 0}

    likes, dislikes = await cache.increment_reaction(1, 42, "like", ttl_seconds=1)
    assert (likes, dislikes) == (1, 0)
    likes, dislikes = await cache.increment_reaction(1, 42, "dislike", ttl_seconds=1)
    assert (likes, dislikes) == (1, 1)
    assert await cache.get_reaction(1, 42) == {"likes": 1, "dislikes": 1}

    await cache.remove_reaction(1, 42)
    assert await cache.get_reaction(1, 42) is None

    await cache.init_reaction(1, 43, ttl_seconds=0.05)
    await asyncio.sleep(0.1)
    assert await cache.get_reaction(1, 43) is None
    await cache.close()

