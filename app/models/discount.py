from sqlalchemy import Column, Integer, ForeignKey, Float, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, select
from sqlalchemy.exc import NoResultFound
from app.database_initializer import Base
from sqlalchemy.ext.asyncio import AsyncSession


class Discount(Base):
    __tablename__ = "discounts"

    id = Column(Integer, primary_key=True, index=True)
    discount_percentage = Column(Float, nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    user = relationship("User", back_populates="discounts")
    organization = relationship("Organization", back_populates="discounts")

    @classmethod
    async def create(
        cls,
        session: AsyncSession,
        user_id: int,
        organization_id: int,
        discount_percentage: float,
    ) -> "Discount":
        """Create a new discount bundle in the database."""
        discount = cls(
            user_id=user_id,
            organization_id=organization_id,
            discount_percentage=discount_percentage,
        )
        session.add(discount)
        await session.commit()
        await session.refresh(discount)
        return discount

    @classmethod
    async def get_by_user_and_organization(
        cls, session: AsyncSession, user_id: int, organization_id: int
    ) -> "Discount":
        """Get discount by user and organization."""
        result = await session.execute(
            select(cls).where(
                cls.user_id == user_id, cls.organization_id == organization_id
            )
        )
        try:
            return result.scalars().one()
        except NoResultFound:
            return None

    async def update_percentage(
        self, session: AsyncSession, discount_percentage: float
    ) -> "Discount":
        """Update the discount percentage in the database."""
        self.discount_percentage = discount_percentage
        await session.commit()
        await session.refresh(self)
        return self
