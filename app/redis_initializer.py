from redis import asyncio as aioredis
from fastapi import HTTPException

from settings import REDIS_HOST

redis = None


async def get_redis(decode_responses=True) -> aioredis.Redis:
    global redis

    if not decode_responses:
        redis = await aioredis.from_url(REDIS_HOST, decode_responses=False)

    if not redis:
        try:
            redis = await aioredis.from_url(REDIS_HOST, decode_responses=True)
        except aioredis.RedisError as err:
            raise HTTPException(
                status_code=500, detail=f"Unable to connect to Redis: {err}"
            )

    return redis
