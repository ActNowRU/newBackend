from typing import Dict
from base64 import b64encode
import logging

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database_initializer import get_db
from app.core.auth import (
    send_email,
    generate_access_token,
    generate_refresh_token,
    decode_token,
    validate_password,
)
from app.database.models.user import User, Role
from app.database.redis import save_token_on_user_logout, check_token_status
from app.database.schemas.user import UserSchema, UserCreateSchema, UserLoginSchema

from app.utils.auth import get_current_user


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
    photo: UploadFile = File(None),
    session: AsyncSession = Depends(get_db),
):
    try:
        if photo:
            content = await photo.read()
            encoded_photo = b64encode(content)
        else:
            encoded_photo = None

        if user := await User.get_by_id_or_login(session=session, login=payload.email):
            if user.is_email_confirmed:
                raise ValueError
            else:
                await user.delete(session=session)

        user = await User.create(
            session=session,
            user_schema=payload,
            photo=encoded_photo,
            role=Role.consumer,
        )

        return UserSchema.model_validate(user)
    except ValueError:
        await session.rollback()
        await session.flush()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Error while creating user. Perhaps, user already exists",
        )

@router.get(
    "/email-verification",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Send email activation code",
    description="Send activation code to the email.",
)
async def email_get_code(email: str, session: AsyncSession = Depends(get_db)):
    user = await User.get_by_id_or_login(session=session, login=email)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User doesn't exist",
        )

    code = await user.set_last_code(session=session)

    text = f'''<h1>Ваш код подтверждения на <b>Goals</b></h1>
    {code}
Если вы не запрашивали код подтверждения, игнорируйте это сообщение.
'''
    try:
        send_email("Подтверждение регистрации на Goals", text, email)
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong",
        )

    return {"detail": "Email activation code sent"}

@router.post(
    "/email-verification",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Check email activation code.",
    description="Check email activation code.",
)
async def email_post_code(email: str, code: str, session: AsyncSession = Depends(get_db)):
    user = await User.get_by_id_or_login(session=session, login=email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User doesn't exist",
        )

    if user.last_code == code and code != "":
        user.is_email_confirmed = True
        await session.commit()

        return {"detail": "Email is activated"}

    raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect activation code",
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
    user = await User.get_by_id_or_login(session=session, login=payload.login)

    try:
        assert user
        logging.info("The user exists")
        assert user.is_email_confirmed
        logging.info("Email is confirmed")
        assert validate_password(user.hashed_password, payload.password)
    except AssertionError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Login or password is incorrect",
        )

    return {
        "access_token": generate_access_token(user),
        "refresh_token": generate_refresh_token(user),
    }


@router.get(
    "/exists",
    response_model=Dict,
    status_code=status.HTTP_200_OK,
    summary="Check if user exists",
    description="Check if user with specified email or username exists",
)
async def exists(login: str, session: AsyncSession = Depends(get_db)):
    user = await User.get_by_id_or_login(session=session, login=login)

    try:
        assert user
        return {"exists": True}
    except AssertionError:
        return {"exists": False}


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

    user = await User.get_by_id_or_login(session=session, user_id=payload["id"])

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

    if payload["type"] != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type"
        )

    try:
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
    description="Get current user. Should be authorized",
)
async def get_current_authorized_user(user: User = Depends(get_current_user)):
    return UserSchema.model_validate(user)


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
