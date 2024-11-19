from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.exc import NoResultFound

from app.core.auth import hash_password
from app.database.models.user import User
from app.database.schemas.user import UserCreateSchema


async def create_user(
    session: AsyncSession,
    user: UserCreateSchema,
    role: str,
    photo: bytes = None,
) -> User:
    if isinstance(user, UserCreateSchema):
        user = user.model_dump()

    user["role"] = role

    hashed_password = hash_password(user["password"])
    user.pop("password")

    db_user = User(**user, photo=photo, hashed_password=hashed_password)
    session.add(db_user)

    await session.commit()
    await session.refresh(db_user)

    return db_user


async def get_user(
    session: AsyncSession,
    user_id: int | None = None,
    username: str | None = None,
    login: str | None = None,
) -> User:
    if user_id:
        db_user_result = await session.execute(select(User).filter(User.id == user_id))
    elif username:
        db_user_result = await session.execute(
            select(User).filter(User.username == username)
        )
    elif login:
        db_user_result = await session.execute(
            select(User).filter(User.username == login)
        )

        try:
            return db_user_result.scalars().one()
        except NoResultFound:
            db_user_result = await session.execute(
                select(User).filter(User.email == login)
            )
    else:
        return None

    try:
        db_user = db_user_result.scalars().one()
    except NoResultFound:
        return None

    return db_user


async def update_user(session: AsyncSession, user: User, schema: dict) -> User:
    for key, value in schema.items():
        if value is None:
            continue
        if key == "password":
            key = "hashed_password"
            value = hash_password(value)
        setattr(user, key, value)

    await session.commit()
    await session.refresh(user)

    return user
