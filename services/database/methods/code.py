from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.database.models.code import Code
from services.database.schemas.code import CodeCreateSchema


DEFAULT_CODE_EXPIRATION = 60 * 5  # 5 minutes


async def create_code(
    session: AsyncSession,
    code: CodeCreateSchema,
):
    created_at = datetime.now()

    db_goal = Code(
        **code.dict(),
        expiration=created_at + timedelta(seconds=DEFAULT_CODE_EXPIRATION),
        created_at=created_at
    )

    session.add(db_goal)

    await session.commit()
    await session.refresh(db_goal)

    return db_goal


async def get_code(session: AsyncSession, value: int):
    db_code_result = await session.execute(select(Code).where(Code.value == value))

    return db_code_result.scalars().one()


async def blacklist_code(session: AsyncSession, code_id: int):
    db_code = await get_code(session, code_id)

    db_code.is_valid = False
    session.add(db_code)

    await session.commit()
    await session.refresh(db_code)
