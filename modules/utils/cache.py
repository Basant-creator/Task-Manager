import time
import threading

class CacheManager:
    """
    A thread-safe, time-aware caching manager.
    """
    def __init__(self):
        self._cache = {}
        self._lock = threading.Lock()

    def get(self, key):
        with self._lock:
            if key in self._cache:
                data, timestamp, ttl = self._cache[key]
                if ttl is None or (time.time() - timestamp) < ttl:
                    return data
            return None

    def set(self, key, value, ttl=None):
        with self._lock:
            self._cache[key] = (value, time.time(), ttl)

    def invalidate(self, key):
        with self._lock:
            if key in self._cache:
                del self._cache[key]

    def clear(self):
        with self._lock:
            self._cache.clear()

# Singleton instance
global_cache = CacheManager()
