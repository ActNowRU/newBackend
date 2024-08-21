import jwt
from fastapi import HTTPException
from sqlalchemy import Column, Integer, String, LargeBinary, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

import settings
from database_initializer import Base


class AdminProfile(Base):
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, index=True)
    hashed_password = Column(LargeBinary, nullable=False)

    @staticmethod
    def get_current_admin_by_token(token: str):
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )

    @staticmethod
    async def get_user(session: AsyncSession, username: str):
        result = await session.execute(
            select(AdminProfile).filter(AdminProfile.username == username)
        )

        return result.scalars().one()
