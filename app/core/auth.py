from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import HTTPException, status

from settings import SECRET_KEY, ACCESS_TOKEN_EXPIRE_TIME, REFRESH_TOKEN_EXPIRE_TIME


def hash_password(password: str) -> bytes:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())


def validate_password(hashed_password: bytes, password: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed_password)


def generate_token(obj, token_type: str, token_expire_time: int) -> str:
    token = jwt.encode(
        {
            "id": obj.id,
            "role": obj.role.value,
            "type": token_type,
            "exp": datetime.now(tz=timezone.utc) + timedelta(seconds=token_expire_time),
        },
        SECRET_KEY,
        algorithm="HS256",
    )

    return token


def generate_access_token(obj: object) -> str:
    return generate_token(
        obj, token_type="access", token_expire_time=ACCESS_TOKEN_EXPIRE_TIME
    )


def generate_refresh_token(obj: object) -> str:
    return generate_token(
        obj, token_type="refresh", token_expire_time=REFRESH_TOKEN_EXPIRE_TIME
    )


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except (jwt.DecodeError, jwt.InvalidTokenError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
        )
    except:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unable to parse token"
        )
