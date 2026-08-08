"""
Kategóriamező-definíciók lekérdezési szolgáltatásai.

A frontend ezek alapján építheti fel dinamikusan
az egyes gyűjtemények adatbeviteli felületét.
"""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Category,
    CategoryField,
    CategoryFieldOption,
    Household,
)


@dataclass(frozen=True)
class CategoryFieldOptionRecord:
    public_id: str

    value: str
    label: str

    sort_order: int


@dataclass(frozen=True)
class CategoryFieldRecord:
    public_id: str

    category_id: int

    name: str
    field_key: str
    field_type: str

    description: str | None
    placeholder: str | None

    is_required: bool
    is_searchable: bool
    is_filterable: bool
    is_visible_in_list: bool

    sort_order: int

    validation_rules: dict
    default_value: dict

    options: list[CategoryFieldOptionRecord]


def _ensure_household_exists(
    session: Session,
    household_id: int,
) -> Household:
    household = session.get(
        Household,
        household_id,
    )

    if household is None or not household.is_active:
        raise ValueError(
            "A megadott háztartás nem elérhető."
        )

    return household


def _ensure_category_available(
    session: Session,
    *,
    household_id: int,
    category_id: int,
) -> Category:
    category = session.get(
        Category,
        category_id,
    )

    if category is None or not category.is_active:
        raise ValueError(
            "A megadott kategória nem elérhető."
        )

    if category.is_system:
        return category

    if category.household_id != household_id:
        raise ValueError(
            "A kategória nem a megadott "
            "háztartáshoz tartozik."
        )

    return category


def list_category_fields(
    session: Session,
    *,
    household_id: int,
    category_id: int,
) -> list[CategoryFieldRecord]:
    """
    Egy elérhető kategória aktív meződefiníciói.

    Csak az aktív mezőket és az aktív
    választási lehetőségeket adja vissza.
    """

    _ensure_household_exists(
        session=session,
        household_id=household_id,
    )

    category = _ensure_category_available(
        session=session,
        household_id=household_id,
        category_id=category_id,
    )

    fields = session.scalars(
        select(CategoryField)
        .where(
            CategoryField.category_id
            == category.id,
            CategoryField.is_active.is_(True),
        )
        .order_by(
            CategoryField.sort_order.asc(),
            CategoryField.id.asc(),
        )
    ).all()

    records: list[CategoryFieldRecord] = []

    for category_field in fields:
        options = session.scalars(
            select(CategoryFieldOption)
            .where(
                CategoryFieldOption.field_id
                == category_field.id,
                CategoryFieldOption.is_active.is_(
                    True
                ),
            )
            .order_by(
                CategoryFieldOption.sort_order.asc(),
                CategoryFieldOption.id.asc(),
            )
        ).all()

        records.append(
            CategoryFieldRecord(
                public_id=str(
                    category_field.public_id
                ),
                category_id=category_field.category_id,
                name=category_field.name,
                field_key=category_field.field_key,
                field_type=category_field.field_type,
                description=category_field.description,
                placeholder=category_field.placeholder,
                is_required=category_field.is_required,
                is_searchable=category_field.is_searchable,
                is_filterable=category_field.is_filterable,
                is_visible_in_list=(
                    category_field.is_visible_in_list
                ),
                sort_order=category_field.sort_order,
                validation_rules=(
                    category_field.validation_rules
                    or {}
                ),
                default_value=(
                    category_field.default_value
                    or {}
                ),
                options=[
                    CategoryFieldOptionRecord(
                        public_id=str(
                            option.public_id
                        ),
                        value=option.value,
                        label=option.label,
                        sort_order=option.sort_order,
                    )
                    for option in options
                ],
            )
        )

    return records
