from datetime import datetime
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.goal import Goal
from app.database.schemas.goal import GoalCreateSchema


async def create_goal(
    session: AsyncSession, goal: GoalCreateSchema, content: List[bytes], owner_id: int
):
    created_at = datetime.now()
    db_goal = Goal(
        **goal.model_dump(), content=content, owner_id=owner_id, created_at=created_at
    )
    session.add(db_goal)

    await session.commit()
    await session.refresh(db_goal)

    return db_goal


async def get_goal_by_id(session: AsyncSession, goal_id: int):
    goal_result = await session.execute(select(Goal).filter(Goal.id == goal_id))

    return goal_result.scalars().one()


async def get_all_user_goals(session: AsyncSession, owner_id: int):
    all_goals_result = await session.execute(
        select(Goal).filter(Goal.owner_id == owner_id)
    )

    return all_goals_result.scalars().all()


async def change_goal(
    session: AsyncSession, goal_id: int, goal: GoalCreateSchema, content: List[bytes]
):
    db_goal_result = await session.execute(select(Goal).filter(Goal.id == goal_id))
    db_goal = db_goal_result.scalars().one()

    for key, value in goal.model_dump().items():
        if key != "owner_id":
            setattr(db_goal, key, value)

    db_goal.content = content

    await session.commit()
    await session.refresh(db_goal)

    return db_goal
