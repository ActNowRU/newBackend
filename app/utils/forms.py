from fastapi import Form
from pydantic import BaseModel


def as_form(cls: BaseModel):
    """This decorator allows FastAPI to use pydantic as form as well"""
    cls.__signature__ = cls.__signature__.replace(
        parameters=[
            arg.replace(default=Form(arg.default))
            for arg in cls.__signature__.parameters.values()
        ]
    )
    return cls
