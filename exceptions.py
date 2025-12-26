from fastapi import HTTPException, status


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
