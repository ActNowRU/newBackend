from services.database.models.code import CodeType

from typing import Optional
from pydantic import BaseModel


class CodeSchema(BaseModel):
    organization_id: Optional[int] = None
    goal_id: Optional[int] = None
    owner_id: int

    class Config:
        from_attributes = True


class CodeCreateSchema(CodeSchema):
    code_type: CodeType
    value: str
    content: Optional[str | bytes] = None

    class Config:
        from_attributes = True
