import logging
from typing import List
from base64 import b64encode

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound, IntegrityError

from app.database_initializer import get_db
from app.models.story import Story
from app.types.enums import ModerationState
from app.models.user import User
from app.models.discount import Discount
from app.schemas.story import (
    StoryCreateSchema,
    StoryChangeSchema,
    StorySchema,
)

from app.utils.auth import get_current_user, is_user_service_admin
from app.models.code import Code


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
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if (story.organization_id and story.goal_id) or (
        not story.organization_id and not story.goal_id
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя создать историю без указания организации или голса, а также с указанием сразу обоих",
        )

    # Check if the user has a scanned code for the goal or organization

    try:
        if story.goal_id:
            code = await Code.get_by_value(
                session, value=f"T:1-N:{story.goal_id}-U:{user.id}"
            )
        elif story.organization_id:
            code = await Code.get_by_value(
                session, value=f"T:2-N:{story.organization_id}-U:{user.id}"
            )
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не можете создать историю для этого голса или организации",
        )

    if code.is_valid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не можете создать историю для этого голса или организации",
        )

    if content is None or len(content) > 3:
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
        await Story.create(
            session=session,
            story=story,
            content=encoded_content,
            owner_id=user.id,
        )
        code.is_valid = True
        return {"detail": "История успешно создана"}
    except Exception as error:
        logging.error(error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось создать историю",
        )


@router.get(
    "/me",
    response_model=List[StorySchema],
    summary="Get current user stories",
    description="Get stories by current user. Should be authorized",
)
async def get_current_user_stories(
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        stories = await Story.get_all_by_owner(session, owner_id=user.id)
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Истории не найдены"
        )

    return [StorySchema.model_validate(story) for story in stories]


@router.get(
    "/{story_id}",
    response_model=StorySchema,
    summary="Get story by id",
    description="Get story by id. Should be authorized",
)
async def get_story(
    story_id: int,
    session: AsyncSession = Depends(get_db),
):
    try:
        story = await Story.get_by_id(session, story_id=story_id)
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="История не найдена"
        )

    return story


@router.get(
    "/organization/{organization_id}",
    response_model=List[StorySchema],
    summary="Get all organization stories",
    description="Get all stories in organization. Should be authorized",
)
async def get_all_organization_stories(
    organization_id: int,
    session: AsyncSession = Depends(get_db),
):
    try:
        stories = await Story.get_all_by_organization(
            session, organization_id=organization_id
        )
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="У организации нет историй",
        )

    return [StorySchema.model_validate(story) for story in stories]


@router.get(
    "/user/{username}",
    response_model=List[StorySchema],
    summary="Get user stories",
    description="Get stories by user. Should be authorized",
)
async def get_user_stories(
    username: str,
    session: AsyncSession = Depends(get_db),
):
    try:
        if user := await User.get_by_id_or_login(session, login=username):
            stories = await Story.get_all_by_owner(session, owner_id=user.id)
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден"
            )
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Истории не найдены"
        )

    return [StorySchema.model_validate(story) for story in stories]


@router.delete(
    "/{story_id}",
    summary="Delete story",
    description="Delete story. Should be authorized",
)
async def delete_story(
    story_id: int,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        story = await Story.get_by_id(session, story_id=story_id, private=True)
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="История не найдена"
        )

    if story.owner_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет прав на удаление этого поста",
        )

    await story.delete(session)

    return {"detail": "История успешно удалена"}


@router.patch(
    "/{story_id}",
    summary="Update story info",
    description="Update story. Should be authorized",
)
async def update_story(
    story_id: int,
    payload: StoryChangeSchema = Depends(),
    content: List[UploadFile] = File(None),
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        story = await Story.get_by_id(session, story_id=story_id, private=True)
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="История не найдена"
        )

    if story.owner_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет прав на изменение этой истории",
        )

    if content and len(content) > 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя загружать более 3 медиа-файлов",
        )

    encoded_content = (
        [
            b64encode(await content_item.read()).decode("utf-8")
            for content_item in content
        ]
        if content
        else None
    )

    await story.change(session=session, story=payload, content=encoded_content)

    return {"detail": "История изменена"}


@router.put(
    "/favorite",
    summary="Update story info",
    description="Set story position in the favorite list in organization. "
    "Up to 6. Should be authorized as organization member",
)
async def update_story_position(
    story_id: int,
    position: int,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        story = await Story.get_by_id(session, story_id=story_id)
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="История не найдена"
        )

    if story.organization_id != user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет прав на изменение позиции этой истории в витрине отзывов",
        )

    await story.change_position(session=session, position=position)

    return {"detail": "Позиция истории изменена"}


@router.get(
    "/favorite/{organization_id}",
    response_model=dict[int, StorySchema],
    summary="Get favorite stories [TESTING]",
    description="Get favorite stories. Should be authorized.",
)
async def get_favorite_stories_by_organization(
    organization_id: int,
    session: AsyncSession = Depends(get_db),
):
    stories = await Story.get_favorite(session, organization_id=organization_id)

    return stories


@router.get(
    "/admin/",
    response_model=dict,
    summary="Get all stories",
    description="Get all stories. Should be authorized as admin.",
)
async def get_all_stories_admin(
    moderation_state: ModerationState,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not await is_user_service_admin(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не являетесь администратором сервиса.",
        )
    try:
        stories = await Story.get_all(session, moderation_state=moderation_state)
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Истории не найдены"
        )

    return [StorySchema.model_validate(story) for story in stories]


@router.patch(
    "/admin/{story_id}",
    response_model=dict,
    summary="Change story moderation state",
    description="Get favorite stories. Should be authorized as admin.",
)
async def change_story_moderation_state_admin(
    story_id: int,
    moderation_state: ModerationState,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not await is_user_service_admin(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не являетесь администратором сервиса.",
        )
    try:
        story = await Story.get_by_id(session=session, story_id=story_id, private=True)

        organization = story.organization
        if not organization:
            organization = story.goal.organization

        if (
            organization.max_discount
            and organization.common_discount
            and organization.step_amount
        ):
            step = (
                organization.max_discount - organization.common_discount
            ) / organization.step_amount

            if (
                moderation_state == ModerationState.allowed
                and story.moderation_state
                in (
                    ModerationState.on_check,
                    ModerationState.denied,
                )
            ):
                discount = await Discount.get_by_user_and_organization(
                    session=session,
                    user_id=story.owner_id,
                    organization_id=story.organization_id,
                )

                if discount:
                    new_discount_percentage = min(
                        discount.discount_percentage + step, organization.max_discount
                    )
                    await discount.update_percentage(
                        session=session, discount_percentage=new_discount_percentage
                    )
                else:
                    await Discount.create(
                        session=session,
                        user_id=story.owner_id,
                        organization_id=organization.id,
                        discount_percentage=new_discount_percentage,
                    )
            elif (
                moderation_state != ModerationState.allowed
                and story.moderation_state == ModerationState.allowed
            ):
                discount = await Discount.get_by_user_and_organization(
                    session=session,
                    user_id=story.owner_id,
                    organization_id=organization.id,
                )

                new_discount_percentage = max(
                    discount.discount_percentage - step, organization.common_discount
                )
                await discount.update_percentage(
                    session=session, discount_percentage=new_discount_percentage
                )

        await story.change_moderation_state(
            session=session, moderation_state=moderation_state
        )
    except (IntegrityError, NoResultFound) as error:
        logging.error(error)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Perhaps, you specified wrong story ID or moderation state.",
        )
    except Exception as error:
        logging.error(error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something Went Wrong",
        )
    return {"detail": "Состояние истории изменено"}
