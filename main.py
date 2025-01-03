import logging

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from pydantic import ValidationError

from lifespan import lifespan

from app import router
from app.admin.views import admin


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

admin.mount_to(app)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["GET,POST,PUT,DELETE"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.exception_handler(ValidationError)
async def validation_error_handler(request, exc):
    """
    Error handler for validation errors.
    Without this, FastAPI will just return a 500 error when using Pydantic as a form.
    It's because of the way FastAPI handles validation errors on declaration of a Pydantic model.

    :param request: Request
    :param exc: ValidationError
    :return: HTTPException
    """
    parsed_errors = []
    for item in exc.errors():
        parsed_item = {
            "type": item.get("type"),
            "loc": item.get("loc"),
            "msg": item.get("msg"),
            "input": str(item.get("input")),
            "ctx": {"error": str(item.get("ctx", {}).get("error"))},
        }
        parsed_errors.append(parsed_item)

    print(parsed_errors)

    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=parsed_errors,
    )


app.include_router(router.root_router)
