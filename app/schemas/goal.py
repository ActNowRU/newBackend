from datetime import date, time
from typing import Optional, List

from pydantic import BaseModel


class GoalCreateSchema(BaseModel):
    title: str = None
    description: str = None
    cost: Optional[int] = None

    prize_info: Optional[str] = None
    prize_conditions: Optional[List[str]] = None

    address: str = None

    dates: Optional[List[str]] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None

    from_time: Optional[time] = None
    to_time: Optional[time] = None


class GoalSchema(GoalCreateSchema):
    id: int
    owner_id: int
    content: Optional[bytes]

    class Config:
        from_attributes = True
