from pydantic import BaseModel


class TagBase(BaseModel):
    type: str
    name: str


class Tag(TagBase):
    id: int

    class Config:
        orm_mode = True
