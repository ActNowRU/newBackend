from pydantic import BaseModel


class ComplaintsCreate(BaseModel):
    value: str


class ComplaintsPostSchema(ComplaintsCreate):
    pass


class ComplaintsStorySchema(ComplaintsCreate):
    pass


class ComplaintsUserSchema(ComplaintsCreate):
    pass

