from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from database_initializer import get_db
from services.core.auth import (
    generate_access_token,
    generate_refresh_token,
    decode_token,
    validate_password,
)
from services.database.methods.user import create_user, get_user
from services.database.models.user import User, Role
from services.database.redis import save_token_on_user_logout, check_token_status
from services.database.schemas.user import UserSchema, UserCreateSchema, UserLoginSchema

router = APIRouter()


@router.post(
    "/signup",
    response_model=UserSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create new user",
    description="Create new user in database",
)
async def signup(
        payload: UserCreateSchema = Depends(),
        session: AsyncSession = Depends(get_db),
):
    try:
        user = await create_user(session, user=payload, role=Role.consumer)
        return UserSchema.model_validate(user)
    except IntegrityError:
        await session.rollback()
        await session.flush()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Error while creating user. Perhaps, user already exists",
        )


class TokenPairSchema(BaseModel):
    access_token: str
    refresh_token: str


class RefreshedAccessTokenSchema(BaseModel):
    access_token: str


@router.post(
    "/login",
    response_model=TokenPairSchema,
    status_code=status.HTTP_200_OK,
    summary="Authenticate user",
    description="Authenticate user and obtain JWT pair of access and refresh tokens",
)
async def login(
        payload: UserLoginSchema = Depends(),
        session: AsyncSession = Depends(get_db),
):
    try:
        user = await get_user(session=session, login=payload.login)
        assert validate_password(user.hashed_password, payload.password)
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Login or password is incorrect",
        )

    return {
        "access_token": generate_access_token(user),
        "refresh_token": generate_refresh_token(user),
    }


@router.post(
    "/refresh",
    response_model=RefreshedAccessTokenSchema,
    status_code=status.HTTP_200_OK,
    summary="Refresh JWT-token",
    description="Refresh and obtain new pair of refresh and access tokens, old ones will be blacklisted",
)
async def refresh(
        credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
        session: AsyncSession = Depends(get_db),
):
    payload = decode_token(token=credentials.credentials)

    if payload["type"] != "refresh":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token type"
        )

    if not await check_token_status(credentials.credentials):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token blacklisted due to logout. Please log in again",
        )

    user = await get_user(session=session, username=payload["username"])

    return {"access_token": generate_access_token(user)}


@router.post(
    "/logout",
    response_model=Dict,
    status_code=status.HTTP_200_OK,
    summary="Logout user",
    description="Add token to blacklist so that it can't be used for further requests anymore",
)
async def logout(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    payload = decode_token(token=credentials.credentials)

    try:
        if payload["type"] != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type"
            )

        await save_token_on_user_logout(credentials.credentials)
        return {"detail": "Вы успешно вышли из системы"}
    except:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Couldn't blacklist token",
        )


@router.get(
    "/me",
    response_model=UserSchema,
    status_code=status.HTTP_200_OK,
    summary="Get current user",
    description="Get current user by access token",
)
async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
        session: AsyncSession = Depends(get_db),
):
    user = User.get_current_user_by_token(credentials.credentials)

    try:
        user = await get_user(session=session, user_id=user["id"])

        assert user

        return UserSchema.model_validate(user)
    except:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Couldn't get user",
        )


# from fastapi import Request
# from services.core.vk.auth import get_vk_auth_url, get_vk_access_token
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