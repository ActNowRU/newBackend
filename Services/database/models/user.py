import jwt
from fastapi import HTTPException, status
from sqlalchemy import (
    LargeBinary,
    Column,
    String,
    Integer,
    UniqueConstraint,
    PrimaryKeyConstraint,
)
from sqlalchemy.orm import relationship

import settings
from database_initializer import Base
from services.database.models.tags import user_tags


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, index=True)
    user_name = Column(String(255), index=True, unique=True)
    first_name = Column(String(255), index=True, nullable=False)
    second_name = Column(String(255), index=True, nullable=False)
    patronymic = Column(String(255), index=True)
    hashed_password = Column(LargeBinary, nullable=False)

    stories = relationship("Story", back_populates="owner")
    posts = relationship("Post", back_populates="owner")

    likes = relationship("Like", back_populates="owner")
    post_likes = relationship("PostLike", back_populates="owner")

    complaints = relationship("Complaint_user", back_populates="user")

    tags = relationship("Tags", secondary=user_tags, backref="users")

    UniqueConstraint("email", name="uq_user_email")
    PrimaryKeyConstraint("id", name="pk_user_id")

    def __repr__(self):
        return "<User {user_name!r}>".format(user_name=self.user_name)

    def get_current_user_by_token(token: str):
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )

    def _str_(self):
        return f"User #{self.email}"
