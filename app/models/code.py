from datetime import datetime, timedelta
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship
from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Enum,
    DateTime,
    Boolean,
    LargeBinary,
    sql,
)

from app.database_initializer import Base
from app.schemas.code import CodeCreateSchema
from app.utils.db import create_model_instance
from app.types.enums import CodeType

DEFAULT_CODE_EXPIRATION = 60 * 5  # 5 minutes


class Code(Base):
    __tablename__ = "codes"

    value = Column(String, index=True, primary_key=True)
    code_type = Column(Enum(CodeType), nullable=False)
    content = Column(LargeBinary, nullable=False)

    is_valid = Column(Boolean, server_default=sql.True_(), nullable=False)
    expiration = Column(DateTime, nullable=True)
    created_at = Column(DateTime, index=True, nullable=True)

    goal_id = Column(Integer, ForeignKey("goals.id"), nullable=True)
    goal = relationship("Goal", back_populates="codes", lazy="selectin")

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    organization = relationship("Organization", back_populates="codes", lazy="selectin")

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="codes", lazy="selectin")

    def __str__(self):
        return f"Goal #{self.id}"

    @classmethod
    async def create(
        cls,
        session: AsyncSession,
        code: CodeCreateSchema,
    ) -> "Code":
        created_at = datetime.now()

        db_goal = await create_model_instance(
            session=session,
            model=cls,
            **code.model_dump(),
            expiration=created_at + timedelta(seconds=DEFAULT_CODE_EXPIRATION),
            created_at=created_at,
        )

        return db_goal

    async def get_vizited_places_by_user(
        session: AsyncSession, user_id: int
    ) -> List["Code"]:
        db_codes_result = await session.execute(
            select(Code).where((Code.owner_id == user_id) & (not Code.is_valid))
        )
        codes = db_codes_result.scalars().all()

        organizations = []

        for code in codes:
            if code.organization:
                organizations.append(code.organization)
            elif code.goal and code.goal.organization:
                organizations.append(code.goal.organization)

        return organizations

    async def get_by_value(session: AsyncSession, value: int) -> "Code":
        db_code_result = await session.execute(select(Code).where(Code.value == value))

        return db_code_result.scalars().one()

    async def blacklist(self, session: AsyncSession) -> "Code":
        self.is_valid = False

        await session.commit()
        await session.refresh(self)

        return self
