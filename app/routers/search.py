import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database_initializer import get_db

from app.models.organization import OrganizationType, Place
from .organization import get_location
from app.schemas.organization import SummaryPlaceSchema


router = APIRouter()


@router.get(
    "/places",
    response_model=List[SummaryPlaceSchema],
    status_code=status.HTTP_200_OK,
    summary="Search places",
    description="Search places by organization name or type.",
)
async def search_places(
    search_query: str = None,
    organization_type: OrganizationType = None,
    has_goals: bool = None,
    has_discount: bool = None,
    session: AsyncSession = Depends(get_db),
):
    try:
        places = await Place.get_by_query(
            session=session,
            search_query=search_query,
            org_type=organization_type,
            has_goals=has_goals,
            has_discount=has_discount,
        )

        return [
            SummaryPlaceSchema.model_validate(
                {**place.__dict__, "location": await get_location(place.address)}
            )
            for place in places
        ]

    except Exception as e:
        logging.error(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось найти места",
        )
