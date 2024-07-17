from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from Schemas.user import UserSchema,UserChangeSchema
from Services.database.redis import verify_token_in_redis
from Services.database.user import get_user
from database_initializer import get_db
from Services.database import user as user_db_services
from Models import user as user_model



router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


#  Работает


#  Работает
@router.get("/profile/{username}", response_model=UserSchema)
def profile(username: str,
            session: Session = Depends(get_db)):
    try:
        user = user_db_services.get_user(session=session, user_name=username)
        return user
    except NoResultFound:
        HTTPException(status_code=403, detail="Пользователь не найден")


@router.patch("/update/{username}")
def update_user(username: str,
                userscheme: UserChangeSchema,
                db: Session = Depends(get_db),
                token: str = Depends(oauth2_scheme)):
    if verify_token_in_redis(token):
        user = get_user(db, user_name=username)
        current_user = user_model.User.get_current_user_by_token(token)
        current_user_id = current_user["id"]
        if user.id != current_user_id:
            raise HTTPException(status_code=403, detail="Вы не имеете прав на изменение этого пользователя")
        if user is None:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        try:
            user_db_services.change_user(session=db, username=username, user=userscheme)
            return {"Данные пользователя изменены"}
        except:
            HTTPException(status_code=404, detail="Не удалось изменить данные пользователя")
    else:
        raise HTTPException(status_code=401, detail="Токен устарел")


