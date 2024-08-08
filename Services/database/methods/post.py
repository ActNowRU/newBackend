from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.database.models.post import Post
from services.database.models.user import User
from services.database.schemas.post import PostBase


async def create_post(session: AsyncSession, post: PostBase, token: str):
    current_user = User.get_current_user_by_token(token)
    owner_id = current_user["id"]
    date_of_creation = datetime.now()
    db_post = Post(**post.dict(), owner_id=owner_id, date_of_creation=date_of_creation)
    session.add(db_post)

    await session.commit()
    await session.refresh(db_post)

    return db_post


async def get_post_by_id(session: AsyncSession, post_id: int):
    post_result = await session.execute(select(Post).filter(Post.id == post_id))

    return post_result.scalars().one()


async def get_all_user_posts(session: AsyncSession, owner_id: int):
    all_posts_result = await session.execute(
        select(Post).filter(Post.owner_id == owner_id)
    )

    return all_posts_result.scalars().all()


async def change_post(session: AsyncSession, post_id: int, post: PostBase):
    db_post_result = await session.execute(select(Post).filter(Post.id == post_id))
    db_post = db_post_result.scalars().one()

    for key, value in post.dict().items():
        if key != "owner_id":
            setattr(db_post, key, value)

    await session.commit()
    await session.refresh(db_post)

    return db_post
