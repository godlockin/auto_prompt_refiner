"""
Rate Limiting Module.

Provides in-memory rate limiting for API endpoints.
"""
import time
import threading
from dataclasses import dataclass
from typing import Dict, Optional, Tuple


@dataclass
class RateLimitConfig:
    """Rate limit configuration."""
    requests: int
    window_seconds: int


class RateLimiter:
    """Thread-safe in-memory rate limiter using sliding window algorithm."""

    def __init__(self):
        self._buckets: Dict[str, list] = {}
        self._lock = threading.Lock()

    def _cleanup_old_entries(self, key: str, window_seconds: int):
        """Remove entries outside the current window."""
        if key not in self._buckets:
            return
        cutoff = time.time() - window_seconds
        self._buckets[key] = [t for t in self._buckets[key] if t > cutoff]

    def is_allowed(
        self,
        identifier: str,
        max_requests: int,
        window_seconds: int
    ) -> Tuple[bool, int, int]:
        """
        Check if a request is allowed under rate limit.

        Returns:
            Tuple of (is_allowed, remaining_requests, reset_time_seconds)
        """
        with self._lock:
            self._cleanup_old_entries(identifier, window_seconds)

            now = time.time()
            if identifier not in self._buckets:
                self._buckets[identifier] = []

            current_count = len(self._buckets[identifier])

            if current_count >= max_requests:
                oldest = min(self._buckets[identifier]) if self._buckets[identifier] else now
                reset_time = int(oldest + window_seconds - now)
                return False, 0, max(0, reset_time)

            self._buckets[identifier].append(now)
            remaining = max_requests - current_count - 1
            oldest = min(self._buckets[identifier]) if self._buckets[identifier] else now
            reset_time = int(oldest + window_seconds - now)

            return True, remaining, max(0, reset_time)


class MultiTierRateLimiter:
    """Multi-tier rate limiter with different limits for different tiers."""

    DEFAULT_TIERS = {
        "default": RateLimitConfig(requests=10, window_seconds=60),
        "auth": RateLimitConfig(requests=5, window_seconds=300),
        "api": RateLimitConfig(requests=100, window_seconds=60),
        "refine": RateLimitConfig(requests=20, window_seconds=60),
    }

    def __init__(self, custom_tiers: Optional[Dict[str, RateLimitConfig]] = None):
        self.tiers = custom_tiers or self.DEFAULT_TIERS.copy()
        self._limiters: Dict[str, RateLimiter] = {}
        for tier_name in self.tiers:
            self._limiters[tier_name] = RateLimiter()

    def is_allowed(
        self,
        identifier: str,
        tier: str = "default"
    ) -> Tuple[bool, Dict[str, str]]:
        """Check if request is allowed for given tier."""
        if tier not in self.tiers:
            tier = "default"

        config = self.tiers[tier]
        limiter = self._limiters[tier]

        is_allowed, remaining, reset_time = limiter.is_allowed(
            identifier,
            config.requests,
            config.window_seconds
        )

        headers: Dict[str, str] = {
            "X-RateLimit-Limit": str(config.requests),
            "X-RateLimit-Remaining": str(max(0, remaining)),
            "X-RateLimit-Reset": str(reset_time)
        }

        return is_allowed, headers


# Global rate limiter instance
_rate_limiter: Optional[MultiTierRateLimiter] = None


def get_rate_limiter() -> MultiTierRateLimiter:
    """Get the global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = MultiTierRateLimiter()
    return _rate_limiter
