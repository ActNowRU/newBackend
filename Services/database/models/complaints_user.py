from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship

from database_initializer import Base


class Complaint_user(Base):
    __tablename__ = "complaints_user"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    value = Column(String, index=True, nullable=False)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user = relationship("User", back_populates="complaints")
