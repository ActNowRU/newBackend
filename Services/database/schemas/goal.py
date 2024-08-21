from datetime import date, time
from typing import Optional

from pydantic import BaseModel


class GoalBase(BaseModel):
    event_date: date
    event_time: time
    location: str
    description: str
    title: str
    content: Optional[list]


class Goal(GoalBase):
    id: int
    owner_id: int

    class Config:
        from_attributes = True
