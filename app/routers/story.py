import logging
from typing import List
from base64 import b64encode

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.exc import NoResultFound

from app.database_initializer import get_db
from app.database.methods.story import (
    get_story_by_id,
    create_story,
    get_all_user_stories,
    change_story,
    get_favorite_stories,
)
from app.database.methods.user import get_user
from app.database.models.story import Story
from app.database.models.user import User
from app.database.schemas.story import (
    StoryCreateSchema,
    StoryChangeSchema,
    StorySchema,
)


router = APIRouter()


@router.post(
    "/",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Create new story",
    description="Create new story in database. Should be authorized",
)
async def create_new_story(
    story: StoryCreateSchema = Depends(),
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

    if (story.organization_id and story.goal_id) or (
        not story.organization_id and not story.goal_id
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя создать историю без указания организации или голса, а также с указанием сразу обоих",
        )

    if len(content) > 3 or not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя загружать менее одного или более 3 медиа-файлов",
        )

    try:
        encoded_content = (
            [
                b64encode(await content_item.read()).decode("utf-8")
                for content_item in content
            ]
            if content
            else None
        )
        await create_story(
            session=session,
            story=story,
            content=encoded_content,
            owner_id=current_user["id"],
        )
        return {"detail": "История успешно создана"}
    except Exception as error:
        logging.error(error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось создать историю",
        )


@router.get(
    "/{story_id}",
    response_model=StorySchema,
    summary="Get story by id",
    description="Get story by id. Should be authorized",
)
async def get_story(
    story_id: int,
    session: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
):
    current_user = User.get_current_user_by_token(credentials.credentials)

    user = await get_user(session=session, user_id=current_user["id"])

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден"
        )

    try:
        story = await get_story_by_id(session, story_id=story_id)
        assert story is not None
        return story
    except (NoResultFound, AssertionError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="История не найдена"
        )


@router.get(
    "/organization/{organization_id}",
    response_model=List[StorySchema],
    summary="Get all organization stories",
    description="Get all stories in organization. Should be authorized",
)
async def get_all_stories(
    organization_id: int,
    session: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
):
    current_user = User.get_current_user_by_token(credentials.credentials)

    user = await get_user(session=session, user_id=current_user["id"])

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден"
        )

    try:
        all_stories_result = await session.execute(
            select(Story).filter(Story.goal.owner_id == organization_id)
        )
        stories = all_stories_result.scalars().all()
        return [StorySchema.model_validate(story) for story in stories]
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="У организации нет историй",
        )


@router.get(
    "/by/user/{username}",
    response_model=List[StorySchema],
    summary="Get user stories",
    description="Get story by user. Should be authorized",
)
async def get_user_stories(
    username: str,
    session: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
):
    User.get_current_user_by_token(credentials.credentials)

    try:
        user = await get_user(session, username=username)

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден"
            )

        stories = await get_all_user_stories(session, owner_id=user.id)
        return stories
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Истории не найдены"
        )


@router.get(
    "/by/me",
    response_model=List[StorySchema],
    summary="Get current user stories",
    description="Get story by current user. Should be authorized",
)
async def get_current_user_stories(
    session: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
):
    current_user = User.get_current_user_by_token(credentials.credentials)

    user = await get_user(session, user_id=current_user["id"])

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден"
        )

    try:
        stories = await get_all_user_stories(session, owner_id=current_user["id"])
        return stories
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Истории не найдены"
        )


@router.delete(
    "/{story_id}",
    summary="Delete story",
    description="Delete story. Should be authorized",
)
async def delete_story(
    story_id: int,
    session: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
):
    story = await get_story_by_id(session, story_id=story_id)

    if story is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="История не найдена"
        )

    current_user = User.get_current_user_by_token(credentials.credentials)

    user = await get_user(session, user_id=current_user["id"])

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден"
        )

    if story.owner_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет прав на удаление этого поста",
        )

    await session.delete(story)
    await session.commit()

    return {"detail": "История успешно удалена"}


@router.patch(
    "/change/{story_id}",
    summary="Update story info",
    description="Update story. Should be authorized",
)
async def update_story(
    story_id: int,
    payload: StoryChangeSchema = Depends(),
    content: List[UploadFile] = File(None),
    session: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
):
    story = await get_story_by_id(session, story_id=story_id)

    if story is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="История не найдена"
        )

    current_user = User.get_current_user_by_token(credentials.credentials)

    user = await get_user(session, user_id=current_user["id"])

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден"
        )

    if story.owner_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет прав на изменение этой истории",
        )

    if len(content) > 3 or not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя загружать менее одного или более 3 медиа-файлов",
        )

    encoded_content = (
        [
            b64encode(await content_item.read()).decode("utf-8")
            for content_item in content
        ]
        if content
        else None
    )

    await change_story(
        story_id=story_id, session=session, story=payload, content=encoded_content
    )

    return {"detail": "История изменена"}


@router.patch(
    "/change/{story_id}/position/{position}",
    summary="Update story info",
    description="Set story position in the favorite list in organization. "
    "Up to 6. Should be authorized as organization member",
)
async def update_story_position(
    story_id: int,
    position: int,
    session: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
):
    story = await get_story_by_id(session, story_id=story_id)

    if story is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="История не найдена"
        )

    current_user = User.get_current_user_by_token(credentials.credentials)

    user = await get_user(session, user_id=current_user["id"])

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден"
        )

    if story.organization_id != user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет прав на изменение позиции этой истории в витрине отзывов",
        )

    await change_story(
        story_id=story_id, session=session, story={"position": position}, content=None
    )

    return {"detail": "Позиция истории изменена"}


@router.get(
    "/favorite/{organization_id}",
    summary="Get favorite stories [TESTING]",
    description="Get favorite stories. Should be authorized. This is on testing, please use /story/organization/{organization_id} instead, to get all organization stories and filter them.",
)
async def get_favorite_stories_by_organization(
    organization_id: int,
    session: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
):
    current_user = User.get_current_user_by_token(credentials.credentials)

    user = await get_user(session, user_id=current_user["id"])

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден"
        )

    stories = await get_favorite_stories(session, organization_id=organization_id)

    return stories
