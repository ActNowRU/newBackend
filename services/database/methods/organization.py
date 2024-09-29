from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.database.methods.user import create_user
from services.database.models.organization import Organization, Place
from services.database.models.user import Role
from services.database.schemas.organization import OrganizationCreateSchema
from services.database.schemas.user import UserCreateSchema


async def create_organization(
    session: AsyncSession, organization: OrganizationCreateSchema, photo: bytes
) -> Organization:
    user = organization.dict()

    user.pop("name")

    organization = organization.dict()
    organization.pop("password")

    db_org = Organization(**organization, photo=photo)
    session.add(db_org)

    await session.commit()
    await session.refresh(db_org)

    user["username"] = f"admin{db_org.id}"

    db_user = await create_user(
        session=session,
        user=UserCreateSchema.model_validate(user),
        role=Role.org_admin,
    )

    db_user.organization_id = db_org.id

    await session.commit()
    await session.refresh(db_user)

    return db_org, db_user


async def get_organization(
    session: AsyncSession,
    organization_id: int | None = None,
) -> Organization:
    if organization_id:
        db_user_result = await session.execute(
            select(Organization).filter(Organization.id == organization_id)
        )
    else:
        return None

    db_user = db_user_result.scalars().one()

    return db_user


async def update_organization(
    session: AsyncSession, organization: Organization, schema: dict
) -> Organization:
    for key, value in schema.items():
        if value is None:
            continue
        setattr(organization, key, value)

    await session.commit()
    await session.refresh(organization)

    return organization


async def set_place(session: AsyncSession, organization_id: int, place: dict) -> Place:
    place["organization_id"] = organization_id

    db_place_result = await session.execute(
        select(Place)
        .filter(Place.organization_id == organization_id)
        .filter(Place.location == place["location"])
    )

    if db_place := db_place_result.scalars().all():
        return db_place

    # This is a temporary solution because for now we use only one address which is legal address by default.
    organization = await get_organization(
        session=session, organization_id=organization_id
    )
    place["address"] = organization.legal_address

    db_place = Place(**place)
    session.add(db_place)

    await session.commit()
    await session.refresh(db_place)

    return db_place


async def get_all_places(session: AsyncSession):
    places_result = await session.execute(
        select(Place).filter(Place.organization_id.isnot(None))
    )

    return places_result.scalars().all()


async def get_places_by_query(
    session: AsyncSession,
    search_query: str,
    org_type: str,
    has_goals: bool,
    has_discount: bool,
):
    to_filter = select(Organization)

    if org_type:
        to_filter = to_filter.filter(Organization.type == org_type)
    if search_query:
        to_filter = to_filter.filter(Organization.name.ilike(f"%{search_query}%"))
    if has_goals:
        to_filter = to_filter.filter(Organization.goals.isnot(None))
    if has_discount:
        to_filter = to_filter.filter(Organization.common_discount.isnot(None))
    else:
        return []

    orgs_result = await session.execute(to_filter)

    orgs = orgs_result.scalars().all()

    if orgs:
        orgs_ids = [org.id for org in orgs]

        places_result = await session.execute(
            select(Place).filter(Place.organization_id.in_(orgs_ids))
        )

        return places_result.scalars().all()

    return []
