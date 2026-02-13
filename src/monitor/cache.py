"""Thread-safe TTL cache for system metrics.

Provides caching to reduce system call overhead for frequent polling.
"""

import threading
import time
from dataclasses import dataclass
from typing import Callable, Generic, Optional, TypeVar

T = TypeVar("T")


@dataclass
class CacheEntry(Generic[T]):
    """A cached value with timestamp."""

    data: T
    timestamp: float


class TTLCache(Generic[T]):
    """Thread-safe TTL cache for single values."""

    def __init__(self, ttl: float = 2.0):
        self._entry: Optional[CacheEntry[T]] = None
        self._lock = threading.Lock()
        self._ttl = ttl

    def get_or_compute(self, compute: Callable[[], T], ttl: Optional[float] = None) -> T:
        """Get cached value or compute new value if expired.

        Args:
            compute: Function to compute the value if cache is stale
            ttl: Optional override TTL for this computation

        Returns:
            The cached or newly computed value
        """
        with self._lock:
            now = time.time()
            effective_ttl = ttl if ttl is not None else self._ttl

            if self._entry and (now - self._entry.timestamp) < effective_ttl:
                return self._entry.data

            data = compute()
            self._entry = CacheEntry(data, now)
            return data

    def invalidate(self) -> None:
        """Clear the cache."""
        with self._lock:
            self._entry = None


class MultiKeyCache(Generic[T]):
    """Thread-safe TTL cache supporting multiple keys."""

    def __init__(self, default_ttl: float = 2.0):
        self._cache: dict[str, CacheEntry[T]] = {}
        self._lock = threading.Lock()
        self._default_ttl = default_ttl

    def get_or_compute(
        self, key: str, compute: Callable[[], T], ttl: Optional[float] = None
    ) -> T:
        """Get cached value by key or compute if not present/expired."""
        with self._lock:
            now = time.time()
            effective_ttl = ttl if ttl is not None else self._default_ttl

            entry = self._cache.get(key)
            if entry and (now - entry.timestamp) < effective_ttl:
                return entry.data

            data = compute()
            self._cache[key] = CacheEntry(data, now)
            return data

    def invalidate(self, key: Optional[str] = None) -> None:
        """Clear cache for specific key or all keys."""
        with self._lock:
            if key:
                self._cache.pop(key, None)
            else:
                self._cache.clear()


class RateCalculator:
    """Calculate rates from cumulative counters.

    Useful for network/disk I/O rate calculations.
    """

    def __init__(self):
        self._last_value: float = 0
        self._last_time: float = 0
        self._lock = threading.Lock()

    def calculate_rate(self, current_value: float) -> float:
        """Calculate rate (value/sec) from cumulative counter.

        Args:
            current_value: Current counter value

        Returns:
            Rate in units per second, or 0 if not enough data
        """
        with self._lock:
            now = time.time()

            if self._last_time == 0:
                self._last_value = current_value
                self._last_time = now
                return 0.0

            time_delta = now - self._last_time
            if time_delta <= 0:
                return 0.0

            value_delta = current_value - self._last_value
            rate = value_delta / time_delta

            self._last_value = current_value
            self._last_time = now

            return rate

    def reset(self) -> None:
        """Reset the calculator state."""
        with self._lock:
            self._last_value = 0
            self._last_time = 0
