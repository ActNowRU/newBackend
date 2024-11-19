import logging
from base64 import b64encode
from typing import List

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi_cache.decorator import cache

from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.database_initializer import get_db
from app.database.methods.organization import (
    create_organization,
    get_organization,
    update_organization,
    set_place,
    get_all_places,
    get_place_by_id,
)
from app.database.methods.user import get_user
from app.database.models.user import User, Role
from app.database.models.organization import OrganizationType
from app.database.schemas.organization import (
    OrganizationSchema,
    OrganizationCreateSchema,
    OrganizationChangeSchema,
    SetPlaceLocationSchema,
    SummaryPlaceSchema,
    VerbosePlaceSchema,
)
from app.database.schemas.user import (
    UserSchemaPublic,
)

from app.utils.geocoder import YandexGeocoder
from settings import YANDEX_API_KEY

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
    description="Get current organization info by access token. Should be authorized as organization member",
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
    description="Get organization info by id. Shows only public information. Should be authorized",
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
    description="Get organization picture by id in base64. Should be authorized.",
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


@router.patch(
    "/update",
    response_model=OrganizationSchema,
    summary="Update organization info",
    description="Update organization text info about their profile. Should be authorized as organization member",
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
            session=session, organization=organization, schema=payload.model_dump()
        )
        return OrganizationSchema.model_validate(organization)
    except Exception as e:
        logging.error("Failed to update user: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось изменить данные организации",
        )


@router.patch(
    "/update/photo",
    response_model=dict,
    summary="Update organization photo",
    description="Update organization profile photo. Should be authorized as organization member",
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


@router.put(
    "/places/",
    response_model=dict,
    summary="Set place",
    description="Set location of place in organization. Should be authorized as organization member",
)
async def set_organization_place(
    place: SetPlaceLocationSchema = Depends(),
    session: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
):
    current_user = User.get_current_user_by_token(credentials.credentials)

    try:
        assert current_user["role"] == Role.org_admin.value
    except AssertionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You have no access to this resource. "
            "You are not an organization admin",
        )

    user = await get_user(session=session, user_id=current_user["id"])

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден"
        )

    try:
        await set_place(
            session=session,
            organization_id=user.organization_id,
            place=place.model_dump(),
        )
        return {"detail": "Место успешно обновлено"}
    except Exception as e:
        logging.error("Failed to update user: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось изменить данные о месте организации",
        )


counter = 0


@cache()
async def get_location(address: str):
    global counter

    geocoder = YandexGeocoder.with_client(api_key=YANDEX_API_KEY)

    data = await geocoder.address_to_geopoint(address)
    counter += 1

    return {"lon": data[0], "lat": data[1]}


@router.get(
    "/places/",
    response_model=List[SummaryPlaceSchema],
    summary="Get all places",
    description="Get all places in all organizations.",
)
async def get_all_available_places(
    session: AsyncSession = Depends(get_db),
):
    places = await get_all_places(session=session)

    formatted_places = [
        SummaryPlaceSchema(
            id=place.id,
            organization_id=place.organization_id,
            name=place.name,
            address=place.address,
            location=await get_location(place.address),
        )
        for place in places
    ]

    return formatted_places


@router.get(
    "/places/{place_id}",
    response_model=VerbosePlaceSchema,
    summary="Get place by id",
    description="Get place by id with its organization data.",
)
async def get_place(
    place_id: int,
    session: AsyncSession = Depends(get_db),
):
    place = await get_place_by_id(session=session, place_id=place_id)

    formatted_place = VerbosePlaceSchema(
        id=place.id,
        organization=place.organization,
        name=place.name,
        address=place.address,
        location=await get_location(place.address),
    )

    return formatted_place


@router.get(
    "/places/tests/caching_geopoint",
    summary="Get counter of geocoding requests",
    description="Get in-memory counter of geocoding requests.",
)
async def test_caching_geopoint():
    return {"counter": counter}


@router.get(
    "/types/available",
    response_model=List[str],
    summary="Get available organization types",
    description="Get list of available organization types.",
)
async def get_available_organization_types():
    return [_type.value for _type in OrganizationType]
