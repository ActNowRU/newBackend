from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.database.models.story import Story
from services.database.models.user import User
from services.database.schemas.story import StoryCreateSchema, StoryChangeSchema


async def create_story(session: AsyncSession, story: StoryCreateSchema, token: str):
    current_user = User.get_current_user_by_token(token)
    owner_id = current_user["id"]
    date_of_creation = datetime.now()
    db_story = Story(
        **story.dict(), owner_id=owner_id, date_of_creation=date_of_creation
    )
    session.add(db_story)

    await session.commit()
    await session.refresh(db_story)

    return db_story


async def get_story_by_id(session: AsyncSession, story_id: int):
    story_result = await session.execute(select(Story).filter(Story.id == story_id))
    return story_result.scalars().one()


async def get_all_user_stories(session: AsyncSession, owner_id: int):
    stories_of_user_result = await session.execute(
        select(Story).filter(Story.owner_id == owner_id)
    )

    return stories_of_user_result.scalars().all()


async def get_all_goal_story(session: AsyncSession, goal_id: int):
    stories_of_goal_result = await session.execute(
        select(Story).filter(Story.goal_id == goal_id)
    )

    return stories_of_goal_result.scalars().all()


async def change_story(session: AsyncSession, story_id, story: StoryChangeSchema):
    db_story_result = await session.execute(select(Story).filter(Story.id == story_id))
    db_story = db_story_result.scalars().one()

    for key, value in story.dict().items():
        if key not in ["owner_id", "goal_id"]:
            setattr(db_story, key, value)

    await session.commit()
    await session.refresh(db_story)

    return db_story
