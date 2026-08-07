"""
Felhasználói kategória-végpontok.

Ezek nem adminisztrációs végpontok:
a bejelentkezett household-tagok számára
az aktív, használható kategóriákat adják vissza.
"""

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.api.dependencies import (
    require_household_viewer,
)
from app.core.database import get_db_session
from app.models import HouseholdMember
from app.schemas import (
    HouseholdCategoryResponse,
)
from app.services import (
    list_available_household_categories,
)


router = APIRouter(
    prefix="/households",
    tags=["categories"],
)


@router.get(
    "/{household_id}/categories",
    response_model=list[HouseholdCategoryResponse],
)
def get_available_categories(
    household_id: int,
    membership: HouseholdMember = Depends(
        require_household_viewer
    ),
    session: Session = Depends(
        get_db_session
    ),
) -> list[HouseholdCategoryResponse]:
    """
    Az adott háztartásban használható
    aktív kategóriák listája.
    """
    try:
        categories = (
            list_available_household_categories(
                session=session,
                household_id=household_id,
            )
        )

        return [
            HouseholdCategoryResponse.model_validate(
                category
            )
            for category in categories
        ]

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
