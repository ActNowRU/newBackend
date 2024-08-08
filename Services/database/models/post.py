from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Date,
    Time,
    # ARRAY,
    JSON,
    DateTime,
)
from sqlalchemy.orm import relationship

from database_initializer import Base
from services.database.models.tags import post_tags


class Post(Base):
    __tablename__ = "post"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    favorites_count = Column(Integer, index=True, nullable=True)
    cost = Column(Integer, index=True, nullable=True)
    event_date = Column(Date, index=True)
    event_time = Column(Time, index=True)
    date_of_creation = Column(DateTime, index=True)
    location = Column(String, index=True)
    description = Column(String, index=True)
    title = Column(String, index=True)

    content = Column(JSON, index=True, nullable=True)
    # ARRAY is compatible only with Postgresql
    # content = Column(ARRAY(String), index=True, nullable=True)

    tags = relationship("Tags", secondary=post_tags, backref="post")

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    owner = relationship("User", back_populates="posts")

    post_likes = relationship("PostLike", back_populates="post")
    stories = relationship("Story", back_populates="posts")

    complaints = relationship("Complaint_post", back_populates="post")

    def _str_(self):
        return f"Post #{self.id}"
