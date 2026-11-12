from __future__ import annotations

import time
import logging
from typing import Any

logger = logging.getLogger("dragon.cache")


class CacheManager:
    """In-memory cache with TTL support. Thread-safe ready interface."""
    def __init__(self):
        self._store: dict[str, tuple[Any, float]] = {}

    async def get(self, key: str) -> Any | None:
        """Retrieves value from cache if it exists and is not expired."""
        if key not in self._store:
            return None
            
        value, expiry = self._store[key]
        if time.time() > expiry:
            # Lazy delete expired cache
            del self._store[key]
            logger.debug("Cache expired for key: %s", key)
            return None
            
        return value

    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """Saves value into cache with a TTL (Time To Live) in seconds."""
        expiry = time.time() + ttl
        self._store[key] = (value, expiry)
        logger.debug("Cache set for key: %s (TTL: %ds)", key, ttl)

    async def delete(self, key: str) -> None:
        """Deletes a key from cache."""
        if key in self._store:
            del self._store[key]
            logger.debug("Cache deleted for key: %s", key)

    async def clear_pattern(self, pattern: str) -> None:
        """Clears all keys starting with the specified prefix pattern."""
        keys_to_del = [k for k in self._store.keys() if k.startswith(pattern)]
        for k in keys_to_del:
            del self._store[k]
        logger.debug("Cleared %d cache keys matching pattern: %s", len(keys_to_del), pattern)


# Singleton cache manager instance
cache = CacheManager()
