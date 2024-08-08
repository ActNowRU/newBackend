from sqlalchemy.ext.asyncio import AsyncSession

from services.database.models.complaint_post import Complaint_post
from services.database.models.complaint_story import Complaint_story
from services.database.models.complaints_user import Complaint_user
from services.database.schemas.complaints import (
    ComplaintsPostSchema,
    ComplaintsUserSchema,
    ComplaintsStorySchema,
)


async def create_post_complaint(
        session: AsyncSession, complaint: ComplaintsPostSchema, post_id: int
):
    db_complaint = Complaint_post(**complaint.dict(), post_id=post_id)
    session.add(db_complaint)

    await session.commit()
    await session.refresh(db_complaint)

    return db_complaint


async def create_story_complaint(
        session: AsyncSession, complaint: ComplaintsStorySchema, story_id: int
):
    db_complaint = Complaint_story(**complaint.dict(), story_id=story_id)
    session.add(db_complaint)

    await session.commit()
    await session.refresh(db_complaint)

    return db_complaint


async def create_user_complaint(
        session: AsyncSession, complaint: ComplaintsUserSchema, user_id: int
):
    db_complaint = Complaint_user(**complaint.dict(), user_id=user_id)
    session.add(db_complaint)

    await session.commit()
    await session.refresh(db_complaint)

    return db_complaint
