"""
Thread-Safe In-Memory Cache with Time-To-Live (TTL)
SIH26151: Dark Web Threat Actor De-anonymization

Caches normalized blockchain lookups to reduce redundant network requests,
comply with rate limits, and provide rapid responses.
"""

import time
import threading
from typing import Dict, Any, Optional, Tuple


class BlockchainCache:
    """Thread-safe in-memory cache with expiration timestamping."""

    def __init__(self, default_ttl_seconds: int = 300):
        self.default_ttl = default_ttl_seconds
        self._cache: Dict[str, Tuple[float, Any]] = {}
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Any]:
        """Retrieves item from cache if not expired."""
        with self._lock:
            if key in self._cache:
                expiry, val = self._cache[key]
                if time.time() < expiry:
                    self._hits += 1
                    return val
                else:
                    del self._cache[key]
            self._misses += 1
            return None

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """Stores item with TTL."""
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        expiry = time.time() + ttl
        with self._lock:
            self._cache[key] = (expiry, value)

    def delete(self, key: str) -> bool:
        """Deletes key from cache."""
        with self._lock:
            return self._cache.pop(key, None) is not None

    def clear(self) -> None:
        """Clears all cached entries."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0

    def get_stats(self) -> Dict[str, Any]:
        """Returns cache telemetry."""
        with self._lock:
            # Clean expired items
            now = time.time()
            active_keys = [k for k, (exp, _) in self._cache.items() if exp >= now]
            total_reqs = self._hits + self._misses
            hit_rate = (self._hits / total_reqs) if total_reqs > 0 else 0.0

            return {
                "active_entries": len(active_keys),
                "total_stored": len(self._cache),
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": round(hit_rate, 4),
                "default_ttl_seconds": self.default_ttl
            }


# Singleton cache instance
GLOBAL_BLOCKCHAIN_CACHE = BlockchainCache(default_ttl_seconds=300)
