"""
Kategóriamezők adminisztrációs HTTP-végpontjai.
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
    CategoryFieldAdminResponse,
    CategoryFieldCreateRequest,
    CategoryFieldOptionAdminResponse,
    CategoryFieldOptionCreateRequest,
    CategoryFieldOptionUpdateRequest,
    CategoryFieldUpdateRequest,
)
from app.services import (
    create_admin_category_field,
    create_admin_category_field_option,
    deactivate_admin_category_field,
    deactivate_admin_category_field_option,
    list_admin_category_field_options,
    list_admin_category_fields,
    update_admin_category_field,
    update_admin_category_field_option,
)


router = APIRouter(
    prefix="/admin/households",
    tags=["admin-category-fields"],
)


@router.get(
    "/{household_id}/categories/{category_id}/fields",
    response_model=list[CategoryFieldAdminResponse],
)
def get_admin_category_fields(
    household_id: int,
    category_id: int,
    membership: HouseholdMember = Depends(
        require_household_admin
    ),
    session: Session = Depends(
        get_db_session
    ),
) -> list[CategoryFieldAdminResponse]:
    try:
        fields = list_admin_category_fields(
            session=session,
            household_id=household_id,
            category_id=category_id,
        )

        return [
            CategoryFieldAdminResponse.model_validate(
                field
            )
            for field in fields
        ]

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


@router.post(
    "/{household_id}/categories/{category_id}/fields",
    response_model=CategoryFieldAdminResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_admin_category_field_endpoint(
    household_id: int,
    category_id: int,
    request: CategoryFieldCreateRequest,
    membership: HouseholdMember = Depends(
        require_household_admin
    ),
    session: Session = Depends(
        get_db_session
    ),
) -> CategoryFieldAdminResponse:
    try:
        field = create_admin_category_field(
            session=session,
            household_id=household_id,
            category_id=category_id,
            name=request.name,
            field_key=request.field_key,
            field_type=request.field_type,
            description=request.description,
            placeholder=request.placeholder,
            is_required=request.is_required,
            is_searchable=request.is_searchable,
            is_filterable=request.is_filterable,
            is_visible_in_list=(
                request.is_visible_in_list
            ),
            sort_order=request.sort_order,
            validation_rules=(
                request.validation_rules
            ),
            default_value=(
                request.default_value
            ),
        )

        session.commit()
        session.refresh(field)

        return (
            CategoryFieldAdminResponse.model_validate(
                field
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
    (
        "/{household_id}/categories/"
        "{category_id}/fields/{field_id}"
    ),
    response_model=CategoryFieldAdminResponse,
)
def update_admin_category_field_endpoint(
    household_id: int,
    category_id: int,
    field_id: int,
    request: CategoryFieldUpdateRequest,
    membership: HouseholdMember = Depends(
        require_household_admin
    ),
    session: Session = Depends(
        get_db_session
    ),
) -> CategoryFieldAdminResponse:
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
        field = update_admin_category_field(
            session=session,
            household_id=household_id,
            category_id=category_id,
            field_id=field_id,
            name=request.name,
            description=request.description,
            placeholder=request.placeholder,
            is_required=request.is_required,
            is_searchable=request.is_searchable,
            is_filterable=request.is_filterable,
            is_visible_in_list=(
                request.is_visible_in_list
            ),
            sort_order=request.sort_order,
            validation_rules=(
                request.validation_rules
            ),
            default_value=(
                request.default_value
            ),
            is_active=request.is_active,
            fields_set=fields_set,
        )

        session.commit()
        session.refresh(field)

        return (
            CategoryFieldAdminResponse.model_validate(
                field
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


@router.delete(
    (
        "/{household_id}/categories/"
        "{category_id}/fields/{field_id}"
    ),
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_admin_category_field_endpoint(
    household_id: int,
    category_id: int,
    field_id: int,
    membership: HouseholdMember = Depends(
        require_household_admin
    ),
    session: Session = Depends(
        get_db_session
    ),
) -> None:
    try:
        deactivate_admin_category_field(
            session=session,
            household_id=household_id,
            category_id=category_id,
            field_id=field_id,
        )

        session.commit()

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
    (
        "/{household_id}/categories/"
        "{category_id}/fields/{field_id}/options"
    ),
    response_model=list[
        CategoryFieldOptionAdminResponse
    ],
)
def get_admin_category_field_options(
    household_id: int,
    category_id: int,
    field_id: int,
    membership: HouseholdMember = Depends(
        require_household_admin
    ),
    session: Session = Depends(
        get_db_session
    ),
) -> list[CategoryFieldOptionAdminResponse]:
    try:
        options = (
            list_admin_category_field_options(
                session=session,
                household_id=household_id,
                category_id=category_id,
                field_id=field_id,
            )
        )

        return [
            CategoryFieldOptionAdminResponse
            .model_validate(
                option
            )
            for option in options
        ]

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


@router.post(
    (
        "/{household_id}/categories/"
        "{category_id}/fields/{field_id}/options"
    ),
    response_model=CategoryFieldOptionAdminResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_admin_category_field_option_endpoint(
    household_id: int,
    category_id: int,
    field_id: int,
    request: CategoryFieldOptionCreateRequest,
    membership: HouseholdMember = Depends(
        require_household_admin
    ),
    session: Session = Depends(
        get_db_session
    ),
) -> CategoryFieldOptionAdminResponse:
    try:
        option = (
            create_admin_category_field_option(
                session=session,
                household_id=household_id,
                category_id=category_id,
                field_id=field_id,
                value=request.value,
                label=request.label,
                sort_order=request.sort_order,
            )
        )

        session.commit()
        session.refresh(option)

        return (
            CategoryFieldOptionAdminResponse
            .model_validate(
                option
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
    (
        "/{household_id}/categories/"
        "{category_id}/fields/{field_id}/"
        "options/{option_id}"
    ),
    response_model=CategoryFieldOptionAdminResponse,
)
def update_admin_category_field_option_endpoint(
    household_id: int,
    category_id: int,
    field_id: int,
    option_id: int,
    request: CategoryFieldOptionUpdateRequest,
    membership: HouseholdMember = Depends(
        require_household_admin
    ),
    session: Session = Depends(
        get_db_session
    ),
) -> CategoryFieldOptionAdminResponse:
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
        option = (
            update_admin_category_field_option(
                session=session,
                household_id=household_id,
                category_id=category_id,
                field_id=field_id,
                option_id=option_id,
                value=request.value,
                label=request.label,
                sort_order=request.sort_order,
                is_active=request.is_active,
                fields_set=fields_set,
            )
        )

        session.commit()
        session.refresh(option)

        return (
            CategoryFieldOptionAdminResponse
            .model_validate(
                option
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


@router.delete(
    (
        "/{household_id}/categories/"
        "{category_id}/fields/{field_id}/"
        "options/{option_id}"
    ),
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_admin_category_field_option_endpoint(
    household_id: int,
    category_id: int,
    field_id: int,
    option_id: int,
    membership: HouseholdMember = Depends(
        require_household_admin
    ),
    session: Session = Depends(
        get_db_session
    ),
) -> None:
    try:
        deactivate_admin_category_field_option(
            session=session,
            household_id=household_id,
            category_id=category_id,
            field_id=field_id,
            option_id=option_id,
        )

        session.commit()

    except ValueError as error:
        session.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    except Exception:
        session.rollback()
        raise
