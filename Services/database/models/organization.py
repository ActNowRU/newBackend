import enum

from sqlalchemy import (
    LargeBinary,
    Column,
    String,
    Integer,
    Boolean,
    Enum,
    JSON,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from database_initializer import Base


class OrganizationType(enum.Enum):
    cafe = "cafe"
    restaurant = "restaurant"
    tattoo = "tattoo"
    anticafe = "anticafe"
    bar = "bar"
    club = "club"
    beauty = "beauty"
    karaoke = "karaoke"
    clinic = "clinic"


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    username = Column(String(255), nullable=False)
    description = Column(String(2550), nullable=True)
    photo = Column(LargeBinary, nullable=True)

    inn_or_ogrn = Column(String(255), nullable=False)
    legal_address = Column(String(255), nullable=False)

    email = Column(String(255), index=True, unique=True, nullable=True)
    is_email_confirmed = Column(Boolean, default=False)

    organization_type = Column(Enum(OrganizationType), nullable=False)

    common_discount = Column(Integer, nullable=True)
    max_discount = Column(Integer, nullable=True)

    goals = relationship("Goal", back_populates="owner", lazy="selectin")
    places = relationship("Place", back_populates="organization", lazy="selectin")
    users = relationship("User", back_populates="organization", lazy="selectin")


class Place(Base):
    __tablename__ = "places"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    location = Column(JSON, index=True, nullable=False)
    address = Column(String(255), nullable=False)

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    organization = relationship(
        "Organization", back_populates="places", lazy="selectin"
    )
