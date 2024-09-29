import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from database_initializer import get_db

from services.database.methods.user import get_user
from services.database.methods.organization import get_places_by_query
from services.database.models.organization import OrganizationType
from services.database.models.user import User

from services.database.schemas.organization import PlaceSchema


router = APIRouter()


@router.get(
    "/places/{search_query}",
    response_model=list[PlaceSchema],
    status_code=status.HTTP_201_CREATED,
    summary="Search places",
    description="Search places by organization name or type. Should be authorized",
)
async def search_places(
    search_query: str | None = None,
    organization_type: OrganizationType | None = None,
    has_goals: bool | None = None,
    has_discount: bool | None = None,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    session: AsyncSession = Depends(get_db),
):
    current_user = User.get_current_user_by_token(credentials.credentials)

    try:
        user = await get_user(session=session, user_id=current_user["id"])

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден"
            )

        places = get_places_by_query(
            session=session,
            search_query=search_query,
            org_type=organization_type,
            has_goals=has_goals,
            has_discount=has_discount,
        )

        return places

    except Exception as e:
        logging.error(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось найти места",
        )
