from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    JSON,
    Date,
    Time,
    DateTime,
)
from sqlalchemy.orm import relationship

from database_initializer import Base


class Goal(Base):
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String, index=True)
    cost = Column(Integer, index=True, nullable=True)

    dates = Column(JSON, index=True, nullable=True)

    from_date = Column(Date, index=True, nullable=True)
    to_date = Column(Date, index=True, nullable=True)

    from_time = Column(Time, index=True, nullable=True)
    to_time = Column(Time, index=True, nullable=True)

    created_at = Column(DateTime, index=True)
    address = Column(JSON, index=True)
    description = Column(String, index=True)

    prize_info = Column(String, index=True, nullable=True)
    prize_conditions = Column(JSON, index=True, nullable=True)

    content = Column(JSON, index=True, nullable=True)

    owner_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    owner = relationship("Organization", back_populates="goals", lazy="selectin")

    codes = relationship("Code", back_populates="goal", lazy="selectin")
    stories = relationship("Story", back_populates="goal", lazy="selectin")

    def __str__(self):
        return f"Goal #{self.id}"
