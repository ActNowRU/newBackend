import random

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import relationship
from sqlalchemy import (
    LargeBinary,
    Column,
    String,
    Integer,
    Boolean,
    Date,
    Enum,
    ForeignKey,
    UniqueConstraint,
    PrimaryKeyConstraint,
)

from app.services.auth.password import hash_password
from app.schemas.user import UserCreateSchema
from app.utils.db import create_model_instance
from app.database_initializer import Base
from app.types.enums import Gender, Role

import settings


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    first_name = Column(String(255), index=True, nullable=True)
    username = Column(String(255), index=True, unique=True, nullable=True)

    description = Column(String(2550), index=True, nullable=True)
    birth_date = Column(Date, index=True, nullable=True)
    gender = Column(Enum(Gender), nullable=True)
    photo = Column(LargeBinary, index=True, nullable=True)

    email = Column(String(255), index=True, unique=True, nullable=True)
    is_email_confirmed = Column(Boolean, default=False)

    last_code = Column(String(5), default="")

    hashed_password = Column(LargeBinary, index=True, nullable=False)

    role = Column(Enum(Role), nullable=False)

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    organization = relationship("Organization", back_populates="users", lazy="selectin")

    stories = relationship("Story", back_populates="owner", lazy="selectin")
    codes = relationship("Code", back_populates="owner", lazy="selectin")
    discounts = relationship("Discount", back_populates="user", lazy="selectin")

    UniqueConstraint("email", name="uq_user_email")
    PrimaryKeyConstraint("id", name="pk_user_id")

    def __repr__(self):
        return "<User {username!r}>".format(username=self.username)

    def __str__(self):
        return f"User #{self.email}"

    @classmethod
    async def create(
        cls,
        session: AsyncSession,
        user_schema: UserCreateSchema,
        role: str,
        photo: bytes | None = None,
    ) -> "User":
        """Create a new user in the database."""
        user_data = user_schema.model_dump()
        user_data["role"] = role

        if settings.DEBUG:
            user_data["is_email_confirmed"] = True

        user_data["hashed_password"] = hash_password(user_data.pop("password"))

        user = await create_model_instance(session, model=cls, **user_data, photo=photo)

        return user

    @classmethod
    async def get_by_id_or_login(
        cls,
        session: AsyncSession,
        user_id: int | None = None,
        login: str | None = None,
    ) -> "User":
        """Get user by id or login (username or email)."""
        query = select(cls)

        if user_id is not None:
            query = query.filter(cls.id == user_id)
        elif login is not None:
            query = query.filter((cls.username == login) | (cls.email == login))

        try:
            return (await session.execute(query)).scalars().one()
        except NoResultFound:
            return None

    async def set_last_code(self, session: AsyncSession) -> str:
        code = "".join([str(random.randint(0, 9)) for _ in range(6)])
        setattr(self, "last_code", code)

        await session.commit()

        return code

    async def delete(self, session: AsyncSession) -> None:
        """Delete a user from the database."""
        await session.delete(self)
        await session.commit()

    async def update(self, session: AsyncSession, updates: dict[str, Any]) -> "User":
        """Update a user in the database."""
        for key, value in updates.items():
            if value is None:
                continue
            if key == "password":
                key = "hashed_password"
                value = hash_password(value)
            setattr(self, key, value)

        await session.commit()
        await session.refresh(self)

        return self
