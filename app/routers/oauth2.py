from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

import httpx

from app.services.auth.jwt import generate_access_token, generate_refresh_token
from app.models.user import User
from app.types.enums import Role
from fastapi import APIRouter, Depends
from app.database_initializer import get_db
from settings import BASE_URL, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET


GOOGLE_REDIRECT_URI = f"{BASE_URL}/oauth2/google/callback"
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"

VK_CLIENT_ID = "51901205"
VK_CLIENT_SECRET = ""
VK_REDIRECT_URL = f"{BASE_URL}/oauth2/vk/callback"

router = APIRouter()


@router.get(
    "/google",
    summary="Get Google OAuth2 Authorization URL",
    description=f'Get authorization URL for user, that redirects to the {GOOGLE_REDIRECT_URI} with query parameters. "code" query parameter should be sent to the post method of this endpoint.',
)
async def get_google_auth_url():
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }
    query_string = "&".join([f"{key}={value}" for key, value in params.items()])
    auth_url = f"{GOOGLE_AUTH_URL}?{query_string}"
    return {"auth_url": auth_url}


@router.post(
    "/google",
    summary="Login with Google Oauth2",
    description="Get JWT-token pair like in usual login, but by google authorization code.",
)
async def google_auth_callback(code: str, session: AsyncSession = Depends(get_db)):
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": GOOGLE_REDIRECT_URI,
            },
        )
        if token_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to fetch access token from Google",
            )
        token_data = token_response.json()
        google_access_token = token_data.get("access_token")

    async with httpx.AsyncClient() as client:
        response = await client.get(
            GOOGLE_TOKENINFO_URL,
            params={"id_token": google_access_token},
        )
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Google token",
            )
        google_user = response.json()

    email = google_user.get("email")

    # Check if user exists in your database
    user = await User.get_by_id_or_login(session=session, login=email)
    if not user:
        # Optionally create a new user
        user = await User.create(
            session=session,
            user_schema={"email": email, "username": email.split("@")[0]},
            role=Role.consumer,
        )

    # Generate your own tokens
    access_token = generate_access_token(user)
    refresh_token = generate_refresh_token(user)

    return {"access_token": access_token, "refresh_token": refresh_token}


@router.get("/vk", summary="Get VK OAuth2 Authorization URL")
async def vk_auth_url():
    auth_url = (
        f"https://oauth.vk.com/authorize?client_id={VK_CLIENT_ID}"
        f"&display=page&redirect_url={VK_REDIRECT_URL}&response_type=code&v=5.52"
    )
    return {"auth_url": auth_url}


@router.post("/vk", summary="Login with VK Oauth2")
async def vk_auth_callback(code: str, session: AsyncSession = Depends(get_db)):
    if code is None:
        raise HTTPException(
            status_code=400,
            detail="Code not provided",
        )
    else:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://oauth.vk.com/access_token?client_id={VK_CLIENT_ID}&client_secret={VK_CLIENT_SECRET}"
                f"&redirect_uri={VK_REDIRECT_URL}&code={code}"
            )

            access_token_info = await response.json()

        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid VK token",
            )

    email = access_token_info.get("email")

    # Check if user exists in your database
    user = await User.get_by_id_or_login(session=session, login=email)
    if not user:
        # Optionally create a new user
        user = await User.create(
            session=session,
            user_schema={"email": email, "username": email.split("@")[0]},
            role=Role.consumer,
        )

    # Generate your own tokens
    access_token = generate_access_token(user)
    refresh_token = generate_refresh_token(user)

    return {"access_token": access_token, "refresh_token": refresh_token}
