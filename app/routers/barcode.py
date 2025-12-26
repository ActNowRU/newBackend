from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound

from app.schemas.code import CodeSchema, CodeCreateSchema
from app.models.code import CodeType, Code
from app.models.goal import Goal
from app.models.user import User
from app.models.organization import Organization

from app.utils.auth import get_current_user, verify_organization_admin

from app.database_initializer import get_db

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
    user: User = Depends(get_current_user),
):
    value = f"T:1-N:{goal_id}-U:{user.id}-{random.randint(100000, 999999)}"
    barcode = Code128(value, writer=SVGWriter())

    # Write to a file-like object:
    buffer = BytesIO()
    barcode.write(buffer)

    svg_content = buffer.getvalue()

    code = CodeCreateSchema(
        goal_id=goal_id,
        owner_id=user.id,
        value=value,
        code_type=CodeType.barcode,
        content=svg_content,
    )
    await Code.create(session, code=code)

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
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    value = f"T:2-N:{organization_id}-U:{user.id}-{random.randint(100000, 999999)}"
    barcode = Code128(value, writer=SVGWriter())

    # Write to a file-like object:
    buffer = BytesIO()
    barcode.write(buffer)

    svg_content = buffer.getvalue()

    code = CodeCreateSchema(
        organization_id=organization_id,
        owner_id=user.id,
        value=value,
        code_type=CodeType.barcode,
        content=svg_content,
    )
    await Code.create(session, code=code)

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
    user: User = Depends(get_current_user),
):
    await verify_organization_admin(user)

    try:
        code = await Code.get_by_value(session, value=value)

        assert code.expiration > datetime.now(), "Code expired"
        assert code.is_valid, "Code expired"

        organization = await Organization.get_by_id(
            session, organization_id=user.organization_id
        )

        if code.organization_id != organization.id:
            code_goal = await Goal.get_by_id(session, goal_id=code.goal_id)

            assert code_goal.owner_id == organization.id, (
                "Code belongs to other organization or goal"
            )

        code_schema = CodeSchema.model_validate(code)

        await code.blacklist(session)

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
