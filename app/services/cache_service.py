import redis
import json
from typing import Optional, Any
from app.core.config import get_settings
from loguru import logger

settings = get_settings()

class CacheService:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            decode_responses=True
        )
        self.default_ttl = 3600  # 1 hour default TTL

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except redis.RedisError as e:
            logger.error(f"Redis error while getting key {key}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for key {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value in cache with optional TTL"""
        try:
            serialized_value = json.dumps(value)
            return self.redis_client.set(
                key,
                serialized_value,
                ex=ttl or self.default_ttl
            )
        except (redis.RedisError, TypeError) as e:
            logger.error(f"Error setting cache for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        try:
            return bool(self.redis_client.delete(key))
        except redis.RedisError as e:
            logger.error(f"Error deleting key {key}: {e}")
            return False

    def generate_key(self, prefix: str, *args) -> str:
        """Generate a cache key from prefix and arguments"""
        return f"{prefix}:{':'.join(str(arg) for arg in args)}"
