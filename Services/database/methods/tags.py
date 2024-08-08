from sqlalchemy.ext.asyncio import AsyncSession

from services.database.models.tags import Tags
from services.database.schemas.tags import TagBase


async def create_tag(tag: TagBase, session: AsyncSession):
    db_tag = Tags(**tag.dict())
    session.add(db_tag)

    await session.commit()
    await session.refresh(db_tag)

    return db_tag
