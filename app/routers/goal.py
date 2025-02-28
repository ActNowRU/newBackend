from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.database_initializer import get_db

from app.database.models.goal import Goal
from app.database.models.user import User
from app.database.schemas.goal import GoalCreateSchema, GoalSchema

from app.utils.auth import get_current_user, is_user_organization_admin

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
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    if not await is_user_organization_admin(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не имеете доступа к данному ресурсу, "
            "так как вы не являетесь администратором организации",
        )

    try:
        assert content, "Необходимо загрузить фотографию"
        assert len(content) == 1, "Нельзя загрузить более одной фотографии"

        if goal.from_date or goal.to_date or goal.dates:
            if goal.dates:
                assert not (
                    goal.from_date or goal.to_date
                ), "Необходимо указывать только дату от и до или только выборку дат"
            else:
                assert goal.from_date and goal.to_date, (
                    "Должна быть указана и дата от, и дата до, "
                    "либо выборка дат, либо оставить поля пустыми"
                )

        if goal.from_time or goal.to_time:
            assert (
                goal.from_time and goal.to_time
            ), "Должно быть указано и время от, и время до, либо не указано"
    except AssertionError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )

    encoded_content = (
        [
            b64encode(await content_item.read()).decode("utf-8")
            for content_item in content
        ]
        if content
        else None
    )

    await Goal.create(
        session=session,
        goal=goal,
        content=encoded_content,
        owner_id=user.organization_id,
    )

    return {"detail": "Голс успешно создан"}


@router.get(
    "/{goal_id}",
    response_model=GoalSchema,
    summary="Get goal by id",
    description="Get goal by id.",
)
async def get_goal(
    goal_id: int,
    session: AsyncSession = Depends(get_db),
):
    try:
        goal = await Goal.get_by_id(session, goal_id=goal_id)
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Голс не найден"
        )

    return GoalSchema.model_validate(goal)


@router.delete(
    "/{goal_id}",
    summary="Delete goal",
    description="Delete goal and all related stories. Should be authorized as organization member",
)
async def delete_goal(
    goal_id: int,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        goal = await Goal.get_by_id(session, goal_id=goal_id)
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Голс не найден"
        )

    if goal.owner_id != user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет прав на удаление этого голса",
        )

    await goal.delete(session=session)

    return {"detail": "Пост и истории к нему успешно удалены"}


@router.get(
    "/",
    response_model=List[GoalSchema],
    summary="Get all goals",
    description="Get all goals.",
)
async def get_all_goals(
    session: AsyncSession = Depends(get_db),
):
    try:
        goals = await Goal.get_all(session=session)
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ни один голс не существует"
        )

    return [GoalSchema.model_validate(goal) for goal in goals]


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
    user: User = Depends(get_current_user),
):
    try:
        goal = await Goal.get_by_id(session=session, goal_id=goal_id)
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Голс не найден"
        )

    if goal.owner_id != user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет прав на изменение этого голса",
        )

    try:
        assert content, "Необходимо загрузить фотографию"
        assert len(content) == 1, "Нельзя загрузить более одной фотографии"
    except AssertionError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )

    encoded_content = (
        [
            b64encode(await content_item.read()).decode("utf-8")
            for content_item in content
        ]
        if content
        else None
    )

    await goal.change(session=session, goal=payload, content=encoded_content)

    return {"detail": "Голс успешно изменен"}
