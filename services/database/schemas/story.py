from typing import Optional, List

from pydantic import BaseModel
from fastapi import Form

from utils.forms import as_form


@as_form
class StoryCreateSchema(BaseModel):
    description: str = Form(...)
    is_recommending: bool = Form(...)
    goal_id: int = Form(None)
    organization_id: int = Form(None)


class StorySchema(StoryCreateSchema):
    id: int
    owner_id: int
    position: Optional[int]
    content: Optional[List[bytes]]

    class Config:
        from_attributes = True


@as_form
class StoryChangeSchema(BaseModel):
    description: str = Form(...)
    is_recommending: bool = Form(...)

    class Config:
        from_attributes = True
