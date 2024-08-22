from typing import Optional

from pydantic import BaseModel


class StoryCreateSchema(BaseModel):
    descriptions: str
    content: Optional[list]
    goal_id: int


class Story(StoryCreateSchema):
    id: int
    owner_id: int

    class Config:
        from_attributes = True


class StoryChangeSchema(BaseModel):
    descriptions: str
    content: str

    class Config:
        from_attributes = True
