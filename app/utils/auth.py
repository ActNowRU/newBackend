from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import HTTPException, Depends, status

from app.database_initializer import get_db
from app.models.user import User, Role
from app.services.auth.jwt import decode_token


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    session: AsyncSession = Depends(get_db),
):
    payload = decode_token(credentials.credentials)

    if payload["type"] != "access":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token type",
        )

    user = await User.get_by_id_or_login(session=session, user_id=payload["id"])

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден в базе данных",
        )

    return user


async def verify_organization_admin(user: User):
    try:
        assert user.role == Role.org_admin
        assert user.organization_id
    except AssertionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не имеете доступа к данному ресурсу, "
            "так как вы не являетесь администратором организации",
        )


async def is_user_service_admin(user: User):
    try:
        assert user.role == Role.admin

        return True
    except AssertionError:
        return False
