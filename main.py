import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pydantic import ValidationError

from lifespan import lifespan
from exceptions import validation_error_handler

from app import router


logging.basicConfig()
logging.getLogger("sqlalchemy.engine.Engine").disabled = True

app = FastAPI(
    lifespan=lifespan,
    title="GoalsAPI",
    description="The end-to-end APIs for the Goals discount services for companies and their customers.",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)


app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["GET,POST,PUT,DELETE,PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)


app.add_exception_handler(ValidationError, validation_error_handler)


app.include_router(router.root_router)
