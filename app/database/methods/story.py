from datetime import datetime
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.goal import Goal
from app.database.models.story import Story
from app.database.schemas.story import StoryCreateSchema, StoryChangeSchema


async def create_story(
    session: AsyncSession, story: StoryCreateSchema, content: List[bytes], owner_id: int
):
    created_at = datetime.now()
    db_story = Story(
        **story.model_dump(), content=content, owner_id=owner_id, created_at=created_at
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


async def change_story(
    session: AsyncSession, story_id, story: StoryChangeSchema, content: List[bytes]
):
    db_story_result = await session.execute(select(Story).filter(Story.id == story_id))
    db_story = db_story_result.scalars().one()

    if not isinstance(story, dict):
        story = story.model_dump()

    for key, value in story.items():
        if key not in ["owner_id", "goal_id", "organization_id"]:
            setattr(db_story, key, value)

    db_story.content = content

    await session.commit()
    await session.refresh(db_story)

    return db_story


async def get_favorite_stories(session: AsyncSession, organization_id: int):
    # Stories for this organization
    stories_by_organization_result = await session.execute(
        select(Story).filter(Story.organization_id == organization_id)
    )
    stories = stories_by_organization_result.scalars().all()

    # Goals in this organization
    goals_by_organization_result = await session.execute(
        select(Goal).filter(Goal.owner_id == organization_id)
    )
    goals_by_organization = goals_by_organization_result.scalars().all()

    # Stories for goals in this organization
    all_stories_result = await session.execute(select(Story).filter(Story.goal_id))
    all_stories = all_stories_result.scalars().all()

    stories_by_goal = [
        story for story in all_stories if story.goal in goals_by_organization
    ]

    stories += stories_by_goal

    return {story.position: story for story in stories if story.position}
