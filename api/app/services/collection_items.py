"""
CollectionItem üzleti szolgáltatások.

A szolgáltatás egy tranzakcióban hozza létre:

- a központi CollectionItem rekordot;
- az opcionális azonosítókat;
- a dinamikus kategóriamező-értékeket.

A HTTP-rétegtől független.
"""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Category,
    CategoryField,
    CollectionItem,
    Household,
    ItemFieldValue,
    ItemIdentifier,
    User,
)


@dataclass(slots=True)
class IdentifierInput:
    identifier_type: str
    identifier_value: str
    provider_code: str | None = None
    is_primary: bool = False


@dataclass(slots=True)
class CollectionItemCreateInput:
    household_id: int
    category_id: int
    title: str
    subtitle: str | None = None
    notes: str | None = None
    status: str = "active"
    created_by_user_id: int | None = None
    identifiers: list[IdentifierInput] = field(default_factory=list)
    field_values: dict[str, Any] = field(default_factory=dict)


def _ensure_household_exists(
    session: Session,
    household_id: int,
) -> Household:
    household = session.get(Household, household_id)

    if household is None:
        raise ValueError("A megadott háztartás nem létezik.")

    return household


def _ensure_category_available(
    session: Session,
    category_id: int,
    household_id: int,
) -> Category:
    category = session.get(Category, category_id)

    if category is None or not category.is_active:
        raise ValueError("A megadott kategória nem elérhető.")

    if category.is_system:
        return category

    if category.household_id != household_id:
        raise ValueError(
            "A kategória nem a megadott háztartáshoz tartozik."
        )

    return category


def _ensure_user_exists(
    session: Session,
    user_id: int | None,
) -> User | None:
    if user_id is None:
        return None

    user = session.get(User, user_id)

    if user is None:
        raise ValueError("A megadott felhasználó nem létezik.")

    return user


def _get_category_fields(
    session: Session,
    category_id: int,
) -> dict[str, CategoryField]:
    fields = session.scalars(
        select(CategoryField).where(
            CategoryField.category_id == category_id,
            CategoryField.is_active.is_(True),
        )
    ).all()

    return {
        category_field.field_key: category_field
        for category_field in fields
    }


def _build_field_value(
    item: CollectionItem,
    category_field: CategoryField,
    value: Any,
) -> ItemFieldValue:
    field_value = ItemFieldValue(
        item=item,
        field=category_field,
    )

    field_type = category_field.field_type

    if field_type in {
        "text",
        "long_text",
        "url",
        "email",
        "barcode",
        "image",
        "file",
    }:
        field_value.value_text = str(value)

    elif field_type in {
        "integer",
        "year",
    }:
        field_value.value_integer = int(value)

    elif field_type == "decimal":
        field_value.value_decimal = Decimal(str(value))

    elif field_type == "boolean":
        if not isinstance(value, bool):
            raise ValueError(
                f"A(z) {category_field.field_key} mező logikai értéket vár."
            )

        field_value.value_boolean = value

    elif field_type == "date":
        if not isinstance(value, date):
            raise ValueError(
                f"A(z) {category_field.field_key} mező dátumot vár."
            )

        field_value.value_date = value

    elif field_type in {
        "single_select",
        "multi_select",
    }:
        field_value.value_json = value

    else:
        raise ValueError(
            f"Nem támogatott mezőtípus: {field_type}"
        )

    return field_value


def create_collection_item(
    session: Session,
    data: CollectionItemCreateInput,
) -> CollectionItem:
    """
    Új gyűjteményi elem létrehozása.

    A hívó kezeli a commitot vagy rollbacket.
    """
    _ensure_household_exists(
        session=session,
        household_id=data.household_id,
    )

    category = _ensure_category_available(
        session=session,
        category_id=data.category_id,
        household_id=data.household_id,
    )

    creator = _ensure_user_exists(
        session=session,
        user_id=data.created_by_user_id,
    )

    normalized_title = data.title.strip()

    if not normalized_title:
        raise ValueError("A cím nem lehet üres.")

    category_fields = _get_category_fields(
        session=session,
        category_id=category.id,
    )

    unknown_field_keys = (
        set(data.field_values) - set(category_fields)
    )

    if unknown_field_keys:
        unknown = ", ".join(sorted(unknown_field_keys))

        raise ValueError(
            f"Ismeretlen kategóriamezők: {unknown}"
        )

    missing_required_fields = [
        category_field.field_key
        for category_field in category_fields.values()
        if category_field.is_required
        and category_field.field_key not in data.field_values
    ]

    if missing_required_fields:
        missing = ", ".join(sorted(missing_required_fields))

        raise ValueError(
            f"Hiányzó kötelező mezők: {missing}"
        )

    item = CollectionItem(
        household_id=data.household_id,
        category=category,
        title=normalized_title,
        subtitle=data.subtitle,
        notes=data.notes,
        status=data.status,
        created_by_user=creator,
        updated_by_user=creator,
    )

    session.add(item)
    session.flush()

    for identifier_input in data.identifiers:
        identifier_value = (
            identifier_input.identifier_value.strip()
        )

        if not identifier_value:
            raise ValueError(
                "Az azonosító értéke nem lehet üres."
            )

        session.add(
            ItemIdentifier(
                item=item,
                identifier_type=identifier_input.identifier_type,
                identifier_value=identifier_value,
                provider_code=identifier_input.provider_code,
                is_primary=identifier_input.is_primary,
            )
        )

    for field_key, value in data.field_values.items():
        if value is None:
            continue

        session.add(
            _build_field_value(
                item=item,
                category_field=category_fields[field_key],
                value=value,
            )
        )

    session.flush()

    return item
