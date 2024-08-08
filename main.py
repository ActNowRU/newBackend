from contextlib import asynccontextmanager

import fastapi

import router
from database_initializer import init_models


@asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
    # Load
    await init_models()
    yield
    # Clean up
    # TODO: Add clean up


app = fastapi.FastAPI(lifespan=lifespan)

app.include_router(router.root_router)
