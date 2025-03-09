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
    Float,
    Enum,
    ForeignKey,
)

from app.models.user import Role, User
from app.schemas.organization import OrganizationCreateSchema
from app.schemas.user import UserCreateSchema
from app.utils.db import create_model_instance
from app.database_initializer import Base
from app.enums import OrganizationType


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    name = Column(String(255), nullable=False)
    description = Column(String(2550), nullable=True)
    photo = Column(LargeBinary, nullable=True)

    inn_or_ogrn = Column(String(255), nullable=False)
    legal_address = Column(String(255), nullable=False)

    email = Column(String(255), index=True, unique=True, nullable=True)
    is_email_confirmed = Column(Boolean, default=False)

    organization_type = Column(Enum(OrganizationType), nullable=False)

    static_discount = Column(Float, nullable=True)

    common_discount = Column(Float, nullable=True)
    max_discount = Column(Float, nullable=True)

    step_amount = Column(Integer, nullable=True)
    days_to_step_back = Column(Integer, nullable=True)

    goals = relationship("Goal", back_populates="owner", lazy="selectin")
    places = relationship("Place", back_populates="organization", lazy="selectin")
    stories = relationship("Story", back_populates="organization", lazy="selectin")
    users = relationship("User", back_populates="organization", lazy="selectin")
    codes = relationship("Code", back_populates="organization", lazy="selectin")
    discounts = relationship("Discount", back_populates="organization", lazy="selectin")

    @classmethod
    async def create(
        cls,
        session: AsyncSession,
        organization_schema: OrganizationCreateSchema,
        photo: bytes,
    ) -> "Organization":
        user_data = organization_schema.model_dump()

        user_data.pop("name")

        organization = organization_schema.model_dump()
        organization.pop("password")

        db_org = await create_model_instance(
            session=session, model=cls, **organization, photo=photo
        )

        user_data["username"] = f"admin{db_org.id}"

        db_user = await User.create(
            session=session,
            user_schema=UserCreateSchema.model_validate(user_data),
            role=Role.org_admin,
        )

        db_user.organization_id = db_org.id

        await session.commit()
        await session.refresh(db_user)

        return db_org, db_user

    async def get_by_id(
        session: AsyncSession,
        organization_id: int | None = None,
    ) -> "Organization":
        if organization_id:
            db_user_result = await session.execute(
                select(Organization).filter(Organization.id == organization_id)
            )
        else:
            return None

        db_user = db_user_result.scalars().one()

        return db_user

    async def update(
        self, session: AsyncSession, updates: dict[str, Any]
    ) -> "Organization":
        for key, value in updates.items():
            if value is None:
                continue
            setattr(self, key, value)

        await session.commit()
        await session.refresh(self)

        return self


class Place(Base):
    __tablename__ = "places"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    name = Column(String, index=True, nullable=False)
    address = Column(String(255), nullable=False)

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    organization = relationship(
        "Organization", back_populates="places", lazy="selectin"
    )

    @classmethod
    async def set(
        cls, session: AsyncSession, organization_id: int, place: dict
    ) -> "Place":
        place["organization_id"] = organization_id

        db_place_result = await session.execute(
            select(cls)
            .filter(cls.organization_id == organization_id)
            .filter(cls.address == place["address"])
        )

        if db_place := db_place_result.scalars().one_or_none():
            return db_place

        db_place = await create_model_instance(session=session, model=cls, **place)

        return db_place

    @classmethod
    async def get_all(cls, session: AsyncSession) -> list["Place"]:
        places_result = await session.execute(
            select(cls).filter(cls.organization_id.isnot(None))
        )

        return places_result.scalars().all()

    @classmethod
    async def get_by_id(cls, session: AsyncSession, place_id: int) -> "Place":
        place_result = await session.execute(
            select(cls).filter(cls.organization_id.isnot(None) & (cls.id == place_id))
        )

        try:
            return place_result.scalars().one()
        except NoResultFound:
            return None

    @classmethod
    async def get_by_query(
        cls,
        session: AsyncSession,
        search_query: str,
        org_type: str,
        has_goals: bool,
        has_discount: bool,
    ) -> list["Place"]:
        to_filter = select(Organization)

        if org_type:
            to_filter = to_filter.filter(Organization.organization_type == org_type)
        if search_query:
            to_filter = to_filter.filter(Organization.name.ilike(f"%{search_query}%"))
        if has_goals:
            to_filter = to_filter.filter(Organization.goals.isnot(None))
        if has_discount:
            to_filter = to_filter.filter(Organization.common_discount.isnot(None))

        orgs_result = await session.execute(to_filter)

        orgs = orgs_result.scalars().all()

        if orgs:
            orgs_ids = [org.id for org in orgs]

            places_result = await session.execute(
                select(cls).filter(cls.organization_id.in_(orgs_ids))
            )

            return places_result.scalars().all()

        return []
