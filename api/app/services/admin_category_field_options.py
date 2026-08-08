"""
Kategóriamező-opciók adminisztrációs üzleti logikája.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Category,
    CategoryField,
    CategoryFieldOption,
    Household,
)


SELECT_FIELD_TYPES = {
    "single_select",
    "multi_select",
}


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


def _get_select_field(
    session: Session,
    *,
    household_id: int,
    category_id: int,
    field_id: int,
) -> CategoryField:
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

    if field.field_type not in SELECT_FIELD_TYPES:
        raise ValueError(
            "Csak egyszeres vagy többszörös "
            "választás típusú mezőhöz "
            "adható válaszlehetőség."
        )

    return field


def list_admin_category_field_options(
    session: Session,
    *,
    household_id: int,
    category_id: int,
    field_id: int,
) -> list[CategoryFieldOption]:
    """
    Egy select mező összes opciójának listázása.

    Az inaktív opciók is szerepelnek,
    mert az admin felületen kezelhetők.
    """
    _ensure_household_exists(
        session=session,
        household_id=household_id,
    )

    field = _get_select_field(
        session=session,
        household_id=household_id,
        category_id=category_id,
        field_id=field_id,
    )

    return list(
        session.scalars(
            select(CategoryFieldOption)
            .where(
                CategoryFieldOption.field_id
                == field.id
            )
            .order_by(
                CategoryFieldOption.sort_order.asc(),
                CategoryFieldOption.id.asc(),
            )
        ).all()
    )


def create_admin_category_field_option(
    session: Session,
    *,
    household_id: int,
    category_id: int,
    field_id: int,
    value: str,
    label: str,
    sort_order: int,
) -> CategoryFieldOption:
    """
    Új válaszlehetőség létrehozása select mezőhöz.
    """
    _ensure_household_exists(
        session=session,
        household_id=household_id,
    )

    field = _get_select_field(
        session=session,
        household_id=household_id,
        category_id=category_id,
        field_id=field_id,
    )

    normalized_value = value.strip()
    normalized_label = label.strip()

    if not normalized_value:
        raise ValueError(
            "Az opció értéke nem lehet üres."
        )

    if not normalized_label:
        raise ValueError(
            "Az opció címkéje nem lehet üres."
        )

    existing = session.scalar(
        select(CategoryFieldOption).where(
            CategoryFieldOption.field_id
            == field.id,
            CategoryFieldOption.value
            == normalized_value,
        )
    )

    if existing is not None:
        raise ValueError(
            "Ezzel az értékkel már létezik "
            "opció ennél a mezőnél."
        )

    option = CategoryFieldOption(
        field_id=field.id,
        value=normalized_value,
        label=normalized_label,
        sort_order=sort_order,
        is_active=True,
    )

    session.add(option)
    session.flush()

    return option


def update_admin_category_field_option(
    session: Session,
    *,
    household_id: int,
    category_id: int,
    field_id: int,
    option_id: int,
    value: str | None,
    label: str | None,
    sort_order: int | None,
    is_active: bool | None,
    fields_set: set[str],
) -> CategoryFieldOption:
    """
    Meglévő select-opció módosítása.
    """
    _ensure_household_exists(
        session=session,
        household_id=household_id,
    )

    field = _get_select_field(
        session=session,
        household_id=household_id,
        category_id=category_id,
        field_id=field_id,
    )

    option = session.scalar(
        select(CategoryFieldOption).where(
            CategoryFieldOption.id == option_id,
            CategoryFieldOption.field_id
            == field.id,
        )
    )

    if option is None:
        raise ValueError(
            "A válaszlehetőség nem található."
        )

    if "value" in fields_set:
        if value is None:
            raise ValueError(
                "Az opció értéke nem lehet null."
            )

        normalized_value = value.strip()

        if not normalized_value:
            raise ValueError(
                "Az opció értéke nem lehet üres."
            )

        duplicate = session.scalar(
            select(CategoryFieldOption).where(
                CategoryFieldOption.field_id
                == field.id,
                CategoryFieldOption.value
                == normalized_value,
                CategoryFieldOption.id
                != option.id,
            )
        )

        if duplicate is not None:
            raise ValueError(
                "Ezzel az értékkel már létezik "
                "másik opció ennél a mezőnél."
            )

        option.value = normalized_value

    if "label" in fields_set:
        if label is None:
            raise ValueError(
                "Az opció címkéje nem lehet null."
            )

        normalized_label = label.strip()

        if not normalized_label:
            raise ValueError(
                "Az opció címkéje nem lehet üres."
            )

        option.label = normalized_label

    if "sort_order" in fields_set:
        if sort_order is None:
            raise ValueError(
                "A sort_order nem lehet null."
            )

        option.sort_order = sort_order

    if "is_active" in fields_set:
        if is_active is None:
            raise ValueError(
                "Az is_active nem lehet null."
            )

        option.is_active = is_active

    session.flush()

    return option


def deactivate_admin_category_field_option(
    session: Session,
    *,
    household_id: int,
    category_id: int,
    field_id: int,
    option_id: int,
) -> None:
    """
    Select-opció logikai törlése.
    """
    _ensure_household_exists(
        session=session,
        household_id=household_id,
    )

    field = _get_select_field(
        session=session,
        household_id=household_id,
        category_id=category_id,
        field_id=field_id,
    )

    option = session.scalar(
        select(CategoryFieldOption).where(
            CategoryFieldOption.id == option_id,
            CategoryFieldOption.field_id
            == field.id,
        )
    )

    if option is None:
        raise ValueError(
            "A válaszlehetőség nem található."
        )

    option.is_active = False

    session.flush()
