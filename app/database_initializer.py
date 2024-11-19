from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

import settings

engine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URL,
    echo=True,
    future=True,
    connect_args={"check_same_thread": False},
)

SessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    bind=engine,
)

Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    db: AsyncSession = SessionLocal()
    try:
        yield db
    finally:
        await db.close()


async def init_models(clean=False) -> None:
    async with engine.begin() as conn:
        if clean:
            await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
