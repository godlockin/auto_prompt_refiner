"""
Response Cache with TTL and LRU Eviction.

Features:
- TTL-based expiration
- LRU eviction when max size reached
- Thread-safe operations
- Cache statistics
"""
import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Generic, TypeVar, Optional
from threading import Lock
from collections import OrderedDict

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class CacheEntry(Generic[T]):
    """Cache entry with metadata."""
    key: str
    value: T
    created_at: float = field(default_factory=time.time)
    accessed_at: float = field(default_factory=time.time)
    access_count: int = 0


@dataclass
class CacheStats:
    """Cache statistics."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    expirations: int = 0
    total_items: int = 0
    max_size: int = 0


class CacheError(Exception):
    """Cache-related error."""
    pass


class LRUCache(Generic[T]):
    """
    Thread-safe LRU cache with TTL support.

    Features:
    - O(1) lookup, insert, and eviction
    - TTL-based automatic expiration
    - LRU eviction when capacity reached
    - Comprehensive statistics
    """

    def __init__(
        self,
        max_size: int = 1000,
        ttl_seconds: float = 3600.0,
        key_prefix: str = ""
    ):
        """
        Initialize cache.

        Args:
            max_size: Maximum number of items
            ttl_seconds: Time-to-live in seconds
            key_prefix: Prefix for cache keys
        """
        if max_size <= 0:
            raise ValueError("max_size must be positive")
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")

        self._max_size = max_size
        self._ttl = ttl_seconds
        self._key_prefix = key_prefix
        self._data: OrderedDict[str, CacheEntry[T]] = OrderedDict()
        self._lock = Lock()
        self._stats = CacheStats(max_size=max_size)

    def _make_key(self, key: str) -> str:
        """Create cache key with prefix."""
        return f"{self._key_prefix}:{key}"

    def _is_expired(self, entry: CacheEntry[T]) -> bool:
        """Check if entry has expired."""
        return time.time() - entry.created_at > self._ttl

    def get(self, key: str) -> Optional[T]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Value or None if not found/expired
        """
        with self._lock:
            full_key = self._make_key(key)

            if full_key not in self._data:
                self._stats.misses += 1
                return None

            entry = self._data[full_key]

            if self._is_expired(entry):
                del self._data[full_key]
                self._stats.expirations += 1
                self._stats.total_items = len(self._data)
                return None

            # Move to end (most recently used)
            self._data.move_to_end(full_key)
            entry.accessed_at = time.time()
            entry.access_count += 1

            self._stats.hits += 1
            return entry.value

    def set(self, key: str, value: T) -> None:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
        """
        with self._lock:
            full_key = self._make_key(key)

            # Update existing entry
            if full_key in self._data:
                entry = self._data[full_key]
                entry.value = value
                entry.created_at = time.time()
                entry.accessed_at = time.time()
                entry.access_count += 1
                self._data.move_to_end(full_key)
                return

            # Create new entry
            entry = CacheEntry(key=full_key, value=value)
            self._data[full_key] = entry

            # Evict oldest if at capacity
            if len(self._data) > self._max_size:
                self._evict_oldest()

            self._stats.total_items = len(self._data)

    def _evict_oldest(self) -> None:
        """Evict the least recently used item."""
        if self._data:
            oldest_key, _ = self._data.popitem(last=False)
            self._stats.evictions += 1
            logger.debug(f"Evicted cache entry: {oldest_key}")

    def delete(self, key: str) -> bool:
        """
        Delete a key from cache.

        Args:
            key: Cache key

        Returns:
            True if deleted, False if not found
        """
        with self._lock:
            full_key = self._make_key(key)
            if full_key in self._data:
                del self._data[full_key]
                self._stats.total_items = len(self._data)
                return True
            return False

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._data.clear()
            self._stats.total_items = 0

    def get_or_set(self, key: str, factory: callable) -> T:
        """
        Get value or compute and cache it.

        Args:
            key: Cache key
            factory: Function to compute value if not cached

        Returns:
            Cached or computed value
        """
        value = self.get(key)
        if value is not None:
            return value

        result = factory()
        self.set(key, result)
        return result

    def peek(self, key: str) -> Optional[T]:
        """
        Peek at value without updating access time.

        Args:
            key: Cache key

        Returns:
            Value or None if not found/expired
        """
        with self._lock:
            full_key = self._make_key(key)

            if full_key not in self._data:
                return None

            entry = self._data[full_key]

            if self._is_expired(entry):
                return None

            return entry.value

    def cleanup(self) -> int:
        """
        Remove all expired entries.

        Returns:
            Number of entries removed
        """
        with self._lock:
            expired_keys = [
                key for key, entry in self._data.items()
                if self._is_expired(entry)
            ]

            for key in expired_keys:
                del self._data[key]

            removed = len(expired_keys)
            self._stats.expirations += removed
            self._stats.total_items = len(self._data)

            if removed > 0:
                logger.info(f"Cleaned up {removed} expired cache entries")

            return removed

    @property
    def stats(self) -> CacheStats:
        """Get cache statistics."""
        with self._lock:
            return CacheStats(
                hits=self._stats.hits,
                misses=self._stats.misses,
                evictions=self._stats.evictions,
                expirations=self._stats.expirations,
                total_items=len(self._data),
                max_size=self._max_size,
            )

    @property
    def size(self) -> int:
        """Get current cache size."""
        with self._lock:
            return len(self._data)

    @property
    def max_size(self) -> int:
        """Get maximum cache size."""
        return self._max_size

    def __contains__(self, key: str) -> bool:
        """Check if key exists in cache."""
        return self.get(key) is not None

    def __len__(self) -> int:
        """Get cache size."""
        return self.size

    def __repr__(self) -> str:
        stats = self.stats
        hit_rate = (
            (stats.hits / (stats.hits + stats.misses) * 100)
            if (stats.hits + stats.misses) > 0 else 0
        )
        return (
            f"LRUCache(size={stats.total_items}/{stats.max_size}, "
            f"hits={stats.hits}, misses={stats.misses}, "
            f"hit_rate={hit_rate:.1f}%)"
        )


def cache_key_from_prompt(prompt: str) -> str:
    """
    Generate a cache key from a prompt.

    Args:
        prompt: User prompt

    Returns:
        MD5 hash of the prompt
    """
    normalized = prompt.strip().lower()
    return hashlib.md5(normalized.encode()).hexdigest()


# Global caches for different purposes
prompt_cache = LRUCache(
    max_size=1000,
    ttl_seconds=3600.0,
    key_prefix="prompt"
)

classification_cache = LRUCache(
    max_size=10000,
    ttl_seconds=86400.0,  # 24 hours
    key_prefix="classify"
)

agent_result_cache = LRUCache(
    max_size=500,
    ttl_seconds=1800.0,  # 30 minutes
    key_prefix="agent"
)
