from sqlalchemy import (
    Column,
    String,
    Integer,
    PrimaryKeyConstraint,
    ForeignKey,
    JSON,
    # ARRAY,
    DateTime,
)
from sqlalchemy.orm import relationship

from database_initializer import Base
from services.database.models.tags import story_tags


class Story(Base):  #
    __tablename__ = "stories"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    descriptions = Column(String(2550), index=True, nullable=True)
    content = Column(JSON, index=True, nullable=True)
    # ARRAY is compatible only with Postgresql
    # content = Column(ARRAY(String), index=True, nullable=True)
    date_of_creation = Column(DateTime, index=True)

    tags = relationship("Tags", secondary=story_tags, backref="stories")

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="stories")

    post_id = Column(Integer, ForeignKey("post.id"), nullable=False)
    posts = relationship("Post", back_populates="stories")

    likes = relationship("Like", back_populates="story")
    complaints = relationship("Complaint_story", back_populates="story")

    PrimaryKeyConstraint("id", name="pk_story_id")

    def _str_(self):
        return f"Story #{self.id}"
