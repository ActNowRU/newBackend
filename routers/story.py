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
    user = await get_user(db, username=username)

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
