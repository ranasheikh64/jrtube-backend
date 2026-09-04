import redis
from app.core.config import settings

# Global redis client instance
_redis_client = None

def get_redis():
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True
        )
    return _redis_client

def get_cache(key: str):
    client = get_redis()
    return client.get(key)

def set_cache(key: str, value: str, ttl: int = settings.CACHE_TTL_SECONDS):
    client = get_redis()
    client.setex(key, ttl, value)
