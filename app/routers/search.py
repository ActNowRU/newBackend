import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database_initializer import get_db

from app.database.models.organization import OrganizationType, Place

from app.database.schemas.organization import SummaryPlaceSchema


router = APIRouter()


@router.get(
    "/places/{search_query}",
    response_model=list[SummaryPlaceSchema],
    status_code=status.HTTP_201_CREATED,
    summary="Search places [TESTING]",
    description="Search places by organization name or type. This is nearly untested, can response unexpected results.",
)
async def search_places(
    search_query: str | None = None,
    organization_type: OrganizationType | None = None,
    has_goals: bool | None = None,
    has_discount: bool | None = None,
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

        print(places[0].__dict__)

        return [SummaryPlaceSchema.model_validate(place) for place in places]

    except Exception as e:
        logging.error(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось найти места",
        )
