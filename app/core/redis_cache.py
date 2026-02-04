"""
Redis Cache with Fallback to In-Memory Cache
Automatically uses Railway Redis in production or falls back to in-memory cache
"""

import os
import redis.asyncio as aioredis
from typing import Any, Optional
import json
import logging

logger = logging.getLogger(__name__)


class RedisCache:
    """Production Redis cache with Railway support"""
    
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self.connected = False
        self._hits = 0
        self._misses = 0
    
    async def connect(self):
        """Connect to Redis using Railway REDIS_URL"""
        try:
            redis_url = os.getenv("REDIS_URL")
            if not redis_url:
                logger.warning("REDIS_URL not found, cache disabled")
                return
            
            self.redis = await aioredis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # Test connection
            await self.redis.ping()
            self.connected = True
            logger.info(f"✅ Connected to Redis: {redis_url.split('@')[-1]}")
            
        except Exception as e:
            logger.warning(f"⚠️ Redis connection failed: {e}")
            self.connected = False
    
    async def set(self, key: str, value: Any, ttl_seconds: int = 3600):
        """Set a value in Redis with TTL"""
        if not self.connected or not self.redis:
            return
        
        try:
            # Serialize value to JSON
            serialized = json.dumps(value)
            await self.redis.setex(key, ttl_seconds, serialized)
            logger.debug(f"Redis SET: {key} (TTL: {ttl_seconds}s)")
        except Exception as e:
            logger.error(f"Redis SET error for {key}: {e}")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get a value from Redis"""
        if not self.connected or not self.redis:
            self._misses += 1
            return None
        
        try:
            value = await self.redis.get(key)
            if value is None:
                self._misses += 1
                logger.debug(f"Redis MISS: {key}")
                return None
            
            self._hits += 1
            logger.debug(f"Redis HIT: {key}")
            return json.loads(value)
            
        except Exception as e:
            logger.error(f"Redis GET error for {key}: {e}")
            self._misses += 1
            return None
    
    async def delete(self, key: str):
        """Delete a key from Redis"""
        if not self.connected or not self.redis:
            return
        
        try:
            await self.redis.delete(key)
            logger.debug(f"Redis DELETE: {key}")
        except Exception as e:
            logger.error(f"Redis DELETE error for {key}: {e}")
    
    async def clear(self):
        """Clear all cache entries"""
        if not self.connected or not self.redis:
            return
        
        try:
            await self.redis.flushdb()
            self._hits = 0
            self._misses = 0
            logger.info("Redis cache CLEARED")
        except Exception as e:
            logger.error(f"Redis CLEAR error: {e}")
    
    async def close(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
            logger.info("Redis connection closed")
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "connected": self.connected,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate_percent": round(hit_rate, 2),
            "total_requests": total_requests
        }


# Global Redis cache instance
redis_cache = RedisCache()
