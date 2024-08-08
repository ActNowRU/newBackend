from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from database_initializer import get_db
from services.database.methods import user as user_db_services
from services.database.models.user import User
from services.database.redis import check_token_status
from services.database.schemas.user import UserSchema, UserChangeSchema

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


@router.get("/profile/{username}", response_model=UserSchema)
async def profile(username: str, session: AsyncSession = Depends(get_db)):
    try:
        user = await user_db_services.get_user(session=session, user_name=username)
        return user
    except NoResultFound:
        HTTPException(status_code=403, detail="Пользователь не найден")


@router.patch("/update/{username}")
async def update_user(
        username: str,
        userscheme: UserChangeSchema,
        db: AsyncSession = Depends(get_db),
        token: str = Depends(oauth2_scheme),
):
    if await check_token_status(token):
        user = await user_db_services.get_user(db, user_name=username)

        current_user = User.get_current_user_by_token(token)
        current_user_id = current_user["id"]

        if user.id != current_user_id:
            raise HTTPException(
                status_code=403,
                detail="Вы не имеете прав на изменение этого пользователя",
            )
        if user is None:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        try:
            await user_db_services.update_user(
                session=db, username=username, user=userscheme
            )
            return {"Данные пользователя изменены"}
        except:
            HTTPException(
                status_code=404, detail="Не удалось изменить данные пользователя"
            )
    else:
        raise HTTPException(status_code=401, detail="Токен устарел")
