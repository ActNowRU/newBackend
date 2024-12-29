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
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.auth import get_current_user
from app.database_initializer import get_db
from app.core.auth import validate_password
from app.database.models.user import User
from app.database.schemas.user import (
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
    description="Get user profile by username. Shows only public information.",
)
async def profile(
    username: str,
    session: AsyncSession = Depends(get_db),
):
    if user := await User.get_by_id_or_login(session=session, login=username):
        return UserSchemaPublic.model_validate(user)
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден"
        )


@router.get(
    "/photo/{username}",
    response_model=dict,
    summary="Get user photo",
    description="Get user profile picture by username in base64",
)
async def profile_photo(
    username: str = Path(...),
    session: AsyncSession = Depends(get_db),
):
    if user := await User.get_by_id_or_login(session=session, login=username):
        return {"photo": user.photo}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден"
        )


@router.patch(
    "/update",
    response_model=UserSchema,
    summary="Update user info",
    description="Update user text info about their profile. Should be authorized",
)
async def update_user_info(
    payload: UserChangeSchema = Depends(),
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        user = await user.update(session=session, updates=payload.model_dump())
        return UserSchema.model_validate(user)
    except Exception as e:
        logging.error("Failed to update user: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось изменить данные пользователя",
        )


@router.patch(
    "/update/photo",
    response_model=dict,
    summary="Update user photo",
    description="Update user profile photo. Should be authorized",
)
async def update_user_photo(
    photo: UploadFile = File(...),
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        content = await photo.read()
        encoded_photo = b64encode(content)

        await user.update(session=session, updates={"photo": encoded_photo})
        return {"detail": "Фото успешно обновлено"}
    except Exception as e:
        logging.error("Failed to update user: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось изменить данные пользователя",
        )


@router.patch(
    "/update/password/",
    response_model=UserSchema,
    summary="Update user password",
    description="Update user password. Should be authorized to prevent unsafe password changes",
)
async def update_user_password(
    payload: UserChangePasswordSchema = Depends(),
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not validate_password(user.hashed_password, payload.old_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный пароль"
        )

    try:
        user = await user.update(
            session=session, updates={"password": payload.new_password}
        )
        return UserSchema.model_validate(user)
    except Exception as e:
        logging.error("Failed to update password: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось изменить пароль пользователя",
        )
