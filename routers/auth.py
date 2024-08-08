from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from database_initializer import get_db
from services.core.auth import (
    generate_token,
    validate_password,
    hash_password,
)
from services.database.methods import user as user_db_services
from services.database.models import user as user_model
from services.database.redis import save_token_on_user_logout
from services.database.schemas.user import UserSchema, UserCreateSchema

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


@router.post("/signup", response_model=UserSchema)
async def signup(
        payload: UserCreateSchema = Body(), session: AsyncSession = Depends(get_db)
):
    try:
        payload.hashed_password = hash_password(payload.hashed_password)
        return await user_db_services.create_user(session, user=payload)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=400,
            detail="Error while creating user. Perhaps, user already exists",
        )


@router.post("/login", response_model=Dict)
async def login(
        payload: OAuth2PasswordRequestForm = Depends(),
        session: AsyncSession = Depends(get_db),
):
    try:
        user: user_model.User = await user_db_services.get_user(
            session=session, user_name=payload.username
        )
    except:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username or password is incorrect",
        )

    is_validated: bool = validate_password(user, payload.password)
    if not is_validated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username or password is incorrect",
        )
    return generate_token(user)


@router.post("/logout")
async def logout(token: str = Depends(oauth2_scheme)):
    try:
        await save_token_on_user_logout(token)
        return {"detail": "Вы успешно вышли из системы"}
    except:
        HTTPException(status_code=404, detail="Ошибка сервера")

# from fastapi import Request
# from services.core.vk.auth import get_vk_auth_url, gev_vk_access_token
#
#
# CLIENT_ID = "51901205"
# CLIENT_SECRET = ""
# REDIRECT_URL = "https://actnow.com"
# PROTECTED_KEY = "MT3X7owJ2WODFv7YtlZR"
#
# router = APIRouter()
#
#
# @router.get("/vk_login")
# async def vk_auth_redirect(request: Request):
#     code = request.query_params.get("code")
#     if code is None:
#         raise HTTPException(
#             status_code=400,
#             detail="Code not provided",
#         )
#     else:
#         access_token_info = await gev_vk_access_token(client_id, client_secret, redirect_url, code)
#         return access_token_info
#
#
# @router.get("/get_vk_auth_url")
# async def vk_auth_url():
#     url = await get_vk_auth_url(CLIENT_ID, REDIRECT_URL)
#     return {"url": url}
