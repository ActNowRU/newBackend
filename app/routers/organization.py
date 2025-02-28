import logging
from base64 import b64encode
from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, status
from fastapi_cache.decorator import cache

from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.database_initializer import get_db
from app.database.models.user import User
from app.database.models.organization import Organization, OrganizationType, Place
from app.database.models.discount import Discount
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

from app.utils.auth import get_current_user, is_user_organization_admin
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

        organization, admin = await Organization.create(
            session=session,
            organization_schema=payload,
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
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    if not await is_user_organization_admin(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не являетесь администратором организации",
        )

    try:
        organization = await Organization.get_by_id(
            session=session, organization_id=user.organization_id
        )
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Организация не найдена"
        )

    return OrganizationSchema.model_validate(organization)


@router.get(
    "/{organization_id}",
    response_model=OrganizationSchema,
    summary="Get organization info",
    description="Get organization info by id. Shows only public information",
)
async def info(
    organization_id: int,
    session: AsyncSession = Depends(get_db),
):
    try:
        organization = await Organization.get_by_id(
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
    description="Get organization picture by id in base64",
)
async def organization_photo(
    organization_id: str,
    session: AsyncSession = Depends(get_db),
):
    try:
        organization = await Organization.get_by_id(
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
    user: User = Depends(get_current_user),
):
    if not await is_user_organization_admin(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не имеете доступа к данному ресурсу, "
            "так как вы не являетесь администратором организации",
        )

    try:
        organization = await Organization.get_by_id(
            session=session, organization_id=user.organization_id
        )

        organization = await organization.update(
            session=session, organization=user.organization, schema=payload.model_dump()
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
    user: User = Depends(get_current_user),
):
    if not await is_user_organization_admin(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не имеете доступа к данному ресурсу, "
            "так как вы не являетесь администратором организации",
        )

    try:
        content = await photo.read()
        encoded_photo = b64encode(content)

        organization = await Organization.get_by_id(
            session=session, organization_id=user.organization_id
        )
        await organization.update(
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
    user: User = Depends(get_current_user),
):
    if not await is_user_organization_admin(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не имеете доступа к данному ресурсу, "
            "так как вы не являетесь администратором организации",
        )

    try:
        await Place.set(
            session=session,
            organization_id=user.organization_id,
            place=place.model_dump(),
        )
        return {"detail": "Место успешно обновлено"}
    except Exception as e:
        logging.error("Failed to update place: %s", e)
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
    places = await Place.get_all(session=session)

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
    place = await Place.get_by_id(session=session, place_id=place_id)

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


@router.get(
    "/discount/{organization_id}",
    response_model=dict,
    summary="Get individual discount of authorized user in specific organization",
    description="Get individual discount of authorized user in specific organization. If timestamp indicates that more time has passed than days_to_step_back, then step back the discount by one step.",
)
async def get_individual_discount(
    organization_id: int,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        discount = await Discount.get_by_user_and_organization(
            session=session,
            user_id=user.id,
            organization_id=organization_id
        )
        if not discount:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Скидка не найдена"
            )

        organization = await Organization.get_by_id(
            session=session, organization_id=organization_id
        )

        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Организация не найдена"
            )

        time_since_update = datetime.now() - discount.updated_at
        if time_since_update > timedelta(days=organization.days_to_step_back):
            step = (organization.max_discount - organization.common_discount) / organization.step_amount
            new_discount_percentage = max(discount.discount_percentage - step, organization.common_discount)
            await discount.update_percentage(session=session, discount_percentage=new_discount_percentage)

        return {"discount_percentage": discount.discount_percentage}
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Скидка не найдена"
        )
    except Exception as e:
        logging.error("Failed to get discount: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось получить скидку",
        )
