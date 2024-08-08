from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database_initializer import get_db
from services.database.methods.complaint import (
    create_post_complaint,
    create_user_complaint,
    create_story_complaint,
)
from services.database.models.post import Post
from services.database.models.story import Story
from services.database.models.user import User
from services.database.schemas.complaints import (
    ComplaintsCreate,
    ComplaintsPostSchema,
    ComplaintsStorySchema,
    ComplaintsUserSchema,
)

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


@router.post("/post/{post_id}", response_model=ComplaintsPostSchema)
async def create_complaint_post(
        complaint: ComplaintsPostSchema,
        post_id: int,
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db),
):
    post_result = await db.execute(select(Post).filter(Post.id == post_id))
    post = post_result.scalars().first()
    if not post:
        raise HTTPException(status_code=403, detail="Пост не найден")
    else:
        return create_post_complaint(
            session=db, complaint=complaint, post_id=post_id
        ), {"message": "Жалоба отправлена"}


@router.post("/story/{story_id}", response_model=ComplaintsCreate)
async def create_complaint_story(
        complaint: ComplaintsStorySchema,
        story_id: int,
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db),
):
    story_result = await db.execute(select(Story).filter(Story.id == story_id))
    story = story_result.scalars().first()
    if not story:
        raise HTTPException(status_code=403, detail="История не найдена")
    else:
        return create_story_complaint(
            complaint=complaint, story_id=story_id, session=db
        ), {"message": "Жалоба " "отправлена"}


@router.post("/user/{user_id}", response_model=ComplaintsUserSchema)
async def create_complaint_user(
        complaint: ComplaintsUserSchema,
        user_id: int,
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db),
):
    user_result = await db.execute(select(User).filter(User.id == user_id))
    user = user_result.scalars().first()

    if not user:
        raise HTTPException(status_code=403, detail="Пользователь не найден")
    else:
        return create_user_complaint(
            session=db, complaint=complaint, user_id=user_id
        ), {"message": "Жалоба " "отправлена"}
