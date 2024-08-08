from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from database_initializer import Base


class Like(Base):
    __tablename__ = "likes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    story_id = Column(Integer, ForeignKey("stories.id"), nullable=False)
    story = relationship("Story", back_populates="likes")

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="likes")

    UniqueConstraint("user_id", "story_id", name="uq_user_story_like")
