import logging
from base64 import b64encode
from typing import List

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    File,
    UploadFile,
    status,
)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from database_initializer import get_db
from services.database.methods.organization import (
    create_organization,
    get_organization,
    update_organization,
    set_place,
    get_all_places,
)
from services.database.methods.user import get_user
from services.database.models.user import User, Role
from services.database.models.organization import OrganizationType
from services.database.schemas.organization import (
    OrganizationSchema,
    OrganizationCreateSchema,
    OrganizationChangeSchema,
    SetPlaceLocationSchema,
    PlaceSchema,
)
from services.database.schemas.user import (
    UserSchemaPublic,
)

router = APIRouter()


class OrganizationCreatedResponseSchema(BaseModel):
    admin: UserSchemaPublic
    organization: OrganizationSchema


@router.post(
    "/register",
    response_model=OrganizationCreatedResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Register new organization",
    description="Create new organization in database",
)
async def register(
    payload: OrganizationCreateSchema = Depends(),
    photo: UploadFile = File(None),
    session: AsyncSession = Depends(get_db),
):
    try:
        if photo:
            content = await photo.read()
            encoded_photo = b64encode(content)
        else:
            encoded_photo = None

        organization, admin = await create_organization(
            session=session,
            organization=payload,
            photo=encoded_photo,
        )

        return OrganizationCreatedResponseSchema(
            admin=UserSchemaPublic.model_validate(admin),
            organization=OrganizationSchema.model_validate(organization),
        )
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Error while creating user. Perhaps, user already exists",
        )
    except Exception as e:
        logging.error("Failed to create organization: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create organization",
        )


@router.get(
    "/us",
    response_model=OrganizationSchema,
    status_code=status.HTTP_200_OK,
    summary="Get current organization info",
    description="Get current organization info by access token",
)
async def get_current_organization(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    session: AsyncSession = Depends(get_db),
):
    user = User.get_current_user_by_token(credentials.credentials)

    try:
        assert user["role"] == Role.org_admin.value

        user = await get_user(session=session, user_id=user["id"])
        organization = await get_organization(
            session=session, organization_id=user.organization_id
        )

        assert user.organization_id

        return OrganizationSchema.model_validate(organization)
    except AssertionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You have no access to this resource. "
            "You are not an organization admin",
        )
    except Exception as e:
        logging.error("Failed to get user: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Couldn't get user",
        )


@router.get(
    "/{organization_id}",
    response_model=OrganizationSchema,
    summary="Get organization info",
    description="Get organization info by username. Shows only public information. Should be authorized",
)
async def info(
    organization_id: int,
    session: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
):
    # Raises error if unauthorized
    User.get_current_user_by_token(credentials.credentials)

    try:
        organization = await get_organization(
            session=session, organization_id=organization_id
        )
        return OrganizationSchema.model_validate(organization)
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Организация не найдена"
        )


@router.get(
    "/photo/{organization_id}",
    response_model=dict,
    summary="Get organization photo",
    description="Get user profile picture by username in base64. Should be authorized",
)
async def organization_photo(
    organization_id: str,
    session: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
):
    # Raises error if unauthorized
    User.get_current_user_by_token(credentials.credentials)

    try:
        organization = await get_organization(
            session=session, organization_id=organization_id
        )

        return {"photo": organization.photo}
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Организация не найдена"
        )


@router.put(
    "/update",
    response_model=OrganizationSchema,
    summary="Update organization info",
    description="Update organization text info about their profile. Should be authorized",
)
async def update_organization_info(
    payload: OrganizationChangeSchema = Depends(),
    session: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
):
    current_user = User.get_current_user_by_token(credentials.credentials)

    try:
        assert current_user["role"] == Role.org_admin.value
        user = await get_user(session=session, user_id=current_user["id"])
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ваш профиль не найден"
        )

    try:
        organization = await get_organization(
            session=session, organization_id=user.organization_id
        )
        organization = await update_organization(
            session=session, organization=organization, schema=payload.dict()
        )
        return OrganizationSchema.model_validate(organization)
    except Exception as e:
        logging.error("Failed to update user: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось изменить данные организации",
        )


@router.put(
    "/update/photo",
    response_model=dict,
    summary="Update organization photo",
    description="Update organization profile photo. Should be authorized",
)
async def update_organization_photo(
    photo: UploadFile = File(...),
    session: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
):
    current_user = User.get_current_user_by_token(credentials.credentials)

    try:
        assert current_user["role"] == Role.org_admin.value
        user = await get_user(session=session, user_id=current_user["id"])
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден"
        )
    try:
        content = await photo.read()
        encoded_photo = b64encode(content)

        organization = await get_organization(
            session=session, organization_id=user.organization_id
        )
        await update_organization(
            session, organization=organization, schema={"photo": encoded_photo}
        )
        return {"detail": "Фото организации успешно обновлено"}
    except Exception as e:
        logging.error("Failed to update user: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось изменить данные организации",
        )


@router.post(
    "/places/set_place",
    response_model=dict,
    summary="Set place",
    description="Set location of place in organization. Should be authorized",
)
async def set_organization_place(
    place: SetPlaceLocationSchema = Depends(),
    session: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
):
    current_user = User.get_current_user_by_token(credentials.credentials)

    try:
        assert current_user["role"] == Role.org_admin.value
        user = await get_user(session=session, user_id=current_user["id"])
    except AssertionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You have no access to this resource. "
            "You are not an organization admin",
        )
    except:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден"
        )

    try:
        await set_place(
            session=session,
            organization_id=user.organization_id,
            place={"location": {"lat": place.lat, "lon": place.lon}},
        )
        return {"detail": "Место успешно обновлено"}
    except Exception as e:
        logging.error("Failed to update user: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось изменить данные о месте организации",
        )


@router.get(
    "/places/get_all_places",
    response_model=List[PlaceSchema],
    summary="Get all places",
    description="Get all places in all organizations. Should be authorized",
)
async def get_all_available_places(
    session: AsyncSession = Depends(get_db),
    # credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
):
    # current_user = User.get_current_user_by_token(credentials.credentials)
    #
    # try:
    #     assert await get_user(session=session, user_id=current_user["id"])
    # except AssertionError:
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND, detail="Вы не авторизованы"
    #     )

    places = await get_all_places(session=session)
    formatted_places = (
        [PlaceSchema.model_validate(place) for place in places] if places else []
    )

    return formatted_places


@router.get(
    "/types/available",
    response_model=List[str],
    summary="Get available organization types",
    description="Get list of available organization types. Should be authorized",
)
async def get_available_organization_types(
    # session: AsyncSession = Depends(get_db),
    # credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
):
    # current_user = User.get_current_user_by_token(credentials.credentials)
    #
    # try:
    #     assert await get_user(session=session, user_id=current_user["id"])
    # except AssertionError:
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND, detail="Вы не авторизованы"
    #     )

    return [_type.value for _type in OrganizationType]
