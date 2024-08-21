from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from database_initializer import get_db
from services.database.methods.goal import create_goal, get_goal_by_id, change_goal
from services.database.methods.story import get_all_goal_story
from services.database.models.goal import Goal
from services.database.models.user import User
from services.database.redis import check_token_status
from services.database.schemas.goal import GoalBase

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


# не работает
@router.post("/create", response_model=GoalBase)
async def create_goal_endpoint(
        goal: GoalBase,
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db),
):
    if await check_token_status(token):
        try:
            await create_goal(session=db, goal=goal, token=token)
            return {"goal created"}
        except:
            raise HTTPException(status_code=403, detail="Данные введены не верно")
    else:
        raise HTTPException(status_code=401, detail="Токен устарел")


@router.get("/get/{goal_id}", response_model=GoalBase)
async def get_goal(goal_id: int, db: AsyncSession = Depends(get_db)):
    try:
        goal = await get_goal_by_id(db, goal_id=goal_id)
        return goal
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Голс не найден")


@router.get("/get_all", response_model=List[GoalBase])
async def get_all_goals(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(Goal))
        return result.scalars().all()
    except:
        HTTPException(status_code=404, detail="Голсы не найдены")


@router.delete("/delete/{goal_id}")
async def delete_goal(
        goal_id: int,
        db: AsyncSession = Depends(get_db),
        token: str = Depends(oauth2_scheme),
):
    if await check_token_status(token):
        goal = await get_goal_by_id(db, goal_id=goal_id)
        user = User.get_current_user_by_token(token)
        user_id = user["id"]
        if goal.owner_id != user_id:
            raise HTTPException(
                status_code=403, detail="У вас нет прав на удаление этого голса"
            )
        if goal is None:
            raise HTTPException(status_code=404, detail="Голс не найден")
        stories = await get_all_goal_story(db, goal_id=goal_id)
        for story in stories:
            await db.delete(story)
        await db.delete(goal)
        await db.commit()
        return {"message": "Пост  и истории к нему успешно удалены "}
    else:
        raise HTTPException(status_code=401, detail="Токен устарел")


@router.patch("/update/{goal_id}")
async def update_post(
        goal_id: int,
        payload: GoalBase,
        db: AsyncSession = Depends(get_db),
        token: str = Depends(oauth2_scheme),
):
    if await check_token_status(token):
        post = await get_goal_by_id(session=db, goal_id=goal_id)
        user = User.get_current_user_by_token(token)
        user_id = user["id"]
        if post.owner_id != user_id:
            raise HTTPException(
                status_code=403, detail="У вас нет прав на изменение этого голса"
            )
        if post is None:
            raise HTTPException(status_code=404, detail="Пост не найден")
        await change_goal(session=db, goal_id=goal_id, goal=payload)
        return {"message": "Голс изменен"}
    else:
        raise HTTPException(status_code=401, detail="Токен устарел")
