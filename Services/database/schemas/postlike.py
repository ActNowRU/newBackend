from pydantic import BaseModel


class PostLikeCreateSchema(BaseModel):
    post_ud: int


class Like(PostLikeCreateSchema):
    id: int

    class Config:
        orm_mode = True
        from_attributes = True
