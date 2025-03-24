from datetime import datetime
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship
from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    JSON,
    Date,
    Time,
    DateTime,
)

from app.utils.db import create_model_instance
from app.schemas.goal import GoalCreateSchema
from app.database_initializer import Base


class Goal(Base):
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String, index=True)
    cost = Column(Integer, index=True, nullable=True)

    dates = Column(JSON, index=True, nullable=True)

    from_date = Column(Date, index=True, nullable=True)
    to_date = Column(Date, index=True, nullable=True)

    from_time = Column(Time, index=True, nullable=True)
    to_time = Column(Time, index=True, nullable=True)

    created_at = Column(DateTime, index=True)
    address = Column(JSON, index=True)
    description = Column(String, index=True)

    prize_info = Column(String, index=True, nullable=True)
    prize_conditions = Column(JSON, index=True, nullable=True)

    content = Column(JSON, index=True, nullable=True)

    owner_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    owner = relationship("Organization", back_populates="goals", lazy="selectin")

    codes = relationship("Code", back_populates="goal", lazy="selectin")
    stories = relationship(
        "Story", back_populates="goal", lazy="selectin", cascade="all, delete-orphan"
    )

    def __str__(self):
        return f"Goal #{self.id}"

    @classmethod
    async def create(
        cls,
        session: AsyncSession,
        goal: GoalCreateSchema,
        content: List[bytes],
        owner_id: int,
    ) -> "Goal":
        db_goal = await create_model_instance(
            session=session,
            model=cls,
            **goal.model_dump(),
            content=content,
            owner_id=owner_id,
            created_at=datetime.now(),
        )

        return db_goal

    @classmethod
    async def get_by_id(cls, session: AsyncSession, goal_id: int) -> "Goal":
        goal_result = await session.execute(select(cls).filter(cls.id == goal_id))

        return goal_result.scalars().one()

    @classmethod
    async def get_all(cls, session: AsyncSession) -> list["Goal"]:
        all_goals_result = await session.execute(select(cls))

        return all_goals_result.scalars().all()

    @classmethod
    async def get_all_by_owner(
        cls, session: AsyncSession, owner_id: int
    ) -> List["Goal"]:
        all_goals_result = await session.execute(
            select(cls).filter(cls.owner_id == owner_id)
        )

        return all_goals_result.scalars().all()

    async def change(
        self,
        session: AsyncSession,
        goal: GoalCreateSchema,
        content: List[bytes],
    ) -> "Goal":
        for key, value in goal.model_dump().items():
            if key != "owner_id":
                setattr(self, key, value)

        self.content = content

        await session.commit()
        await session.refresh(self)

        return self

    async def delete(self, session: AsyncSession) -> None:
        await session.delete(self)
        await session.commit()
