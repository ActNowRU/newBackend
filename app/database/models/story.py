from datetime import datetime
from typing import List

from sqlalchemy.orm import relationship
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import (
    Column,
    String,
    Integer,
    PrimaryKeyConstraint,
    ForeignKey,
    Enum,
    Boolean,
    JSON,
    SmallInteger,
    DateTime,
)

from app.database.utils import create_model_instance
from app.database.schemas.story import StoryCreateSchema, StoryChangeSchema
from app.database_initializer import Base
from app.database.enums import ModerationState


class Story(Base):
    __tablename__ = "stories"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    description = Column(String(2550), index=True, nullable=True)
    content = Column(JSON, index=True, nullable=True)

    created_at = Column(DateTime, index=True)

    moderation_state = Column(Enum(ModerationState), default=ModerationState.on_check)
    is_recommending = Column(Boolean, default=False)

    position = Column(SmallInteger, default=0, nullable=False)

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="stories", lazy="selectin")

    goal_id = Column(Integer, ForeignKey("goals.id"), nullable=True)
    goal = relationship("Goal", back_populates="stories", lazy="selectin")

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    organization = relationship(
        "Organization", back_populates="stories", lazy="selectin"
    )

    PrimaryKeyConstraint("id", name="pk_story_id")

    def __str__(self):
        return f"Story #{self.id}"

    @classmethod
    async def create(
        cls,
        session: AsyncSession,
        story: StoryCreateSchema,
        content: List[bytes],
        owner_id: int,
    ) -> "Story":
        db_story = await create_model_instance(
            session=session,
            model=cls,
            **story.model_dump(),
            content=content,
            owner_id=owner_id,
            created_at=datetime.now(),
        )

        return db_story

    @classmethod
    async def get_by_id(cls, session: AsyncSession, story_id: int) -> "Story":
        story_result = await session.execute(
            select(cls).filter(
                cls.id == story_id & cls.moderation_state == ModerationState.allowed
            )
        )
        return story_result.scalars().one()

    @classmethod
    async def get_all(cls, session: AsyncSession, moderation_state) -> List["Story"]:
        stories_of_user_result = await session.execute(
            select(cls).filter(cls.moderation_state == moderation_state)
        )

        return stories_of_user_result.scalars().all()

    @classmethod
    async def get_all_by_owner(
        cls, session: AsyncSession, owner_id: int
    ) -> List["Story"]:
        stories_of_user_result = await session.execute(
            select(cls).filter(
                cls.owner_id
                == owner_id & cls.moderation_state
                == ModerationState.allowed
            )
        )

        return stories_of_user_result.scalars().all()

    @classmethod
    async def get_all_by_organization(
        cls, session: AsyncSession, organization_id: int
    ) -> List["Story"]:
        stories_of_organization_result = await session.execute(
            select(cls).filter(
                cls.goal.owner_id
                == organization_id & cls.moderation_state
                == ModerationState.allowed
            )
        )

        return stories_of_organization_result.scalars().all()

    @classmethod
    async def get_all_by_goal(
        cls, session: AsyncSession, goal_id: int
    ) -> List["Story"]:
        stories_of_goal_result = await session.execute(
            select(cls).filter(
                cls.goal_id == goal_id & cls.moderation_state == ModerationState.allowed
            )
        )

        return stories_of_goal_result.scalars().all()

    @staticmethod
    async def get_favorite(session: AsyncSession, organization_id: int) -> dict:
        from app.database.models.goal import Goal

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

    async def delete(self, session: AsyncSession) -> None:
        await session.delete(self)
        await session.commit()

    async def change_moderation_state(
        self, session: AsyncSession, moderation_state: ModerationState
    ) -> "Story":
        self.moderation_state = moderation_state

        await session.commit()
        await session.refresh(self)

        return self

    async def change(
        self,
        session: AsyncSession,
        story: StoryChangeSchema,
        content: List[bytes],
    ) -> "Story":
        if not isinstance(story, dict):
            story = story.model_dump()

        story["moderation_state"] = ModerationState.on_check

        for key, value in story.items():
            if key not in ["owner_id", "goal_id", "organization_id"]:
                setattr(self, key, value)

        self.content = content

        await session.commit()
        await session.refresh(self)

        return self
