from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

from app.redis_initializer import get_redis
from app.database_initializer import init_models


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Init anything on startup
    await init_models()
    redis = await get_redis(decode_responses=False)
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
    yield
    # Clean up on shutdown
    # TODO: Add clean up
