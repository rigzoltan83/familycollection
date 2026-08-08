"""
Kategóriákhoz engedélyezett tárhelyek kezelése.

Szabály:

- ha egy household + category pároshoz nincs szabály,
  akkor minden aktív tárhely engedélyezett;
- ha van legalább egy szabály, akkor csak a kijelölt
  tárhelyek és az include_descendants=True szabályok
  leszármazottai engedélyezettek.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    CategoryStorageLocation,
    StorageLocation,
)


def _collect_descendant_ids(
    *,
    root_id: int,
    children_by_parent_id: dict[
        int | None,
        list[StorageLocation],
    ],
) -> set[int]:
    result: set[int] = set()

    stack = list(
        children_by_parent_id.get(
            root_id,
            [],
        )
    )

    while stack:
        location = stack.pop()

        if location.id in result:
            continue

        result.add(
            location.id
        )

        stack.extend(
            children_by_parent_id.get(
                location.id,
                [],
            )
        )

    return result


def get_allowed_storage_location_ids(
    session: Session,
    *,
    household_id: int,
    category_id: int,
) -> set[int]:
    """
    Visszaadja az adott kategóriában használható
    aktív StorageLocation rekordok ID-it.

    Ha nincs kategória-specifikus szabály:
    minden aktív household tárhely engedélyezett.
    """

    locations = session.scalars(
        select(StorageLocation).where(
            StorageLocation.household_id
            == household_id,
            StorageLocation.is_active.is_(True),
        )
    ).all()

    location_by_id = {
        location.id: location
        for location in locations
    }

    rules = session.scalars(
        select(CategoryStorageLocation).where(
            CategoryStorageLocation.household_id
            == household_id,
            CategoryStorageLocation.category_id
            == category_id,
        )
    ).all()

    if not rules:
        return set(
            location_by_id
        )

    children_by_parent_id: dict[
        int | None,
        list[StorageLocation],
    ] = {}

    for location in locations:
        children_by_parent_id.setdefault(
            location.parent_id,
            [],
        ).append(
            location
        )

    allowed_ids: set[int] = set()

    for rule in rules:
        if (
            rule.storage_location_id
            not in location_by_id
        ):
            continue

        allowed_ids.add(
            rule.storage_location_id
        )

        if rule.include_descendants:
            allowed_ids.update(
                _collect_descendant_ids(
                    root_id=(
                        rule.storage_location_id
                    ),
                    children_by_parent_id=(
                        children_by_parent_id
                    ),
                )
            )

    return allowed_ids


def is_storage_location_allowed(
    session: Session,
    *,
    household_id: int,
    category_id: int,
    storage_location_id: int,
) -> bool:
    return (
        storage_location_id
        in get_allowed_storage_location_ids(
            session=session,
            household_id=household_id,
            category_id=category_id,
        )
    )

def list_category_storage_rules(
    session: Session,
    *,
    household_id: int,
    category_id: int,
) -> list[CategoryStorageLocation]:
    """
    Visszaadja az adott household + category
    explicit tárhelyszabályait.
    """

    return session.scalars(
        select(CategoryStorageLocation)
        .where(
            CategoryStorageLocation.household_id
            == household_id,
            CategoryStorageLocation.category_id
            == category_id,
        )
        .order_by(
            CategoryStorageLocation.id.asc()
        )
    ).all()


def replace_category_storage_rules(
    session: Session,
    *,
    household_id: int,
    category_id: int,
    rules: list[
        tuple[str, bool]
    ],
) -> list[CategoryStorageLocation]:
    """
    Lecseréli az adott kategória teljes
    tárhelyszabály-listáját.

    A rules elemei:
    (
        storage_location_public_id,
        include_descendants,
    )

    Üres lista = nincs korlátozás.
    """

    existing_rules = (
        list_category_storage_rules(
            session=session,
            household_id=household_id,
            category_id=category_id,
        )
    )

    for existing_rule in existing_rules:
        session.delete(
            existing_rule
        )

    seen_public_ids: set[str] = set()

    new_rules: list[
        CategoryStorageLocation
    ] = []

    for (
        storage_location_public_id,
        include_descendants,
    ) in rules:
        normalized_public_id = (
            storage_location_public_id.strip()
        )

        if not normalized_public_id:
            raise ValueError(
                "A tárhely public_id "
                "nem lehet üres."
            )

        if (
            normalized_public_id
            in seen_public_ids
        ):
            raise ValueError(
                "Ugyanaz a tárhely csak egyszer "
                "szerepelhet a szabályok között."
            )

        seen_public_ids.add(
            normalized_public_id
        )

        location = session.scalar(
            select(StorageLocation).where(
                StorageLocation.public_id
                == normalized_public_id,
                StorageLocation.household_id
                == household_id,
            )
        )

        if location is None:
            raise ValueError(
                "A megadott tárhely nem létezik "
                "ebben a háztartásban."
            )

        if not location.is_active:
            raise ValueError(
                "Inaktív tárhely nem rendelhető "
                "kategóriához."
            )

        rule = CategoryStorageLocation(
            household_id=household_id,
            category_id=category_id,
            storage_location_id=(
                location.id
            ),
            include_descendants=(
                include_descendants
            ),
        )

        session.add(
            rule
        )

        new_rules.append(
            rule
        )

    session.flush()

    return new_rules


def get_allowed_storage_location_public_ids(
    session: Session,
    *,
    household_id: int,
    category_id: int,
) -> set[str]:
    """
    Visszaadja az adott kategóriában használható
    aktív tárhelyek public_id értékeit.
    """

    allowed_ids = (
        get_allowed_storage_location_ids(
            session=session,
            household_id=household_id,
            category_id=category_id,
        )
    )

    if not allowed_ids:
        return set()

    locations = session.scalars(
        select(StorageLocation).where(
            StorageLocation.id.in_(
                allowed_ids
            ),
            StorageLocation.is_active.is_(True),
        )
    ).all()

    return {
        location.public_id
        for location in locations
    }
