"""
Háztartási felhasználó-adminisztráció HTTP-végpontjai.
"""

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_current_user,
    require_household_admin,
)
from app.core.database import get_db_session
from app.models import HouseholdMember, User
from app.schemas import (
    HouseholdUserCreateRequest,
    HouseholdUserResponse,
    HouseholdUserUpdateRequest,
)
from app.services import (
    HouseholdUserRecord,
    create_household_user,
    list_household_users,
    update_household_user,
)


router = APIRouter(
    prefix="/admin/households",
    tags=["admin-users"],
)


def _build_response(
    record: HouseholdUserRecord,
) -> HouseholdUserResponse:
    return HouseholdUserResponse(
        user_id=record.user_id,
        email=record.email,
        display_name=record.display_name,
        user_is_active=record.user_is_active,
        membership_id=record.membership_id,
        role=record.role,
        membership_is_active=(
            record.membership_is_active
        ),
        joined_at=record.joined_at,
    )


@router.get(
    "/{household_id}/users",
    response_model=list[HouseholdUserResponse],
)
def get_household_users(
    household_id: int,
    membership: HouseholdMember = Depends(
        require_household_admin
    ),
    session: Session = Depends(get_db_session),
) -> list[HouseholdUserResponse]:
    try:
        records = list_household_users(
            session=session,
            household_id=household_id,
        )

        return [
            _build_response(record)
            for record in records
        ]

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


@router.post(
    "/{household_id}/users",
    response_model=HouseholdUserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_household_user_endpoint(
    household_id: int,
    request: HouseholdUserCreateRequest,
    membership: HouseholdMember = Depends(
        require_household_admin
    ),
    session: Session = Depends(get_db_session),
) -> HouseholdUserResponse:
    try:
        record = create_household_user(
            session=session,
            household_id=household_id,
            email=str(request.email),
            display_name=request.display_name,
            password=request.password,
            role=request.role,
        )

        session.commit()

        return _build_response(record)

    except ValueError as error:
        session.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    except Exception:
        session.rollback()
        raise


@router.patch(
    "/{household_id}/users/{user_id}",
    response_model=HouseholdUserResponse,
)
def update_household_user_endpoint(
    household_id: int,
    user_id: int,
    request: HouseholdUserUpdateRequest,
    membership: HouseholdMember = Depends(
        require_household_admin
    ),
    current_user: User = Depends(
        get_current_user
    ),
    session: Session = Depends(get_db_session),
) -> HouseholdUserResponse:
    fields_set = set(
        request.model_fields_set
    )

    if not fields_set:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Legalább egy módosítandó mezőt "
                "meg kell adni."
            ),
        )

    try:
        record = update_household_user(
            session=session,
            household_id=household_id,
            user_id=user_id,
            acting_user_id=current_user.id,
            display_name=request.display_name,
            role=request.role,
            membership_is_active=(
                request.membership_is_active
            ),
            fields_set=fields_set,
        )

        session.commit()

        return _build_response(record)

    except ValueError as error:
        session.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    except Exception:
        session.rollback()
        raise
