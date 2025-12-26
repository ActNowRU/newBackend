import pytest_asyncio
import logging

from typing import AsyncGenerator
from contextlib import asynccontextmanager

from httpx import AsyncClient, ASGITransport
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from pydantic import ValidationError

from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

import os

# Set debug mode for successful testing (it should be before importing app modules)
os.environ["DEBUG"] = "true"

from exceptions import validation_error_handler
from app.router import root_router
from app.redis_initializer import get_redis
from app.database_initializer import init_models
from create_superuser import create_superuser

# Configure logging
logging.basicConfig(level=logging.INFO)
logging.getLogger("sqlalchemy.engine.Engine").disabled = True
logging.getLogger("httpx").disabled = True

logger = logging.getLogger(__name__)


@pytest_asyncio.fixture(scope="session")
async def app():
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Init anything on startup
        await init_models(clean=True)
        await create_superuser("testadmin", "adminpasswD1$")
        redis = await get_redis(decode_responses=False)
        FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")

        yield
        # Clean up on shutdown
        # TODO: Add clean up

    app = FastAPI(lifespan=lifespan)

    app.include_router(root_router)

    app.add_exception_handler(ValidationError, validation_error_handler)

    async with LifespanManager(app) as manager:
        yield manager.app


@pytest_asyncio.fixture(scope="session")
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://localhost/api"
    ) as client:
        yield client


@pytest_asyncio.fixture(scope="session")
async def access_data(client: AsyncClient):
    response_log = await client.post(
        "/auth/login", data={"login": "test@test.com", "password": "Test123$"}
    )
    logger.info(
        f"Initial login attempt: {response_log.status_code}, {response_log.json()}"
    )

    if response_log.status_code != 200:
        response_reg = await client.post(
            "/organization/register",
            data={
                "name": "Test Org",
                "email": "test@test.com",
                "organization_type": "кафе",
                "password": "Test123$",
                "inn_or_ogrn": "1234567890",
                "legal_address": "Gorbunova Street, 14, Moscow, 121596",
            },
        )
        logger.info(
            f"Registration attempt: {response_reg.status_code}, {response_reg.json()}"
        )
        if response_reg.status_code != 201:
            raise Exception(
                f"Failed to register user. Status code: {response_reg.status_code}, response: {response_reg.json()}"
            )

        response_log = await client.post(
            "/auth/login", data={"login": "test@test.com", "password": "Test123$"}
        )
        logger.info(
            f"Second login attempt: {response_log.status_code}, {response_log.json()}"
        )

        if not response_log.json().get("access_token"):
            raise Exception(
                f"Failed to login user. Status code: {response_log.status_code}, response: {response_log.json()}"
            )

    return response_log.json()


@pytest_asyncio.fixture(scope="session")
async def access_data_admin(client: AsyncClient):
    response = await client.post(
        "/auth/login", data={"login": "testadmin", "password": "adminpasswD1$"}
    )

    logger.info(f"Admin login attempt: {response.status_code}, {response.json()}")

    return response.json()
