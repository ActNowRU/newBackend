import enum

from fastapi import HTTPException, status
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
from sqlalchemy.orm import relationship

from app.database_initializer import Base
from app.core.auth import decode_token


class Gender(enum.Enum):
    male = "male"
    female = "female"


class Role(enum.Enum):
    admin = "admin"
    org_admin = "org.admin"
    # org_staff = "org.staff"
    consumer = "consumer"


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

    hashed_password = Column(LargeBinary, index=True, nullable=False)

    role = Column(Enum(Role), nullable=False)

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    organization = relationship("Organization", back_populates="users", lazy="selectin")

    stories = relationship("Story", back_populates="owner", lazy="selectin")
    codes = relationship("Code", back_populates="owner", lazy="selectin")

    UniqueConstraint("email", name="uq_user_email")
    PrimaryKeyConstraint("id", name="pk_user_id")

    def __repr__(self):
        return "<User {username!r}>".format(username=self.username)

    def __str__(self):
        return f"User #{self.email}"

    @staticmethod
    def get_current_user_by_token(token: str) -> dict:
        payload = decode_token(token)

        if payload["type"] != "access":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token type",
            )

        return payload
