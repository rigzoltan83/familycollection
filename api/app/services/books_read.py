"""
Kompatibilis könyvolvasó szolgáltatás az új CollectionItem modellhez.

A visszaadott adatszerkezet szándékosan követi a régi books API
mezőit, hogy a meglévő frontend változtatás nélkül használhassa.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import String, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    CategoryField,
    CollectionItem,
    ItemFieldValue,
    ItemIdentifier,
    ItemStorageAssignment,
    LegacyBookMigration,
    StorageLocation,
)


@dataclass(slots=True)
class BookReadRecord:
    id: int
    public_id: str
    isbn: str | None
    title: str
    author: str | None
    publisher: str | None
    year: int | None
    added: datetime | None
    updated: datetime | None
    location_id: int | None
    room: str | None
    shelf: str | None
    slot: int | None
    borrower: str | None
    status: str


@dataclass(slots=True)
class BookReadPage:
    page: int
    page_size: int
    total: int
    records: list[BookReadRecord]


def _extract_dynamic_fields(
    item: CollectionItem,
) -> dict[str, object]:
    values: dict[str, object] = {}

    for field_value in item.field_values:
        field_key = field_value.field.field_key

        value: object = None

        if field_value.value_text is not None:
            value = field_value.value_text
        elif field_value.value_integer is not None:
            value = field_value.value_integer
        elif field_value.value_decimal is not None:
            value = field_value.value_decimal
        elif field_value.value_boolean is not None:
            value = field_value.value_boolean
        elif field_value.value_date is not None:
            value = field_value.value_date
        elif field_value.value_json is not None:
            value = field_value.value_json

        values[field_key] = value

    return values


def _get_primary_identifier(
    item: CollectionItem,
) -> str | None:
    active_identifiers = [
        identifier
        for identifier in item.identifiers
        if identifier.is_active
    ]

    if not active_identifiers:
        return None

    primary_identifier = next(
        (
            identifier
            for identifier in active_identifiers
            if identifier.is_primary
        ),
        active_identifiers[0],
    )

    if primary_identifier.identifier_type == "issn":
        return f"ISSN {primary_identifier.identifier_value}"

    return primary_identifier.identifier_value


def _get_active_storage_assignment(
    item: CollectionItem,
) -> ItemStorageAssignment | None:
    return next(
        (
            assignment
            for assignment in item.storage_assignments
            if assignment.is_active
        ),
        None,
    )


def _slot_number_from_location(
    storage_location: StorageLocation | None,
) -> int | None:
    if storage_location is None:
        return None

    slug = storage_location.slug

    if not slug.startswith("slot-"):
        return None

    slot_value = slug.removeprefix("slot-")

    try:
        return int(slot_value)
    except ValueError:
        return None


def _build_book_record(
    migration: LegacyBookMigration,
) -> BookReadRecord:
    item = migration.collection_item

    if item is None:
        raise ValueError(
            "A migrációs naplóhoz nem tartozik gyűjteményi elem: "
            f"legacy_book_id={migration.legacy_book_id}"
        )

    dynamic_fields = _extract_dynamic_fields(item)

    assignment = _get_active_storage_assignment(item)

    slot_location = (
        assignment.storage_location
        if assignment is not None
        else None
    )

    shelf_location = (
        slot_location.parent
        if slot_location is not None
        else None
    )

    room_location = (
        shelf_location.parent
        if shelf_location is not None
        else None
    )

    publish_year = dynamic_fields.get("publish_year")

    normalized_year = (
        int(publish_year)
        if isinstance(publish_year, int)
        else None
    )

    return BookReadRecord(
        id=migration.legacy_book_id,
        public_id=item.public_id,
        isbn=_get_primary_identifier(item),
        title=item.title,
        author=(
            str(dynamic_fields["author"])
            if dynamic_fields.get("author") is not None
            else None
        ),
        publisher=(
            str(dynamic_fields["publisher"])
            if dynamic_fields.get("publisher") is not None
            else None
        ),
        year=normalized_year,
        added=item.created_at,
        updated=item.updated_at,
        location_id=migration.legacy_location_id,
        room=(
            room_location.name
            if room_location is not None
            else migration.legacy_room
        ),
        shelf=(
            shelf_location.name
            if shelf_location is not None
            else migration.legacy_shelf
        ),
        slot=(
            _slot_number_from_location(slot_location)
            or migration.legacy_slot
        ),
        borrower=migration.legacy_borrowed_to,
        status=item.status,
    )


def _book_loader_options():
    return (
        selectinload(
            LegacyBookMigration.collection_item
        ).selectinload(
            CollectionItem.identifiers
        ),
        selectinload(
            LegacyBookMigration.collection_item
        ).selectinload(
            CollectionItem.field_values
        ).selectinload(
            ItemFieldValue.field
        ),
        selectinload(
            LegacyBookMigration.collection_item
        ).selectinload(
            CollectionItem.storage_assignments
        ).selectinload(
            ItemStorageAssignment.storage_location
        ).selectinload(
            StorageLocation.parent
        ).selectinload(
            StorageLocation.parent
        ),
    )


def get_book_by_legacy_id(
    session: Session,
    legacy_book_id: int,
) -> BookReadRecord | None:
    migration = session.scalar(
        select(LegacyBookMigration)
        .options(*_book_loader_options())
        .join(
            CollectionItem,
            CollectionItem.id
            == LegacyBookMigration.collection_item_id,
        )
        .where(
            LegacyBookMigration.legacy_book_id
            == legacy_book_id,
            CollectionItem.is_active.is_(True),
        )
    )

    if migration is None:
        return None

    return _build_book_record(migration)


def list_latest_books(
    session: Session,
    *,
    limit: int = 20,
) -> list[BookReadRecord]:
    normalized_limit = max(1, min(limit, 100))

    migrations = session.scalars(
        select(LegacyBookMigration)
        .options(*_book_loader_options())
        .join(
            CollectionItem,
            CollectionItem.id
            == LegacyBookMigration.collection_item_id,
        )
        .where(
            CollectionItem.is_active.is_(True),
        )
        .order_by(
            CollectionItem.created_at.desc(),
            CollectionItem.id.desc(),
        )
        .limit(normalized_limit)
    ).all()

    return [
        _build_book_record(migration)
        for migration in migrations
    ]


def list_books(
    session: Session,
    *,
    page: int = 1,
    page_size: int = 50,
    search: str = "",
) -> BookReadPage:
    normalized_page = max(1, int(page))
    normalized_page_size = max(
        1,
        min(int(page_size), 100),
    )

    offset = (
        normalized_page - 1
    ) * normalized_page_size

    normalized_search = search.strip()

    filters = [
        CollectionItem.is_active.is_(True),
    ]

    if normalized_search:
        search_pattern = f"%{normalized_search}%"

        identifier_match = (
            select(ItemIdentifier.id)
            .where(
                ItemIdentifier.item_id
                == CollectionItem.id,
                ItemIdentifier.is_active.is_(True),
                ItemIdentifier.identifier_value.ilike(
                    search_pattern
                ),
            )
            .exists()
        )

        field_match = (
            select(ItemFieldValue.id)
            .join(
                CategoryField,
                CategoryField.id
                == ItemFieldValue.field_id,
            )
            .where(
                ItemFieldValue.item_id
                == CollectionItem.id,
                or_(
                    ItemFieldValue.value_text.ilike(
                        search_pattern
                    ),
                    func.cast(
                        ItemFieldValue.value_integer,
                        String,
                    ).ilike(search_pattern),
                ),
            )
            .exists()
        )

        filters.append(
            or_(
                CollectionItem.title.ilike(search_pattern),
                LegacyBookMigration.legacy_borrowed_to.ilike(
                    search_pattern
                ),
                LegacyBookMigration.legacy_room.ilike(
                    search_pattern
                ),
                LegacyBookMigration.legacy_shelf.ilike(
                    search_pattern
                ),
                func.cast(
                    LegacyBookMigration.legacy_slot,
                    String,
                ).ilike(search_pattern),
                identifier_match,
                field_match,
            )
        )

    base_query = (
        select(LegacyBookMigration)
        .join(
            CollectionItem,
            CollectionItem.id
            == LegacyBookMigration.collection_item_id,
        )
        .where(*filters)
    )

    total = session.scalar(
        select(func.count())
        .select_from(base_query.subquery())
    )

    migrations = session.scalars(
        base_query
        .options(*_book_loader_options())
        .order_by(
            CollectionItem.title.asc(),
            LegacyBookMigration.legacy_book_id.asc(),
        )
        .limit(normalized_page_size)
        .offset(offset)
    ).all()

    return BookReadPage(
        page=normalized_page,
        page_size=normalized_page_size,
        total=int(total or 0),
        records=[
            _build_book_record(migration)
            for migration in migrations
        ],
    )

def soft_delete_book_by_legacy_id(
    session: Session,
    legacy_book_id: int,
) -> bool:
    """
    A régi könyvazonosító alapján soft delete-eli
    a kapcsolódó CollectionItem rekordot.

    Visszatérési érték:
    - True: a könyv aktív volt és törlésre került;
    - False: nincs ilyen aktív könyv.
    """
    migration = session.scalar(
        select(LegacyBookMigration)
        .join(
            CollectionItem,
            CollectionItem.id
            == LegacyBookMigration.collection_item_id,
        )
        .where(
            LegacyBookMigration.legacy_book_id
            == legacy_book_id,
            CollectionItem.is_active.is_(True),
        )
    )

    if migration is None:
        return False

    item = migration.collection_item

    if item is None:
        return False

    item.is_active = False
    session.flush()

    return True

def update_collection_item_title(
    session: Session,
    legacy_book_id: int,
    title: str,
) -> bool:
    """
    Frissíti a CollectionItem címét a legacy könyvazonosító alapján.
    """

    migration = session.scalar(
        select(LegacyBookMigration)
        .join(
            CollectionItem,
            CollectionItem.id
            == LegacyBookMigration.collection_item_id,
        )
        .where(
            LegacyBookMigration.legacy_book_id
            == legacy_book_id,
            CollectionItem.is_active.is_(True),
        )
    )

    if migration is None:
        return False

    item = migration.collection_item

    if item is None:
        return False

    item.title = title.strip()

    session.flush()

    return True


def update_collection_item_title(
    session: Session,
    legacy_book_id: int,
    title: str,
) -> bool:
    """
    Frissíti az aktív CollectionItem címét
    a régi könyvazonosító alapján.

    Visszatérési érték:
    - True: a könyv megtalálható volt és frissült;
    - False: nincs ilyen aktív könyv.
    """
    cleaned_title = title.strip()

    if not cleaned_title:
        raise ValueError(
            "A cím nem lehet üres."
        )

    migration = session.scalar(
        select(LegacyBookMigration)
        .join(
            CollectionItem,
            CollectionItem.id
            == LegacyBookMigration.collection_item_id,
        )
        .where(
            LegacyBookMigration.legacy_book_id
            == legacy_book_id,
            CollectionItem.is_active.is_(True),
        )
    )

    if migration is None:
        return False

    item = migration.collection_item

    if item is None:
        return False

    item.title = cleaned_title

    session.flush()

    return True
