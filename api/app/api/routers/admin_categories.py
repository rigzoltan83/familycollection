"""
Háztartási kategória-adminisztráció HTTP-végpontjai.
"""

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.api.dependencies import (
    require_household_admin,
)
from app.core.database import get_db_session
from app.models import HouseholdMember
from app.schemas import (
    CategoryStorageLocationRuleResponse,
    CategoryStorageLocationRulesResponse,
    CategoryStorageLocationRulesUpdateRequest,
    HouseholdCategoryCreateRequest,
    HouseholdCategoryResponse,
    HouseholdCategoryUpdateRequest,
)
from app.services import (
    create_household_category,
    list_category_storage_rules,
    list_household_categories,
    replace_category_storage_rules,
    update_household_category,
)


router = APIRouter(
    prefix="/admin/households",
    tags=["admin-categories"],
)


@router.get(
    "/{household_id}/categories",
    response_model=list[HouseholdCategoryResponse],
)
def get_household_categories(
    household_id: int,
    membership: HouseholdMember = Depends(
        require_household_admin
    ),
    session: Session = Depends(
        get_db_session
    ),
) -> list[HouseholdCategoryResponse]:
    """
    Rendszer- és saját kategóriák listázása.
    """
    try:
        categories = list_household_categories(
            session=session,
            household_id=household_id,
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


@router.post(
    "/{household_id}/categories",
    response_model=HouseholdCategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_household_category_endpoint(
    household_id: int,
    request: HouseholdCategoryCreateRequest,
    membership: HouseholdMember = Depends(
        require_household_admin
    ),
    session: Session = Depends(
        get_db_session
    ),
) -> HouseholdCategoryResponse:
    """
    Új saját household-kategória létrehozása.
    """
    try:
        category = create_household_category(
            session=session,
            household_id=household_id,
            name=request.name,
            description=request.description,
            icon=request.icon,
            supports_barcode=(
                request.supports_barcode
            ),
            sort_order=request.sort_order,
        )

        session.commit()
        session.refresh(category)

        return (
            HouseholdCategoryResponse.model_validate(
                category
            )
        )

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
    "/{household_id}/categories/{category_id}",
    response_model=HouseholdCategoryResponse,
)
def update_household_category_endpoint(
    household_id: int,
    category_id: int,
    request: HouseholdCategoryUpdateRequest,
    membership: HouseholdMember = Depends(
        require_household_admin
    ),
    session: Session = Depends(
        get_db_session
    ),
) -> HouseholdCategoryResponse:
    """
    Saját household-kategória módosítása.
    """
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
        category = update_household_category(
            session=session,
            household_id=household_id,
            category_id=category_id,
            name=request.name,
            description=request.description,
            icon=request.icon,
            supports_barcode=(
                request.supports_barcode
            ),
            sort_order=request.sort_order,
            is_active=request.is_active,
            fields_set=fields_set,
        )

        session.commit()
        session.refresh(category)

        return (
            HouseholdCategoryResponse.model_validate(
                category
            )
        )

    except ValueError as error:
        session.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    except Exception:
        session.rollback()
        raise


@router.get(
    "/{household_id}/categories/{category_id}/storage-rules",
    response_model=CategoryStorageLocationRulesResponse,
)
def get_category_storage_rules(
    household_id: int,
    category_id: int,
    membership: HouseholdMember = Depends(
        require_household_admin
    ),
    session: Session = Depends(
        get_db_session
    ),
) -> CategoryStorageLocationRulesResponse:
    """
    Egy kategória explicit tárhelyszabályainak
    lekérése.

    Ha nincs szabály, restricted=False,
    ami azt jelenti, hogy minden aktív
    household-tárhely használható.
    """
    try:
        rules = list_category_storage_rules(
            session=session,
            household_id=household_id,
            category_id=category_id,
        )

        return CategoryStorageLocationRulesResponse(
            category_id=category_id,
            restricted=bool(rules),
            rules=[
                CategoryStorageLocationRuleResponse(
                    storage_location_public_id=(
                        rule.storage_location.public_id
                    ),
                    include_descendants=(
                        rule.include_descendants
                    ),
                )
                for rule in rules
            ],
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


@router.put(
    "/{household_id}/categories/{category_id}/storage-rules",
    response_model=CategoryStorageLocationRulesResponse,
)
def replace_category_storage_rules_endpoint(
    household_id: int,
    category_id: int,
    request: CategoryStorageLocationRulesUpdateRequest,
    membership: HouseholdMember = Depends(
        require_household_admin
    ),
    session: Session = Depends(
        get_db_session
    ),
) -> CategoryStorageLocationRulesResponse:
    """
    Egy kategória teljes tárhelyszabály-listájának
    atomikus cseréje.

    Üres rules lista = nincs tárhelykorlátozás.
    """
    try:
        rules = replace_category_storage_rules(
            session=session,
            household_id=household_id,
            category_id=category_id,
            rules=[
                (
                    rule.storage_location_public_id,
                    rule.include_descendants,
                )
                for rule in request.rules
            ],
        )

        session.commit()

        for rule in rules:
            session.refresh(rule)

        return CategoryStorageLocationRulesResponse(
            category_id=category_id,
            restricted=bool(rules),
            rules=[
                CategoryStorageLocationRuleResponse(
                    storage_location_public_id=(
                        rule.storage_location.public_id
                    ),
                    include_descendants=(
                        rule.include_descendants
                    ),
                )
                for rule in rules
            ],
        )

    except ValueError as error:
        session.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    except Exception:
        session.rollback()
        raise
