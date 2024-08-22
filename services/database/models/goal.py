from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Date,
    Time,
    JSON,
    DateTime,
)
from sqlalchemy.orm import relationship

from database_initializer import Base


class Goal(Base):
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    favorites_count = Column(Integer, index=True, nullable=True)
    cost = Column(Integer, index=True, nullable=True)
    event_date = Column(Date, index=True)
    event_time = Column(Time, index=True)
    creation_date = Column(DateTime, index=True)
    location = Column(JSON, index=True)
    description = Column(String, index=True)
    title = Column(String, index=True)

    content = Column(JSON, index=True, nullable=True)
    # ARRAY is compatible only with Postgresql
    # content = Column(ARRAY(String), index=True, nullable=True)

    owner_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    owner = relationship("Organization", back_populates="goals", lazy="selectin")

    stories = relationship("Story", back_populates="goals", lazy="selectin")

    def __str__(self):
        return f"Goal #{self.id}"
