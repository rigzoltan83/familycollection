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
    CategoryAllowedStorageResponse,
    CategoryFieldResponse,
    HouseholdCategoryResponse,
)
from app.services import (
    get_allowed_storage_location_public_ids,
    list_available_household_categories,
    list_category_fields,
    list_category_storage_rules,
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


@router.get(
    "/{household_id}/categories/{category_id}/fields",
    response_model=list[CategoryFieldResponse],
)
def get_category_fields(
    household_id: int,
    category_id: int,
    membership: HouseholdMember = Depends(
        require_household_viewer
    ),
    session: Session = Depends(
        get_db_session
    ),
) -> list[CategoryFieldResponse]:
    """
    Az adott háztartásban használható kategória
    aktív meződefinícióinak lekérése.
    """
    try:
        records = list_category_fields(
            session=session,
            household_id=household_id,
            category_id=category_id,
        )

        return [
            CategoryFieldResponse(
                public_id=record.public_id,
                category_id=record.category_id,
                name=record.name,
                field_key=record.field_key,
                field_type=record.field_type,
                description=record.description,
                placeholder=record.placeholder,
                is_required=record.is_required,
                is_searchable=record.is_searchable,
                is_filterable=record.is_filterable,
                is_visible_in_list=(
                    record.is_visible_in_list
                ),
                sort_order=record.sort_order,
                validation_rules=(
                    record.validation_rules
                ),
                default_value=(
                    record.default_value
                ),
                options=[
                    {
                        "public_id":
                            option.public_id,
                        "value":
                            option.value,
                        "label":
                            option.label,
                        "sort_order":
                            option.sort_order,
                    }
                    for option in record.options
                ],
            )
            for record in records
        ]

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


@router.get(
    (
        "/{household_id}/categories/"
        "{category_id}/allowed-storage"
    ),
    response_model=CategoryAllowedStorageResponse,
)
def get_category_allowed_storage(
    household_id: int,
    category_id: int,
    membership: HouseholdMember = Depends(
        require_household_viewer
    ),
    session: Session = Depends(
        get_db_session
    ),
) -> CategoryAllowedStorageResponse:
    """
    Az adott kategóriában ténylegesen
    használható aktív tárhelyek lekérése.
    """

    try:
        rules = list_category_storage_rules(
            session=session,
            household_id=household_id,
            category_id=category_id,
        )

        public_ids = (
            get_allowed_storage_location_public_ids(
                session=session,
                household_id=household_id,
                category_id=category_id,
            )
        )

        return CategoryAllowedStorageResponse(
            category_id=category_id,
            restricted=bool(rules),
            storage_public_ids=sorted(
                public_ids
            ),
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
