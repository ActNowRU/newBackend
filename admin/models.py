import jwt
from fastapi import HTTPException
from sqlalchemy import Column, Integer, String, LargeBinary
from sqlalchemy.orm import Session
from starlette import status

import settings
from database_initializer import Base


class Admin_user(Base):
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, index=True)
    hashed_password = Column(LargeBinary, nullable=False)

    def get_current_amin_by_token(token: str):
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

    def get_user(session: Session, user_name: str):
        return session.query(Admin_user).filter(Admin_user.email == email).one()