from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.database.models.user import User
from services.database.schemas.user import UserCreateSchema, UserChangeSchema

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def create_user(session: AsyncSession, user: UserCreateSchema):
    db_user = User(**user.dict())
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user


async def get_user(session: AsyncSession, user_name: str):
    db_user_result = await session.execute(
        select(User).filter(User.user_name == user_name)
    )
    db_user = db_user_result.scalars().one()

    return db_user


async def update_user(session: AsyncSession, username: str, user: UserChangeSchema):
    db_user_result = await session.execute(
        select(User).filter(User.user_name == username)
    )
    db_user = db_user_result.scalars().one()

    for key, value in user.dict().items():
        setattr(db_user, key, value)

    await session.commit()
    await session.refresh(db_user)

    return db_user
