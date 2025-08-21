"""Asynchronous in-memory cache with TTL support.

This module replaces the previous SQLite-backed implementation with an
``asyncio`` friendly in-memory cache.  It provides non-blocking operations
and a background task that periodically removes expired entries.
"""

from __future__ import annotations

import asyncio
import contextlib
from typing import Dict, Tuple


class AsyncTTLCache:
    """Simple in-memory TTL cache.

    The cache stores two kinds of data:

    * ``recent_links`` – remembers recently sent links for each chat to avoid
      duplicates for a period of time.
    * ``reaction_counts`` – counts likes/dislikes for a message and expires
      after a configurable TTL.

    Expired records are cleaned up periodically in the background so cache
    operations do not spend time on housekeeping.
    """

    def __init__(self, cleanup_interval: float = 60.0) -> None:
        self._recent_links: Dict[Tuple[int, str], float] = {}
        self._reactions: Dict[Tuple[int, int], Dict[str, float]] = {}
        self._lock = asyncio.Lock()
        self._cleanup_interval = cleanup_interval
        self._cleanup_task: asyncio.Task | None = None

    # ------------------------------------------------------------------
    # Helpers
    def _ensure_cleanup(self) -> None:
        """Start background cleanup task once an event loop is running."""

        if self._cleanup_task is None:
            loop = asyncio.get_running_loop()
            self._cleanup_task = loop.create_task(self._cleanup_loop())

    async def _cleanup_loop(self) -> None:
        try:
            while True:
                await asyncio.sleep(self._cleanup_interval)
                await self._cleanup_expired()
        except asyncio.CancelledError:  # pragma: no cover - cooperative cancellation
            pass

    async def _cleanup_expired(self) -> None:
        loop = asyncio.get_running_loop()
        now = loop.time()
        async with self._lock:
            self._recent_links = {
                key: exp for key, exp in self._recent_links.items() if exp > now
            }
            self._reactions = {
                key: val
                for key, val in self._reactions.items()
                if val["expires_at"] > now
            }

    async def close(self) -> None:
        """Cancel the background cleanup task."""

        if self._cleanup_task:
            self._cleanup_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._cleanup_task

    # ------------------------------------------------------------------
    # Recent links operations
    async def set_recent_link(self, chat_id: int, url: str, ttl_seconds: int) -> None:
        self._ensure_cleanup()
        loop = asyncio.get_running_loop()
        expires_at = loop.time() + ttl_seconds
        async with self._lock:
            self._recent_links[(chat_id, url)] = expires_at

    async def is_recent_link(self, chat_id: int, url: str) -> bool:
        self._ensure_cleanup()
        loop = asyncio.get_running_loop()
        now = loop.time()
        async with self._lock:
            expires_at = self._recent_links.get((chat_id, url))
            if not expires_at:
                return False
            if expires_at < now:
                del self._recent_links[(chat_id, url)]
                return False
            return True

    # ------------------------------------------------------------------
    # Reaction counts operations
    async def init_reaction(self, chat_id: int, message_id: int, ttl_seconds: int) -> None:
        self._ensure_cleanup()
        loop = asyncio.get_running_loop()
        expires_at = loop.time() + ttl_seconds
        async with self._lock:
            self._reactions[(chat_id, message_id)] = {
                "likes": 0,
                "dislikes": 0,
                "expires_at": expires_at,
            }

    async def increment_reaction(
        self, chat_id: int, message_id: int, reaction: str, ttl_seconds: int
    ) -> Tuple[int, int]:
        self._ensure_cleanup()
        loop = asyncio.get_running_loop()
        now = loop.time()
        expires_at = now + ttl_seconds
        async with self._lock:
            data = self._reactions.get((chat_id, message_id))
            if not data or data["expires_at"] < now:
                likes = dislikes = 0
            else:
                likes, dislikes = data["likes"], data["dislikes"]
            if reaction == "like":
                likes += 1
            else:
                dislikes += 1
            self._reactions[(chat_id, message_id)] = {
                "likes": likes,
                "dislikes": dislikes,
                "expires_at": expires_at,
            }
            return likes, dislikes

    async def get_reaction(self, chat_id: int, message_id: int):
        self._ensure_cleanup()
        loop = asyncio.get_running_loop()
        now = loop.time()
        async with self._lock:
            data = self._reactions.get((chat_id, message_id))
            if not data:
                return None
            if data["expires_at"] < now:
                del self._reactions[(chat_id, message_id)]
                return None
            return {"likes": data["likes"], "dislikes": data["dislikes"]}

    async def remove_reaction(self, chat_id: int, message_id: int) -> None:
        self._ensure_cleanup()
        async with self._lock:
            self._reactions.pop((chat_id, message_id), None)


# Default cache instance used throughout the project
cache = AsyncTTLCache()

