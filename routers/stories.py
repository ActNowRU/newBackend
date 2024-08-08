from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.exc import NoResultFound

from database_initializer import get_db
from services.database.methods.story import (
    get_story_by_id,
    create_story,
    get_all_user_stories,
    change_story,
)
from services.database.methods.user import get_user
from services.database.models.story import Story
from services.database.models.story_likes import Like
from services.database.models.user import User
from services.database.redis import check_token_status
from services.database.schemas.story import StoryCreateSchema, StoryChangeSchema

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


@router.post("/stories", response_model=StoryCreateSchema)
async def create_story_endpoint(
        story: StoryCreateSchema,
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db),
):
    if await check_token_status(token):
        try:
            await create_story(session=db, story=story, token=token)
            return {"История создана"}
        except:
            HTTPException(status_code=403, detail="Данные ведены не верно")
    else:
        raise HTTPException(status_code=401, detail="Токен устарел")


@router.get("/get_stories", response_model=List[StoryCreateSchema])
async def get_all_stories(db: AsyncSession = Depends(get_db)):
    try:
        all_stories_result = await db.execute(select(Story))
        return all_stories_result.scalars().all()
    except:
        HTTPException(status_code=404, detail="Историй нет")


@router.get("/stories/{story_id}", response_model=StoryCreateSchema)
async def read_story(story_id: int, db: AsyncSession = Depends(get_db)):
    try:
        story = get_story_by_id(db, story_id=story_id)
        if story is None:
            raise HTTPException(status_code=404, detail="История не найдена")
        return story
    except NoResultFound:
        raise HTTPException(status_code=404, detail="История не найдена")


@router.get("/stories_by_username/{username}", response_model=List[StoryCreateSchema])
async def read_user_stories(username: str, db: AsyncSession = Depends(get_db)):
    user = await get_user(db, user_name=username)

    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    try:
        stories = get_all_user_stories(db, owner_id=user.id)
        return stories
    except NoResultFound:
        raise HTTPException(status_code=404, detail="История не найдена")


@router.delete("/delete/{story_id}")
async def delete_story(
        story_id: int,
        db: AsyncSession = Depends(get_db),
        token: str = Depends(oauth2_scheme),
):
    if await check_token_status(token):
        story = await get_story_by_id(db, story_id=story_id)
        user = User.get_current_user_by_token(token)
        user_id = user["id"]

        if story.owner_id != user_id:
            raise HTTPException(
                status_code=403, detail="У вас нет прав на удаление этого поста"
            )

        if story is None:
            raise HTTPException(status_code=404, detail="История не найдена")

        await db.delete(story)
        await db.commit()

        return {"message": "История успешно удалена"}
    else:
        raise HTTPException(status_code=401, detail="Токен устарел")


@router.patch("/stories_change/{story_id}")
async def update_story(
        story_id: int,
        storyscheme: StoryChangeSchema,
        db: AsyncSession = Depends(get_db),
        token: str = Depends(oauth2_scheme),
):
    if await check_token_status(token):
        story = await get_story_by_id(db, story_id=story_id)
        user = User.get_current_user_by_token(token)
        user_id = user["id"]
        if story.owner_id != user_id:
            raise HTTPException(
                status_code=403, detail="У вас нет прав на изменение этой истории"
            )
        if story is None:
            raise HTTPException(status_code=404, detail="История не найдена")
        await change_story(story_id=story_id, session=db, story=storyscheme)
        return {"message": "История изменена"}
    else:
        raise HTTPException(status_code=401, detail="Токен устарел")


@router.post("/like_story/{story_id}")
async def create_and_delete_like(
        story_id: int,
        db: AsyncSession = Depends(get_db),
        token: str = Depends(oauth2_scheme),
):
    if await check_token_status(token):
        story_result = await db.execute(select(Story).filter(Story.id == story_id))
        story = story_result.scalars().first()
        current_user = User.get_current_user_by_token(token)
        if not story:
            raise HTTPException(status_code=404, detail="Story not found")
        like_result = await db.execute(
            select(Like).filter(
                Like.owner_id == current_user["id"], Like.story_id == story_id
            )
        )
        like = like_result.scalars().first()
        if like:
            await db.delete(like)
            await db.commit()
            return {"message": "Like deleted successfully"}
        elif not like:
            new_like = Like(owner_id=current_user["id"], story_id=story_id)
            db.add(new_like)
            await db.commit()
            return {"message": "Like added successfully"}
    else:
        raise HTTPException(status_code=401, detail="Токен устарел")


@router.get("/likes_count/{story_id}")
async def get_likes_count(story_id: int, db: AsyncSession = Depends(get_db)):
    story_result = await db.execute(select(Story).filter(Story.id == story_id))
    story = story_result.scalars().first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    likes_result = await db.execute(select(Like).filter(Like.story_id == story_id))
    likes_count = likes_result.scalars().all().count()
    return {"likes_count": likes_count}


@router.get("/story_likes_user/{user_name}")
async def get_user_story_likes(username: str, db: AsyncSession = Depends(get_db)):
    user = await get_user(db, user_name=username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    likes_result = await db.execute(select(Like).filter(Like.owner_id == user.id))
    likes = likes_result.scalars().all()
    if not user:
        raise HTTPException(status_code=404, detail="Likes not found")
    return {"user_story_likes": likes}
