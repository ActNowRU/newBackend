import enum

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
from sqlalchemy.orm import relationship

from database_initializer import Base


class OrganizationType(enum.Enum):
    cafe = "кафе"
    restaurant = "ресторан"
    tattoo = "тату-салон"
    anticafe = "антикафе"
    bar = "бар"
    club = "клуб"
    beauty = "салон красоты"
    karaoke = "караоке"
    clinic = "клиника"


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


class Place(Base):
    __tablename__ = "places"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    name = Column(String, index=True, nullable=False)
    address = Column(String(255), nullable=False)

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    organization = relationship(
        "Organization", back_populates="places", lazy="selectin"
    )
