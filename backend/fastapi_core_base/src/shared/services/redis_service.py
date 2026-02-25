import redis.asyncio as redis
from typing import Any
from src.shared.configuration.config import env_config_manager
from src.shared.services.logging_service import LoggingService

logger = LoggingService.get_logger(__name__)

class RedisService:
    """Service class for managing Redis cache operations."""

    def __init__(self):
        self._redis_client = None
        self.host = env_config_manager.get_dynamic_setting("REDIS_HOST", "localhost")
        self.port = int(env_config_manager.get_dynamic_setting("REDIS_PORT", 6379))
        self.password = env_config_manager.get_dynamic_setting("REDIS_PASSWORD", None)
        self.use_redis = str(env_config_manager.get_dynamic_setting("UNIVERSAL_USE_REDIS", "false")).lower() == "true"

    async def get_client(self):
        """Get or create an async Redis client instance."""
        if not self.use_redis:
            return None
            
        if self._redis_client is None:
            try:
                # Basic connection configuration
                self._redis_client = redis.Redis(
                    host=self.host,
                    port=self.port,
                    password=self.password,
                    decode_responses=True
                )
                # Check connection
                await self._redis_client.ping()
                logger.debug(f"Connected to Redis at {self.host}:{self.port}")
            except Exception as e:
                logger.error(f"Failed to connect to Redis at {self.host}:{self.port}: {e}")
                self._redis_client = None
                return None
        return self._redis_client

    async def get_cache(self, key: str, namespace: str = None) -> Any:
        """Get a value from cache."""
        if not self.use_redis:
            return None
            
        client = await self.get_client()
        if client:
            try:
                full_key = f"{namespace}:{key}" if namespace else key
                return await client.get(full_key)
            except Exception as e:
                logger.error(f"Error getting key '{key}' from Redis: {e}")
        return None

    async def set_cache(self, key: str, value: Any, expire_seconds: int = 3600, namespace: str = None) -> bool:
        """Set a value in cache with expiration."""
        if not self.use_redis:
            return False
            
        client = await self.get_client()
        if client:
            try:
                full_key = f"{namespace}:{key}" if namespace else key
                # Convert non-string values to string if necessary, 
                # but redis-py handles bools/ints/floats if needed
                await client.set(full_key, value, ex=expire_seconds)
                return True
            except Exception as e:
                logger.error(f"Error setting key '{key}' in Redis: {e}")
        return False

    async def close(self):
        """Close the Redis client connection."""
        if self._redis_client:
            await self._redis_client.close()
            self._redis_client = None
            logger.debug("Redis connection closed")

# Global singleton instance
redis_service = RedisService()
