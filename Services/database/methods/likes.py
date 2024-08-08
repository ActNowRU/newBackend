from sqlalchemy.ext.asyncio import AsyncSession

from services.database.models.story_likes import Like
from services.database.models.user import User
from services.database.schemas.likes import LikeCreateSchema


async def create_like(session: AsyncSession, like: LikeCreateSchema, token: str):
    current_user = User.get_current_user_by_token(token)
    owner_id = current_user["id"]
    db_like = Like(**like.dict(), owner_id=owner_id)
    session.add(db_like)

    await session.commit()
    await session.refresh(db_like)

    return db_like
