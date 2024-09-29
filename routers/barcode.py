from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound

from services.database.schemas.code import CodeSchema, CodeCreateSchema

from services.database.models.code import CodeType
from services.database.models.user import User

from services.database.methods.user import get_user
from services.database.methods.goal import get_goal_by_id
from services.database.methods.organization import get_organization
from services.database.methods.code import create_code, get_code, blacklist_code

from database_initializer import get_db

from barcode import Code128
from barcode.writer import SVGWriter

import random

from datetime import datetime
from io import BytesIO
from base64 import b64encode

router = APIRouter()


@router.post(
    "/goal/{goal_id}",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Generate new barcode for goal",
    description="Create new user barcode for goal in database. Should be authorized",
)
async def create_goal_barcode(
    goal_id: int,
    session: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
):
    payload = User.get_current_user_by_token(credentials.credentials)

    value = f"T:1-N:{goal_id}-U:{payload['id']}-{random.randint(100000, 999999)}"
    barcode = Code128(value, writer=SVGWriter())

    # Write to a file-like object:
    buffer = BytesIO()
    barcode.write(buffer)

    svg_content = buffer.getvalue()

    code = CodeCreateSchema(
        goal_id=goal_id,
        owner_id=payload["id"],
        value=value,
        code_type=CodeType.barcode,
        content=svg_content,
    )
    await create_code(session, code=code)

    encoded = b64encode(svg_content).decode("utf-8")

    return {"detail": "Barcode created", "barcode": encoded, "value": value}


@router.post(
    "/organization/{organization_id}",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Generate new barcode for organization",
    description="Create new user barcode for organization in database. Should be authorized",
)
async def create_organization_barcode(
    organization_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    session: AsyncSession = Depends(get_db),
):
    payload = User.get_current_user_by_token(credentials.credentials)

    value = (
        f"T:2-N:{organization_id}-U:{payload['id']}-{random.randint(100000, 999999)}"
    )
    barcode = Code128(value, writer=SVGWriter())

    # Write to a file-like object:
    buffer = BytesIO()
    barcode.write(buffer)

    svg_content = buffer.getvalue()

    code = CodeCreateSchema(
        organization_id=organization_id,
        owner_id=payload["id"],
        value=value,
        code_type=CodeType.barcode,
        content=svg_content,
    )
    await create_code(session, code=code)

    encoded = b64encode(svg_content).decode("utf-8")

    return {"detail": "Barcode created", "barcode": encoded, "value": value}


@router.get(
    "/verify/{value}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Verify code",
    description="Verify code in database, then blacklist it instantly. "
    "Once endpoint is called, code will be not usable. Should be authorized as organization member",
)
async def verify_code(
    value: str,
    session: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
):
    payload = User.get_current_user_by_token(credentials.credentials)

    try:
        user = await get_user(session, user_id=payload["id"])
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="You are not authorized"
        )

    try:

        assert user.organization_id, "You are not an organization member"

        code = await get_code(session, value=value)

        assert code.expiration > datetime.now(), "Code expired"
        assert code.is_valid, "Code expired"

        organization = await get_organization(
            session, organization_id=user.organization_id
        )

        if code.organization_id != organization.id:
            code_goal = await get_goal_by_id(session, goal_id=code.goal_id)

            assert (
                code_goal.owner_id == organization.id
            ), "Code belongs to other organization or goal"

        code_schema = CodeSchema.model_validate(code)

        await blacklist_code(session, code_id=value)

    except AssertionError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Код не найден"
        )
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        )

    return {
        "detail": "Code verified and blacklisted to prevent reuse",
        "code": code_schema,
    }
