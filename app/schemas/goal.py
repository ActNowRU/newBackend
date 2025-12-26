from datetime import date, time
from typing import Optional, List

from pydantic import BaseModel, Field
from fastapi import File, UploadFile


class GoalCreateSchema(BaseModel):
    title: str = Field(..., description="The title of the goal", max_length=100)
    description: str = Field(
        ..., description="A detailed description of the goal", max_length=500
    )
    cost: Optional[int] = Field(
        None, description="The estimated cost associated with the goal"
    )

    prize_info: Optional[str] = Field(
        None, description="Information about the prize for achieving the goal"
    )
    prize_conditions: Optional[List[str]] = Field(
        None, description="Conditions to be met to claim the prize"
    )

    address: str = Field(..., description="The address related to the goal")

    dates: Optional[List[str]] = Field(
        None, description="List of specific dates related to the goal"
    )
    from_date: Optional[date] = Field(None, description="The start date of the goal")
    to_date: Optional[date] = Field(None, description="The end date of the goal")

    from_time: Optional[time] = Field(None, description="The start time of the goal")
    to_time: Optional[time] = Field(None, description="The end time of the goal")

    content: UploadFile = File(..., description="The cover for your goal")


class GoalUpdateSchema(GoalCreateSchema):
    content: Optional[UploadFile] = File(None, description="The cover for your goal")


class GoalSchema(GoalCreateSchema):
    id: int
    owner_id: int
    content: Optional[bytes]

    class Config:
        from_attributes = True
