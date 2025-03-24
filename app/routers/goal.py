from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Form, File, UploadFile
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.database_initializer import get_db

from app.models.goal import Goal
from app.models.user import User
from app.schemas.goal import GoalCreateSchema, GoalSchema

from app.utils.auth import get_current_user, verify_organization_admin

from base64 import b64encode


router = APIRouter()


def validate_datetime(dates, from_date, to_date, from_time, to_time):
    try:
        if dates:
            assert not (from_date or to_date), (
                "Необходимо указывать только дату от и до или только выборку дат"
            )
        else:
            assert not (from_date or to_date) or (from_date and to_date), (
                "Должна быть указана и дата от, и дата до, "
                "либо выборка дат, либо оставить поля пустыми"
            )

        assert not (from_time or to_time) or (from_time and to_time), (
            "Должно быть указано и время от, и время до, либо не указано"
        )
    except AssertionError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )


@router.post(
    "/",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Create new goal",
    description="Create new goal in database. Should be authorized as organization member. ",
)
async def create_new_goal(
    title: str = Form(...),
    description: str = Form(...),
    address: str = Form(...),
    cost: int = Form(...),
    prize_info: str = Form(None),
    prize_conditions: List[str] = Form(None),
    from_time: str = Form(None),
    to_time: str = Form(None),
    from_date: str = Form(None),
    to_date: str = Form(None),
    dates: List[str] = Form(None),
    content: UploadFile = File(...),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    await verify_organization_admin(user)

    validate_datetime(dates, from_date, to_date, from_time, to_time)

    encoded_content = (
        b64encode(await content.read()).decode("utf-8") if content else None
    )

    goal = GoalCreateSchema(
        title=title,
        description=description,
        address=address,
        cost=cost,
        prize_info=prize_info,
        prize_conditions=prize_conditions,
        from_time=from_time,
        to_time=to_time,
        from_date=from_date,
        to_date=to_date,
        dates=dates,
    )

    await Goal.create(
        session=session,
        goal=goal,
        content=encoded_content,
        owner_id=user.organization_id,
    )

    return {"detail": "Голс успешно создан"}


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


@router.patch(
    "/{goal_id}",
    summary="Update goal info",
    description="Update goal. Should be authorized as organization member",
)
async def update_post(
    goal_id: int,
    title: str = Form(None),
    description: str = Form(None),
    address: str = Form(None),
    cost: int = Form(None),
    prize_info: str = Form(None),
    prize_conditions: List[str] = Form(None),
    from_time: str = Form(None),
    to_time: str = Form(None),
    from_date: str = Form(None),
    to_date: str = Form(None),
    dates: List[str] = Form(None),
    content: UploadFile = File(None),
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await verify_organization_admin(user)

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

    validate_datetime(dates, from_date, to_date, from_time, to_time)

    encoded_content = (
        b64encode(await content.read()).decode("utf-8") if content else None
    )

    goal_data = GoalCreateSchema(
        title=title,
        description=description,
        address=address,
        cost=cost,
        prize_info=prize_info,
        prize_conditions=prize_conditions,
        from_time=from_time,
        to_time=to_time,
        from_date=from_date,
        to_date=to_date,
        dates=dates,
    )

    await goal.change(session=session, goal=goal_data, content=encoded_content)

    return {"detail": "Голс успешно изменен"}


@router.delete(
    "/{goal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete goal",
    description="Delete goal and all related stories. Should be authorized as organization member",
)
async def delete_goal(
    goal_id: int,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await verify_organization_admin(user)

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
