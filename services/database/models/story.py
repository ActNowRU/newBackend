from sqlalchemy import (
    Column,
    String,
    Integer,
    PrimaryKeyConstraint,
    ForeignKey,
    Boolean,
    JSON,
    # ARRAY,
    DateTime,
)
from sqlalchemy.orm import relationship

from database_initializer import Base


class Story(Base):
    __tablename__ = "stories"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    descriptions = Column(String(2550), index=True, nullable=True)
    content = Column(JSON, index=True, nullable=True)
    # ARRAY is compatible only with Postgresql
    # content = Column(ARRAY(String), index=True, nullable=True)
    date_of_creation = Column(DateTime, index=True)

    is_recommended = Column(Boolean, default=False)

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="stories", lazy="selectin")

    goal_id = Column(Integer, ForeignKey("goals.id"), nullable=False)
    goals = relationship("Goal", back_populates="stories", lazy="selectin")

    PrimaryKeyConstraint("id", name="pk_story_id")

    def __str__(self):
        return f"Story #{self.id}"
