from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship

from database_initializer import Base


class Complaint_post(Base):
    __tablename__ = "complaints_post"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    value = Column(String, index=True, nullable=False)

    post_id = Column(Integer, ForeignKey("post.id"), nullable=True)
    post = relationship("Post", back_populates="complaints")
