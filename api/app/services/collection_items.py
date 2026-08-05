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
    CategoryFieldOption,
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


def _get_field_options(
    session: Session,
    field_id: int,
) -> set[str]:
    """
    Az aktív választható értékek lekérése.
    """
    option_values = session.scalars(
        select(CategoryFieldOption.value).where(
            CategoryFieldOption.field_id == field_id,
            CategoryFieldOption.is_active.is_(True),
        )
    ).all()

    return set(option_values)


def _validate_numeric_rules(
    category_field: CategoryField,
    numeric_value: int | Decimal,
) -> None:
    rules = category_field.validation_rules or {}

    minimum = rules.get("minimum")
    maximum = rules.get("maximum")

    if minimum is not None and numeric_value < Decimal(str(minimum)):
        raise ValueError(
            f"A(z) {category_field.field_key} mező értéke "
            f"nem lehet kisebb mint {minimum}."
        )

    if maximum is not None and numeric_value > Decimal(str(maximum)):
        raise ValueError(
            f"A(z) {category_field.field_key} mező értéke "
            f"nem lehet nagyobb mint {maximum}."
        )


def _validate_text_rules(
    category_field: CategoryField,
    text_value: str,
) -> None:
    rules = category_field.validation_rules or {}

    minimum_length = rules.get("minimum_length")
    maximum_length = rules.get("maximum_length")

    if (
        minimum_length is not None
        and len(text_value) < int(minimum_length)
    ):
        raise ValueError(
            f"A(z) {category_field.field_key} mező legalább "
            f"{minimum_length} karakter hosszú legyen."
        )

    if (
        maximum_length is not None
        and len(text_value) > int(maximum_length)
    ):
        raise ValueError(
            f"A(z) {category_field.field_key} mező legfeljebb "
            f"{maximum_length} karakter hosszú lehet."
        )


def _validate_select_value(
    session: Session,
    category_field: CategoryField,
    value: Any,
) -> None:
    allowed_values = _get_field_options(
        session=session,
        field_id=category_field.id,
    )

    if category_field.field_type == "single_select":
        if not isinstance(value, str):
            raise ValueError(
                f"A(z) {category_field.field_key} mező "
                "egyetlen szöveges értéket vár."
            )

        if value not in allowed_values:
            raise ValueError(
                f"Érvénytelen választási érték a(z) "
                f"{category_field.field_key} mezőnél: {value}"
            )

        return

    if not isinstance(value, list):
        raise ValueError(
            f"A(z) {category_field.field_key} mező "
            "értéklistát vár."
        )

    invalid_values = set(value) - allowed_values

    if invalid_values:
        invalid = ", ".join(sorted(str(item) for item in invalid_values))

        raise ValueError(
            f"Érvénytelen választási értékek a(z) "
            f"{category_field.field_key} mezőnél: {invalid}"
        )


def _build_field_value(
    session: Session,
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
        text_value = str(value).strip()

        _validate_text_rules(
            category_field=category_field,
            text_value=text_value,
        )

        field_value.value_text = text_value

    elif field_type in {
        "integer",
        "year",
    }:
        try:
            integer_value = int(value)
        except (TypeError, ValueError) as error:
            raise ValueError(
                f"A(z) {category_field.field_key} mező "
                "egész számot vár."
            ) from error

        _validate_numeric_rules(
            category_field=category_field,
            numeric_value=integer_value,
        )

        field_value.value_integer = integer_value

    elif field_type == "decimal":
        try:
            decimal_value = Decimal(str(value))
        except Exception as error:
            raise ValueError(
                f"A(z) {category_field.field_key} mező "
                "decimális számot vár."
            ) from error

        _validate_numeric_rules(
            category_field=category_field,
            numeric_value=decimal_value,
        )

        field_value.value_decimal = decimal_value

    elif field_type == "boolean":
        if not isinstance(value, bool):
            raise ValueError(
                f"A(z) {category_field.field_key} mező "
                "logikai értéket vár."
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
        _validate_select_value(
            session=session,
            category_field=category_field,
            value=value,
        )

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
                session=session,
                item=item,
                category_field=category_fields[field_key],
                value=value,
            )
        )

    session.flush()

    return item
