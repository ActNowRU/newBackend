from typing import Dict
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from Models import user as user_model
from Schemas.user import UserSchema, UserCreateSchema
from Services.database import user as user_db_services
from database_initializer import get_db
from Services.database.auth import generate_token, validate_password, hash_password
from Services.database.redis import logout_user

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


@router.post("/signup", response_model=UserSchema)
def signup(
        payload: UserCreateSchema = Body(),
        session: Session = Depends(get_db)
):
    try:
        payload.hashed_password = hash_password(payload.hashed_password)
        return user_db_services.create_user(session, user=payload)
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=400,
                            detail="Ошибка при создании пользователя, возможно, такой пользователь уже существует")

#  Работает


@router.post('/login', response_model=Dict)
def login(
        payload: OAuth2PasswordRequestForm = Depends(),
        session: Session = Depends(get_db)
):
    try:
        user: user_model.User = user_db_services.get_user(
            session=session, user_name=payload.username
        )
    except:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверные учетные данные пользователя"
        )

    is_validated: bool = validate_password(user, payload.password)
    if not is_validated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверные учетные данные пользователя"
        )
    return generate_token(user)


@router.post('/logout')
def logout(token: str = Depends(oauth2_scheme)):
    try :
        logout_user(token)
        return {"detail": "Вы успешно вышли из системы"}
    except:
        HTTPException(status_code=404, detail="Ошибка сервера")
