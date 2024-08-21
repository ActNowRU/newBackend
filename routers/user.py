import logging
from base64 import b64encode

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    File,
    Path,
    UploadFile,
    status,
)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from database_initializer import get_db
from services.core.auth import validate_password
from services.database.methods import user as user_db_services
from services.database.models.user import User
from services.database.schemas.user import (
    UserSchema,
    UserSchemaPublic,
    UserChangeSchema,
    UserChangePasswordSchema,
)

router = APIRouter()


@router.get(
    "/{username}",
    response_model=UserSchemaPublic,
    summary="Get user profile",
    description="Get user profile by username. Shows only public information. Should be authorized",
)
async def profile(
        username: str,
        session: AsyncSession = Depends(get_db),
        credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
):
    # Raises error if unauthorized
    User.get_current_user_by_token(credentials.credentials)

    try:
        user = await user_db_services.get_user(session=session, username=username)
        return UserSchemaPublic.model_validate(user)
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден"
        )


@router.get(
    "/photo/{username}",
    response_model=dict,
    summary="Get user photo",
    description="Get user profile picture by username in base64. Should be authorized",
)
async def profile(
        username: str = Path(...),
        session: AsyncSession = Depends(get_db),
        credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
):
    # Raises error if unauthorized
    User.get_current_user_by_token(credentials.credentials)

    try:
        user = await user_db_services.get_user(session=session, username=username)
        if user.photo is None:
            encoded_photo = None
        else:
            encoded_photo = b64encode(user.photo).decode("utf-8")
        print(encoded_photo)
        return {"photo": encoded_photo}
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден"
        )


@router.put(
    "/update",
    response_model=UserSchema,
    summary="Update user info",
    description="Update user text info about their profile. Should be authorized",
)
async def update_user_info(
        payload: UserChangeSchema = Depends(),
        session: AsyncSession = Depends(get_db),
        credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
):
    current_user = User.get_current_user_by_token(credentials.credentials)

    try:
        user = await user_db_services.get_user(
            session=session, user_id=current_user["id"]
        )
        assert user
    except:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ваш профиль не найден"
        )

    try:
        user = await user_db_services.update_user(
            session=session, user=user, schema=payload.dict()
        )
        return UserSchema.model_validate(user)
    except Exception as e:
        logging.error("Failed to update user: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось изменить данные пользователя",
        )


@router.put(
    "/update/photo",
    response_model=dict,
    summary="Update user photo",
    description="Update user profile photo. Should be authorized",
)
async def update_user_photo(
        photo: UploadFile = File(...),
        session: AsyncSession = Depends(get_db),
        credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
):
    current_user = User.get_current_user_by_token(credentials.credentials)

    try:
        user = await user_db_services.get_user(
            session=session, user_id=current_user["id"]
        )
        assert user
    except:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден"
        )
    try:
        content = await photo.read()
        await user_db_services.update_user(
            session=session, user=user, schema={"photo": content}
        )
        return {"detail": "Фото успешно обновлено"}
    except Exception as e:
        logging.error("Failed to update user: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось изменить данные пользователя",
        )


@router.put(
    "/update/password/",
    response_model=UserSchema,
    summary="Update user password",
    description="Update user password. Should be authorized to prevent unsafe password changes",
)
async def update_user_password(
        payload: UserChangePasswordSchema = Depends(),
        session: AsyncSession = Depends(get_db),
        credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
):
    current_user = User.get_current_user_by_token(credentials.credentials)

    try:
        user = await user_db_services.get_user(
            session=session, user_id=current_user["id"]
        )
        assert user
    except:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден"
        )

    if not validate_password(user.hashed_password, payload.old_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный пароль"
        )

    try:
        user = await user_db_services.update_user(
            session=session, user=user, schema={"password": payload.new_password}
        )
        return UserSchema.model_validate(user)
    except Exception as e:
        logging.error("Failed to update password: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось изменить пароль пользователя",
        )
