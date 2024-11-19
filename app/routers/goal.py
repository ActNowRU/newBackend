import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.database_initializer import get_db

from app.database.methods.goal import create_goal, get_goal_by_id, change_goal
from app.database.methods.story import get_all_goal_story
from app.database.methods.user import get_user

from app.database.models.goal import Goal
from app.database.models.user import User, Role

from app.database.schemas.goal import GoalCreateSchema, GoalSchema

from base64 import b64encode

router = APIRouter()


@router.post(
    "/",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Create new goal [TESTING]",
    description="Create new goal in database. Should be authorized as organization member. "
    "This is on testing, it doesn't properly retrieve and parse some date fields, try to combine them or not to send them at all",
)
async def create_new_goal(
    goal: GoalCreateSchema = Depends(),
    content: List[UploadFile] = File(None),
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    session: AsyncSession = Depends(get_db),
):
    current_user = User.get_current_user_by_token(credentials.credentials)

    user = await get_user(session=session, user_id=current_user["id"])

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден"
        )

    try:
        assert current_user["role"] == Role.org_admin.value

        assert content, "Необходимо загрузить фотографию"
        assert len(content) == 1, "Нельзя загрузить более одной фотографии"

        assert ((goal.from_date and goal.to_date) or goal.dates) or not any(
            [goal.from_date, goal.to_date, goal.dates]
        ), (
            "Должна быть указана и дата от, и дата до, "
            "либо выборка дат, либо оставить поля пустыми"
        )

        assert ((goal.from_date or goal.to_date) and not goal.dates) or not any(
            [goal.from_date, goal.to_date, goal.dates]
        ), "Необходимо указывать только дату от и до или только выборку дат"

        assert (
            goal.from_time and goal.to_time
        ), "Должно быть указано и время от, и время до, либо не указано"

        encoded_content = (
            [
                b64encode(await content_item.read()).decode("utf-8")
                for content_item in content
            ]
            if content
            else None
        )

        await create_goal(
            session=session,
            goal=goal,
            content=encoded_content,
            owner_id=user.organization_id,
        )

        return {"detail": "Голс успешно создан"}
    except AssertionError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )
    except Exception as e:
        logging.error(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось создать голс",
        )


@router.get(
    "/{goal_id}",
    response_model=GoalSchema,
    summary="Get goal by id",
    description="Get goal by id. Should be authorized",
)
async def get_goal(
    goal_id: int,
    session: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
):
    User.get_current_user_by_token(credentials.credentials)

    try:
        goal = await get_goal_by_id(session, goal_id=goal_id)
        return GoalSchema.model_validate(goal)
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Голс не найден"
        )


@router.delete(
    "/{goal_id}",
    summary="Delete goal",
    description="Delete goal and all related stories. Should be authorized as organization member",
)
async def delete_goal(
    goal_id: int,
    session: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
):
    try:
        goal = await get_goal_by_id(session, goal_id=goal_id)
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Голс не найден"
        )

    current_user = User.get_current_user_by_token(credentials.credentials)

    user = await get_user(session, user_id=current_user["id"])

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден"
        )

    if goal.owner_id != user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет прав на удаление этого голса",
        )

    stories = await get_all_goal_story(session, goal_id=goal_id)

    for story in stories:
        await session.delete(story)

    await session.delete(goal)
    await session.commit()

    return {"detail": "Пост и истории к нему успешно удалены"}


@router.get(
    "/",
    response_model=List[GoalSchema],
    summary="Get all goals",
    description="Get all goals. Should be authorized",
)
async def get_all_goals(
    session: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
):
    User.get_current_user_by_token(credentials.credentials)

    try:
        result = await session.execute(select(Goal))
        goals = result.scalars().all()

        return [GoalSchema.model_validate(goal) for goal in goals]
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ни один голс не существует"
        )


@router.patch(
    "/change/{goal_id}",
    summary="Update goal info",
    description="Update goal. Should be authorized as organization member",
)
async def update_post(
    goal_id: int,
    payload: GoalCreateSchema = Depends(),
    content: List[UploadFile] = File(None),
    session: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
):
    try:
        goal = await get_goal_by_id(session=session, goal_id=goal_id)
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Голс не найден"
        )

    current_user = User.get_current_user_by_token(credentials.credentials)

    user = await get_user(session=session, user_id=current_user["id"])

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден"
        )

    if goal.owner_id != user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет прав на изменение этого голса",
        )

    if not content:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Необходимо загрузить фотографию",
        )

    if len(content) != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нельзя загрузить более одной фотографии",
        )

    encoded_content = (
        [
            b64encode(await content_item.read()).decode("utf-8")
            for content_item in content
        ]
        if content
        else None
    )

    await change_goal(
        session=session, goal_id=goal_id, goal=payload, content=encoded_content
    )

    return {"detail": "Голс успешно изменен"}
