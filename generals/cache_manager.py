class CacheService:
    def __init__(self):
        self.cache = {}


    def get_value(self, key):
        return self.cache.get(key)
    

    def set_value(self, key, value) -> None:
        if key not in self.cache:
            self.cache[key] = value


    def clear(self):
        self.cache = {}


class CacheManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._caches = {}
        return cls._instance
    

    def get_cache(self, scope: str) -> 'CacheService':
        """Get or create a named cache scope"""
        if scope not in self._caches:
            self._caches[scope] = CacheService()

        return self._caches[scope]
    

    def invalidate(self, scope: str = None):
        """Invalidate specific cache or all caches"""
        if scope:
            if scope in self._caches:
                self._caches[scope].clear()

        else:
            for cache in self._caches.values():
                cache.clear()
