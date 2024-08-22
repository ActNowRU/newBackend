from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.database.models.goal import Goal
from services.database.models.user import User
from services.database.schemas.goal import GoalBase


async def create_goal(session: AsyncSession, goal: GoalBase, token: str):
    current_user = User.get_current_user_by_token(token)
    owner_id = current_user["id"]
    date_of_creation = datetime.now()
    db_goal = Goal(**goal.dict(), owner_id=owner_id, date_of_creation=date_of_creation)
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


async def change_goal(session: AsyncSession, goal_id: int, goal: GoalBase):
    db_goal_result = await session.execute(select(Goal).filter(Goal.id == goal_id))
    db_goal = db_goal_result.scalars().one()

    for key, value in goal.dict().items():
        if key != "owner_id":
            setattr(db_goal, key, value)

    await session.commit()
    await session.refresh(db_goal)

    return db_goal
