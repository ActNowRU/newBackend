from contextlib import asynccontextmanager

from fastapi import FastAPI

from database_initializer import init_models


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Init anything on startup
    await init_models()
    yield
    # Clean up on shutdown
    # TODO: Add clean up
