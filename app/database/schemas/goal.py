from datetime import date, time
from typing import Optional, List

from fastapi import Form
from pydantic import BaseModel

from app.utils.forms import as_form


@as_form
class GoalCreateSchema(BaseModel):
    title: str = Form(...)
    description: str = Form(...)
    cost: int = Form(None)

    prize_info: Optional[str] = Form(None)
    prize_conditions: Optional[list[str]] = Form(None)

    address: str = Form(...)

    dates: Optional[list[date] | list[str] | None] = Form(None)
    from_date: Optional[date] = Form(None)
    to_date: Optional[date] = Form(None)

    from_time: Optional[time] = Form(None)
    to_time: Optional[time] = Form(None)


class GoalSchema(GoalCreateSchema):
    id: int
    owner_id: int
    content: Optional[List[bytes]]

    class Config:
        from_attributes = True
