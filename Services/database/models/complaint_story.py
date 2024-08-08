from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship

from database_initializer import Base


class Complaint_story(Base):
    __tablename__ = "complaints_story"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    value = Column(String, index=True, nullable=False)

    story_id = Column(Integer, ForeignKey("stories.id"), nullable=True)
    story = relationship("Story", back_populates="complaints")
