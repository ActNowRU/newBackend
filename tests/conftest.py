import pytest_asyncio

from typing import AsyncGenerator
from contextlib import asynccontextmanager

from httpx import AsyncClient, ASGITransport
from asgi_lifespan import LifespanManager
from fastapi import FastAPI

from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

import sys
import os
import inspect

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from app.router import root_router  # noqa: E402
from app.redis_initializer import get_redis  # noqa: E402
from app.database_initializer import init_models  # noqa: E402


@pytest_asyncio.fixture(scope="session")
async def app():
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Init anything on startup
        await init_models(clean=True)
        redis = await get_redis(decode_responses=False)
        FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
        yield
        # Clean up on shutdown
        # TODO: Add clean up

    app = FastAPI(
        lifespan=lifespan,
        title="Test",
        description="Test",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    app.include_router(root_router)

    async with LifespanManager(app) as manager:
        yield manager.app


@pytest_asyncio.fixture(scope="session")
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://localhost"
    ) as client:
        yield client


@pytest_asyncio.fixture(scope="session")
async def access_data(client: AsyncClient):
    response = await client.post(
        "/auth/login", data={"login": "test@test.com", "password": "Test123$"}
    )
    return response.json()
