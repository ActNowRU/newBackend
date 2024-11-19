from sqlalchemy import (
    Column,
    String,
    Integer,
    PrimaryKeyConstraint,
    ForeignKey,
    Boolean,
    JSON,
    SmallInteger,
    DateTime,
)
from sqlalchemy.orm import relationship

from app.database_initializer import Base


class Story(Base):
    __tablename__ = "stories"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    description = Column(String(2550), index=True, nullable=True)
    content = Column(JSON, index=True, nullable=True)

    created_at = Column(DateTime, index=True)

    is_recommending = Column(Boolean, default=False)

    position = Column(SmallInteger, default=0, nullable=False)

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="stories", lazy="selectin")

    goal_id = Column(Integer, ForeignKey("goals.id"), nullable=True)
    goal = relationship("Goal", back_populates="stories", lazy="selectin")

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    organization = relationship(
        "Organization", back_populates="stories", lazy="selectin"
    )

    PrimaryKeyConstraint("id", name="pk_story_id")

    def __str__(self):
        return f"Story #{self.id}"
