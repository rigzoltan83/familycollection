"""
Kategóriamezők adminisztrációs üzleti logikája.
"""

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Category,
    CategoryField,
    Household,
)


def normalize_field_key(
    field_key: str,
) -> str:
    """
    Mezőkulcs normalizálása.

    Csak kisbetű, szám és aláhúzás marad.
    """
    normalized = (
        field_key
        .strip()
        .lower()
        .replace("-", "_")
        .replace(" ", "_")
    )

    normalized = re.sub(
        r"[^a-z0-9_]+",
        "",
        normalized,
    )

    normalized = re.sub(
        r"_+",
        "_",
        normalized,
    ).strip("_")

    if not normalized:
        raise ValueError(
            "A mezőkulcs nem lehet üres."
        )

    if len(normalized) > 100:
        raise ValueError(
            "A mezőkulcs legfeljebb "
            "100 karakter hosszú lehet."
        )

    return normalized


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
            "Az aktív háztartás nem található."
        )

    return household


def _get_editable_category(
    session: Session,
    *,
    household_id: int,
    category_id: int,
) -> Category:
    category = session.get(
        Category,
        category_id,
    )

    if category is None:
        raise ValueError(
            "A kategória nem található."
        )

    if not category.is_active:
        raise ValueError(
            "Az inaktív kategória nem módosítható."
        )

    if category.is_system:
        raise ValueError(
            "Rendszerkategória mezői ezen a "
            "felületen nem módosíthatók."
        )

    if category.household_id != household_id:
        raise ValueError(
            "A kategória nem ehhez a "
            "háztartáshoz tartozik."
        )

    return category


def list_admin_category_fields(
    session: Session,
    *,
    household_id: int,
    category_id: int,
) -> list[CategoryField]:
    """
    Saját kategória összes mezőjének listázása.

    Az inaktív mezőket is visszaadja,
    mert az admin felületen ezeket is kezelni kell.
    """
    _ensure_household_exists(
        session=session,
        household_id=household_id,
    )

    category = _get_editable_category(
        session=session,
        household_id=household_id,
        category_id=category_id,
    )

    return list(
        session.scalars(
            select(CategoryField)
            .where(
                CategoryField.category_id
                == category.id
            )
            .order_by(
                CategoryField.sort_order.asc(),
                CategoryField.id.asc(),
            )
        ).all()
    )


def create_admin_category_field(
    session: Session,
    *,
    household_id: int,
    category_id: int,
    name: str,
    field_key: str,
    field_type: str,
    description: str | None,
    placeholder: str | None,
    is_required: bool,
    is_searchable: bool,
    is_filterable: bool,
    is_visible_in_list: bool,
    sort_order: int,
    validation_rules: dict,
    default_value: dict,
) -> CategoryField:
    """
    Új dinamikus mező létrehozása
    saját household-kategóriához.
    """
    _ensure_household_exists(
        session=session,
        household_id=household_id,
    )

    category = _get_editable_category(
        session=session,
        household_id=household_id,
        category_id=category_id,
    )

    normalized_name = name.strip()

    if not normalized_name:
        raise ValueError(
            "A mező neve nem lehet üres."
        )

    normalized_field_key = (
        normalize_field_key(
            field_key
        )
    )

    existing = session.scalar(
        select(CategoryField).where(
            CategoryField.category_id
            == category.id,
            CategoryField.field_key
            == normalized_field_key,
        )
    )

    if existing is not None:
        raise ValueError(
            "Ezzel a mezőkulccsal már "
            "létezik mező ebben a kategóriában."
        )

    normalized_description = (
        description.strip()
        if description
        and description.strip()
        else None
    )

    normalized_placeholder = (
        placeholder.strip()
        if placeholder
        and placeholder.strip()
        else None
    )

    field = CategoryField(
        category_id=category.id,
        name=normalized_name,
        field_key=normalized_field_key,
        field_type=field_type,
        description=normalized_description,
        placeholder=normalized_placeholder,
        is_required=is_required,
        is_searchable=is_searchable,
        is_filterable=is_filterable,
        is_visible_in_list=is_visible_in_list,
        is_active=True,
        sort_order=sort_order,
        validation_rules=validation_rules or {},
        default_value=default_value or {},
    )

    session.add(field)
    session.flush()

    return field


def update_admin_category_field(
    session: Session,
    *,
    household_id: int,
    category_id: int,
    field_id: int,
    name: str | None,
    description: str | None,
    placeholder: str | None,
    is_required: bool | None,
    is_searchable: bool | None,
    is_filterable: bool | None,
    is_visible_in_list: bool | None,
    sort_order: int | None,
    validation_rules: dict | None,
    default_value: dict | None,
    is_active: bool | None,
    fields_set: set[str],
) -> CategoryField:
    """
    Meglévő kategóriamező módosítása.

    A field_key és field_type szándékosan
    nem módosítható ezen a végponton.
    """
    _ensure_household_exists(
        session=session,
        household_id=household_id,
    )

    category = _get_editable_category(
        session=session,
        household_id=household_id,
        category_id=category_id,
    )

    field = session.scalar(
        select(CategoryField).where(
            CategoryField.id == field_id,
            CategoryField.category_id
            == category.id,
        )
    )

    if field is None:
        raise ValueError(
            "A kategóriamező nem található."
        )

    if "name" in fields_set:
        if name is None:
            raise ValueError(
                "A mező neve nem lehet null."
            )

        normalized_name = name.strip()

        if not normalized_name:
            raise ValueError(
                "A mező neve nem lehet üres."
            )

        field.name = normalized_name

    if "description" in fields_set:
        field.description = (
            description.strip()
            if description
            and description.strip()
            else None
        )

    if "placeholder" in fields_set:
        field.placeholder = (
            placeholder.strip()
            if placeholder
            and placeholder.strip()
            else None
        )

    if "is_required" in fields_set:
        if is_required is None:
            raise ValueError(
                "Az is_required nem lehet null."
            )

        field.is_required = is_required

    if "is_searchable" in fields_set:
        if is_searchable is None:
            raise ValueError(
                "Az is_searchable nem lehet null."
            )

        field.is_searchable = is_searchable

    if "is_filterable" in fields_set:
        if is_filterable is None:
            raise ValueError(
                "Az is_filterable nem lehet null."
            )

        field.is_filterable = is_filterable

    if "is_visible_in_list" in fields_set:
        if is_visible_in_list is None:
            raise ValueError(
                "Az is_visible_in_list "
                "nem lehet null."
            )

        field.is_visible_in_list = (
            is_visible_in_list
        )

    if "sort_order" in fields_set:
        if sort_order is None:
            raise ValueError(
                "A sort_order nem lehet null."
            )

        field.sort_order = sort_order

    if "validation_rules" in fields_set:
        field.validation_rules = (
            validation_rules or {}
        )

    if "default_value" in fields_set:
        field.default_value = (
            default_value or {}
        )

    if "is_active" in fields_set:
        if is_active is None:
            raise ValueError(
                "Az is_active nem lehet null."
            )

        field.is_active = is_active

    session.flush()

    return field


def deactivate_admin_category_field(
    session: Session,
    *,
    household_id: int,
    category_id: int,
    field_id: int,
) -> None:
    """
    Kategóriamező logikai törlése.
    """
    _ensure_household_exists(
        session=session,
        household_id=household_id,
    )

    category = _get_editable_category(
        session=session,
        household_id=household_id,
        category_id=category_id,
    )

    field = session.scalar(
        select(CategoryField).where(
            CategoryField.id == field_id,
            CategoryField.category_id
            == category.id,
        )
    )

    if field is None:
        raise ValueError(
            "A kategóriamező nem található."
        )

    field.is_active = False

    session.flush()
