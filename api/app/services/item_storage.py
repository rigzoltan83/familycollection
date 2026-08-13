"""
Generikus CollectionItem tárhely-hozzárendelási műveletek.

A gyűjteményi elemek aktuális fizikai helyét az
ItemStorageAssignment történeti tábla kezeli.

Egy elemhez egyszerre legfeljebb egy aktív
tárhely-hozzárendelés tartozhat.
"""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    CollectionItem,
    ItemStorageAssignment,
    StorageLocation,
)

from app.services.category_storage import (
    is_storage_location_allowed,
)

def get_active_item_storage_assignment(
    session: Session,
    *,
    item_id: int,
) -> ItemStorageAssignment | None:
    """
    Visszaadja az elem jelenlegi aktív
    tárhely-hozzárendelását.
    """
    return session.scalar(
        select(ItemStorageAssignment).where(
            ItemStorageAssignment.item_id == item_id,
            ItemStorageAssignment.is_active.is_(True),
        )
    )


def set_item_storage_location(
    session: Session,
    *,
    item: CollectionItem,
    storage_public_id: str | None,
    moved_by_user_id: int | None = None,
    movement_reason: str = "item_update",
    notes: str | None = None,
) -> ItemStorageAssignment | None:
    """
    Beállítja egy CollectionItem aktuális tárolási helyét.

    Ha már másik aktív helyen van:
    - a korábbi assignment lezárásra kerül;
    - új aktív assignment jön létre.

    Ha ugyanazt a helyet kapja újra:
    - nem készül új történeti rekord.

    Ha storage_public_id None:
    - a jelenlegi aktív assignment lezárásra kerül;
    - új assignment nem készül.

    Új célhelyként csak:
    - létező;
    - aktív;
    - ugyanahhoz a háztartáshoz tartozó;
    - az elem kategóriájához engedélyezett
    tárhely használható.
    """
    active_assignment = get_active_item_storage_assignment(
        session=session,
        item_id=item.id,
    )

    if storage_public_id is None:
        if active_assignment is None:
            return None

        active_assignment.is_active = False
        active_assignment.removed_at = (
            datetime.now()
        )

        session.flush()

        return None

    normalized_public_id = (
        storage_public_id.strip()
    )

    if not normalized_public_id:
        raise ValueError(
            "A tárhely azonosítója nem lehet üres."
        )

    target_location = session.scalar(
        select(StorageLocation).where(
            StorageLocation.public_id
            == normalized_public_id
        )
    )

    if target_location is None:
        raise ValueError(
            "A megadott tárolóhely nem létezik."
        )

    if not target_location.is_active:
        raise ValueError(
            "A megadott tárolóhely nem aktív."
        )

    if (
        target_location.household_id
        != item.household_id
    ):
        raise ValueError(
            "A tárolóhely nem ehhez "
            "a háztartáshoz tartozik."
        )

    if not is_storage_location_allowed(
        session=session,
        household_id=item.household_id,
        category_id=item.category_id,
        storage_location_id=target_location.id,
    ):
        raise ValueError(
            "A megadott tárolóhely "
            "nem engedélyezett ehhez "
            "a kategóriához."
        )

    if (
        active_assignment is not None
        and active_assignment.storage_location_id
        == target_location.id
    ):
        return active_assignment

    now = datetime.now()

    if active_assignment is not None:
        active_assignment.is_active = False
        active_assignment.removed_at = now

    normalized_reason = (
        movement_reason.strip()
    )

    if not normalized_reason:
        normalized_reason = "item_update"

    normalized_notes = (
        notes.strip()
        if notes is not None
        and notes.strip()
        else None
    )

    new_assignment = ItemStorageAssignment(
        item=item,
        storage_location=target_location,
        is_active=True,
        assigned_at=now,
        moved_by_user_id=moved_by_user_id,
        movement_reason=normalized_reason,
        notes=normalized_notes,
    )

    session.add(
        new_assignment
    )

    session.flush()

    return new_assignment
