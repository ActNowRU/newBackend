import enum

from sqlalchemy.orm import relationship
from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Enum,
    DateTime,
    Boolean,
    LargeBinary,
    sql,
)

from database_initializer import Base


class CodeType(enum.Enum):
    qr_code = "qr"
    barcode = "barcode"
    digital = "digital"


class Code(Base):
    __tablename__ = "codes"

    value = Column(String, index=True, primary_key=True)
    code_type = Column(Enum(CodeType), nullable=False)
    content = Column(LargeBinary, nullable=False)

    is_valid = Column(Boolean, server_default=sql.True_(), nullable=False)
    expiration = Column(DateTime, nullable=True)
    created_at = Column(DateTime, index=True, nullable=True)

    goal_id = Column(Integer, ForeignKey("goals.id"), nullable=True)
    goal = relationship("Goal", back_populates="codes", lazy="selectin")

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    organization = relationship("Organization", back_populates="codes", lazy="selectin")

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="codes", lazy="selectin")

    def __str__(self):
        return f"Goal #{self.id}"
