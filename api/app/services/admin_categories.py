"""
Háztartási kategória-adminisztráció üzleti logikája.

A rendszerkategóriák globálisak és ezen a service-en
keresztül nem módosíthatók.

A háztartási kategóriák kizárólag a saját
háztartásukon belül kezelhetők.
"""

import re
import unicodedata

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import Category, Household


def normalize_category_name(name: str) -> str:
    """
    Kategórianév normalizálása.
    """
    normalized = " ".join(
        name.strip().split()
    )

    if not normalized:
        raise ValueError(
            "A kategória neve nem lehet üres."
        )

    return normalized


def slugify_category_name(name: str) -> str:
    """
    URL-barát slug készítése kategórianévből.

    Az ékezeteket eltávolítja, kisbetűsít,
    a nem alfanumerikus részeket kötőjelre cseréli.
    """
    normalized = unicodedata.normalize(
        "NFKD",
        name,
    )

    ascii_name = normalized.encode(
        "ascii",
        "ignore",
    ).decode("ascii")

    slug = re.sub(
        r"[^a-z0-9]+",
        "-",
        ascii_name.lower(),
    ).strip("-")

    if not slug:
        slug = "category"

    return slug[:100]


def _ensure_household_exists(
    session: Session,
    household_id: int,
) -> Household:
    """
    Ellenőrzi, hogy a háztartás létezik és aktív.
    """
    household = session.scalar(
        select(Household).where(
            Household.id == household_id,
            Household.is_active.is_(True),
        )
    )

    if household is None:
        raise ValueError(
            "A háztartás nem található vagy nem aktív."
        )

    return household


def _build_unique_household_slug(
    session: Session,
    *,
    household_id: int,
    name: str,
    exclude_category_id: int | None = None,
) -> str:
    """
    Egyedi household-kategória slug készítése.

    Példa:
    film -> film
    film -> film-2
    film -> film-3
    """
    base_slug = slugify_category_name(
        name
    )

    candidate = base_slug
    suffix = 2

    while True:
        query = select(Category.id).where(
            Category.household_id
            == household_id,
            Category.slug == candidate,
        )

        if exclude_category_id is not None:
            query = query.where(
                Category.id
                != exclude_category_id
            )

        existing_id = session.scalar(
            query
        )

        if existing_id is None:
            return candidate

        suffix_text = f"-{suffix}"

        candidate = (
            base_slug[
                : 100 - len(suffix_text)
            ]
            + suffix_text
        )

        suffix += 1


def list_household_categories(
    session: Session,
    household_id: int,
) -> list[Category]:
    """
    Visszaadja az adott háztartás számára
    elérhető kategóriákat.

    A lista tartalmazza:
    - a globális rendszerkategóriákat;
    - az adott háztartás saját kategóriáit.

    Az inaktív kategóriák is szerepelnek,
    mert ez adminisztrációs lista.
    """
    _ensure_household_exists(
        session=session,
        household_id=household_id,
    )

    return list(
        session.scalars(
            select(Category)
            .where(
                or_(
                    Category.is_system.is_(
                        True
                    ),
                    Category.household_id
                    == household_id,
                )
            )
            .order_by(
                Category.is_system.desc(),
                Category.sort_order.asc(),
                Category.name.asc(),
                Category.id.asc(),
            )
        )
    )


def create_household_category(
    session: Session,
    *,
    household_id: int,
    name: str,
    description: str | None,
    icon: str | None,
    supports_barcode: bool,
    sort_order: int,
) -> Category:
    """
    Új saját kategória létrehozása.
    """
    _ensure_household_exists(
        session=session,
        household_id=household_id,
    )

    normalized_name = (
        normalize_category_name(name)
    )

    normalized_description = (
        description.strip()
        if description
        and description.strip()
        else None
    )

    normalized_icon = (
        icon.strip()
        if icon
        and icon.strip()
        else None
    )

    slug = _build_unique_household_slug(
        session=session,
        household_id=household_id,
        name=normalized_name,
    )

    category = Category(
        household_id=household_id,
        name=normalized_name,
        slug=slug,
        description=normalized_description,
        icon=normalized_icon,
        is_system=False,
        is_active=True,
        supports_barcode=supports_barcode,
        metadata_lookup_type="manual",
        sort_order=sort_order,
    )

    session.add(category)
    session.flush()

    return category


def update_household_category(
    session: Session,
    *,
    household_id: int,
    category_id: int,
    name: str | None,
    description: str | None,
    icon: str | None,
    supports_barcode: bool | None,
    sort_order: int | None,
    is_active: bool | None,
    fields_set: set[str],
) -> Category:
    """
    Saját household-kategória módosítása.

    Rendszerkategória ezen a service-en keresztül
    nem módosítható.
    """
    _ensure_household_exists(
        session=session,
        household_id=household_id,
    )

    category = session.scalar(
        select(Category).where(
            Category.id == category_id,
            or_(
                Category.is_system.is_(
                    True
                ),
                Category.household_id
                == household_id,
            ),
        )
    )

    if category is None:
        raise ValueError(
            "A kategória nem található."
        )

    if category.is_system:
        raise ValueError(
            "Rendszerkategória nem módosítható."
        )

    if category.household_id != household_id:
        raise ValueError(
            "A kategória nem ehhez a háztartáshoz tartozik."
        )

    if "name" in fields_set:
        if name is None:
            raise ValueError(
                "A kategória neve nem lehet null."
            )

        normalized_name = (
            normalize_category_name(name)
        )

        if normalized_name != category.name:
            category.name = normalized_name

            category.slug = (
                _build_unique_household_slug(
                    session=session,
                    household_id=household_id,
                    name=normalized_name,
                    exclude_category_id=(
                        category.id
                    ),
                )
            )

    if "description" in fields_set:
        category.description = (
            description.strip()
            if description
            and description.strip()
            else None
        )

    if "icon" in fields_set:
        category.icon = (
            icon.strip()
            if icon
            and icon.strip()
            else None
        )

    if "supports_barcode" in fields_set:
        if supports_barcode is None:
            raise ValueError(
                "A supports_barcode nem lehet null."
            )

        category.supports_barcode = (
            supports_barcode
        )

    if "sort_order" in fields_set:
        if sort_order is None:
            raise ValueError(
                "A sort_order nem lehet null."
            )

        category.sort_order = sort_order

    if "is_active" in fields_set:
        if is_active is None:
            raise ValueError(
                "Az is_active nem lehet null."
            )

        category.is_active = is_active

    session.flush()

    return category
