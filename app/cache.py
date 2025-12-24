import hashlib
import logging
from typing import Optional

import redis.asyncio as redis

from app.config import settings

logger = logging.getLogger(__name__)


class Cache:
    """Redis cache manager."""

    def __init__(self):
        self.client: Optional[redis.Redis] = None
        self.ttl = settings.CACHE_TTL

    async def connect(self):
        try:
            self.client = redis.from_url(
                settings.REDIS_URL,
                encoding='utf-8',
                decode_responses=True
            )
            await self.client.ping()
            logger.info(f'Connected to Redis at {settings.REDIS_URL}')
        except Exception as e:
            logger.warning(f'Redis connection failed: {e}. Cache disabled.')
            self.client = None

    async def close(self):
        if self.client:
            await self.client.close()
            logger.info('Redis connection closed')

    def _make_key(self, query: str) -> str:
        """Generate cache key from query."""
        # Use MD5 hash of query as key
        return f'query:{hashlib.md5(query.encode()).hexdigest()}'

    async def get(self, query: str) -> Optional[int]:
        """Get cached result for query."""
        if not self.client:
            return None
        try:
            key = self._make_key(query)
            value = await self.client.get(key)
            if value is not None:
                logger.info(f'Cache HIT for query: {query[:50]}...')
                return int(value)
            logger.debug(f'Cache MISS for query: {query[:50]}...')
            return None
        except Exception as e:
            logger.error(f'Cache get error: {e}')
            return None

    async def set(self, query: str, result: int):
        """Cache query result."""
        if not self.client:
            return
        try:
            key = self._make_key(query)
            await self.client.set(key, str(result), ex=self.ttl)
            logger.debug(f'Cached result for query: {query[:50]}...')
        except Exception as e:
            logger.error(f'Cache set error: {e}')

    async def clear(self):
        if not self.client:
            return
        try:
            keys = []
            async for key in self.client.scan_iter(match='query:*'):
                keys.append(key)
            if keys:
                await self.client.delete(*keys)
                logger.info(f'Cleared {len(keys)} cached queries')
        except Exception as e:
            logger.error(f'Cache clear error: {e}')


cache = Cache()
