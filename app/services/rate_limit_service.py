"""
Redis-backed fixed-window rate limiter.

Redis INCR is atomic, so this is safe under concurrency without extra
locking. Fixed-window is simpler than a sliding window/token bucket and is
sufficient for the spec's V1 scope ("basic API-key/project-based rate
limiting"); swap the algorithm here later without touching callers.
"""
import time

import redis.asyncio as redis

from app.core.config import get_settings

settings = get_settings()

_redis_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client


class RateLimitService:
    def __init__(self, client: redis.Redis | None = None):
        self._client = client or get_redis()

    async def check(self, *, key: str, limit_per_minute: int) -> tuple[bool, int]:
        window = int(time.time() // 60)
        redis_key = f"ratelimit:{key}:{window}"

        count = await self._client.incr(redis_key)
        if count == 1:
            await self._client.expire(redis_key, 65)

        remaining = max(limit_per_minute - count, 0)
        return count <= limit_per_minute, remaining
