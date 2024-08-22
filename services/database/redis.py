from redis_initializer import get_redis
from settings import REFRESH_TOKEN_EXPIRE_TIME, REDIS_LOGOUT_VALUE


async def save_token_on_user_logout(token: str) -> None:
    redis = await get_redis()
    await redis.setex(
        name=token, time=REFRESH_TOKEN_EXPIRE_TIME, value=REDIS_LOGOUT_VALUE
    )


async def check_token_status(token: str) -> bool:
    redis = await get_redis()

    token_status = await redis.get(token)

    if not token_status:
        return True
    if token_status == REDIS_LOGOUT_VALUE:
        return False

    return True