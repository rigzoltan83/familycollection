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


def update_primary_identifier(
    session: Session,
    legacy_book_id: int,
    *,
    identifier_type: str,
    identifier_value: str,
) -> bool:
    """
    Frissíti vagy létrehozza egy aktív könyv elsődleges
    azonosítóját a régi könyvazonosító alapján.

    A korábbi elsődleges azonosítók elvesztik az elsődleges
    jelölést. Ha már ugyanilyen aktív azonosító létezik,
    azt teszi elsődlegessé.

    Visszatérési érték:
    - True: a könyv megtalálható volt és frissült;
    - False: nincs ilyen aktív könyv.
    """
    cleaned_type = identifier_type.strip().lower()
    cleaned_value = identifier_value.strip()

    allowed_identifier_types = {
        "isbn10",
        "isbn13",
        "ean8",
        "ean13",
        "upc",
        "issn",
        "catalog_number",
        "provider_external_id",
        "custom",
        "qr",
        "rfid",
        "nfc",
    }

    if cleaned_type not in allowed_identifier_types:
        raise ValueError(
            "Nem támogatott azonosítótípus: "
            f"{cleaned_type or identifier_type}"
        )

    if not cleaned_value:
        raise ValueError(
            "Az azonosító értéke nem lehet üres."
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

    active_identifiers = session.scalars(
        select(ItemIdentifier).where(
            ItemIdentifier.item_id == item.id,
            ItemIdentifier.is_active.is_(True),
        )
    ).all()

    target_identifier = next(
        (
            identifier
            for identifier in active_identifiers
            if (
                identifier.identifier_type == cleaned_type
                and identifier.identifier_value == cleaned_value
            )
        ),
        None,
    )

    for identifier in active_identifiers:
        identifier.is_primary = False

    if target_identifier is None:
        target_identifier = ItemIdentifier(
            item_id=item.id,
            identifier_type=cleaned_type,
            identifier_value=cleaned_value,
            provider_code=None,
            is_primary=True,
            is_active=True,
        )

        session.add(target_identifier)
    else:
        target_identifier.is_primary = True

    migration.legacy_isbn = cleaned_value

    session.flush()

    return True


def update_book_metadata_fields(
    session: Session,
    legacy_book_id: int,
    *,
    author: str | None,
    publisher: str | None,
    publish_year: int | None,
) -> bool:
    """
    Frissíti egy aktív könyv dinamikus mezőit:

    - author
    - publisher
    - publish_year

    A None vagy üres szöveges érték törli a meglévő mezőértéket.
    A publish_year None értéke szintén törli az év mezőt.

    Visszatérési érték:
    - True: a könyv megtalálható volt és frissült;
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

    fields = {
        field.field_key: field
        for field in session.scalars(
            select(CategoryField).where(
                CategoryField.category_id == item.category_id,
                CategoryField.field_key.in_(
                    {
                        "author",
                        "publisher",
                        "publish_year",
                    }
                ),
                CategoryField.is_active.is_(True),
            )
        ).all()
    }

    required_field_keys = {
        "author",
        "publisher",
        "publish_year",
    }

    missing_field_keys = (
        required_field_keys
        - set(fields)
    )

    if missing_field_keys:
        raise ValueError(
            "Hiányzó könyvmezők: "
            + ", ".join(
                sorted(missing_field_keys)
            )
        )

    existing_values = {
        value.field_id: value
        for value in session.scalars(
            select(ItemFieldValue).where(
                ItemFieldValue.item_id == item.id,
                ItemFieldValue.field_id.in_(
                    [
                        field.id
                        for field in fields.values()
                    ]
                ),
            )
        ).all()
    }

    cleaned_author = (
        author.strip()
        if author is not None
        else None
    )

    cleaned_publisher = (
        publisher.strip()
        if publisher is not None
        else None
    )

    if cleaned_author == "":
        cleaned_author = None

    if cleaned_publisher == "":
        cleaned_publisher = None

    if publish_year is not None:
        if publish_year < 1000:
            raise ValueError(
                "A megjelenési év nem lehet kisebb mint 1000."
            )

        if publish_year > 9999:
            raise ValueError(
                "A megjelenési év nem lehet nagyobb mint 9999."
            )

    def set_text_value(
        field_key: str,
        value: str | None,
    ) -> None:
        field = fields[field_key]
        existing = existing_values.get(field.id)

        if value is None:
            if existing is not None:
                session.delete(existing)

            return

        if existing is None:
            session.add(
                ItemFieldValue(
                    item_id=item.id,
                    field_id=field.id,
                    value_text=value,
                )
            )

            return

        existing.value_text = value
        existing.value_integer = None
        existing.value_decimal = None
        existing.value_boolean = None
        existing.value_date = None
        existing.value_json = None

    def set_integer_value(
        field_key: str,
        value: int | None,
    ) -> None:
        field = fields[field_key]
        existing = existing_values.get(field.id)

        if value is None:
            if existing is not None:
                session.delete(existing)

            return

        if existing is None:
            session.add(
                ItemFieldValue(
                    item_id=item.id,
                    field_id=field.id,
                    value_integer=value,
                )
            )

            return

        existing.value_text = None
        existing.value_integer = value
        existing.value_decimal = None
        existing.value_boolean = None
        existing.value_date = None
        existing.value_json = None

    set_text_value(
        "author",
        cleaned_author,
    )

    set_text_value(
        "publisher",
        cleaned_publisher,
    )

    set_integer_value(
        "publish_year",
        publish_year,
    )

    session.flush()

    return True


def move_book_to_storage_location(
    session: Session,
    legacy_book_id: int,
    *,
    storage_location_id: int,
    moved_by_user_id: int | None = None,
    movement_reason: str = "book_update",
    notes: str | None = None,
) -> bool:
    """
    Áthelyez egy aktív könyvet egy másik tárolóhelyre.

    A korábbi aktív tárolási rekord lezárásra kerül, majd
    új aktív ItemStorageAssignment rekord jön létre.

    Visszatérési érték:
    - True: a könyv megtalálható volt és áthelyezésre került;
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

    target_location = session.get(
        StorageLocation,
        storage_location_id,
    )

    if target_location is None:
        raise ValueError(
            "A megadott tárolóhely nem létezik."
        )

    if not target_location.is_active:
        raise ValueError(
            "A megadott tárolóhely nem aktív."
        )

    if target_location.household_id != item.household_id:
        raise ValueError(
            "A tárolóhely nem ehhez a háztartáshoz tartozik."
        )

    if target_location.location_type != "slot":
        raise ValueError(
            "Könyv csak slot típusú tárolóhelyre helyezhető."
        )

    active_assignment = session.scalar(
        select(ItemStorageAssignment).where(
            ItemStorageAssignment.item_id == item.id,
            ItemStorageAssignment.is_active.is_(True),
        )
    )

    if (
        active_assignment is not None
        and active_assignment.storage_location_id
        == target_location.id
    ):
        return True

    now = datetime.now()

    if active_assignment is not None:
        active_assignment.is_active = False
        active_assignment.removed_at = now

    new_assignment = ItemStorageAssignment(
        item_id=item.id,
        storage_location_id=target_location.id,
        is_active=True,
        assigned_at=now,
        moved_by_user_id=moved_by_user_id,
        movement_reason=movement_reason.strip() or "book_update",
        notes=(
            notes.strip()
            if notes is not None and notes.strip()
            else None
        ),
    )

    session.add(new_assignment)

    shelf_location = target_location.parent

    room_location = (
        shelf_location.parent
        if shelf_location is not None
        else None
    )

    if shelf_location is None or room_location is None:
        raise ValueError(
            "A tárolóhely hierarchiája hiányos."
        )

    slot_number = _slot_number_from_location(
        target_location
    )

    if slot_number is None:
        raise ValueError(
            "A tárolóhely slot száma nem állapítható meg."
        )

    migration.legacy_location_id = None
    migration.legacy_room = room_location.name
    migration.legacy_shelf = shelf_location.name
    migration.legacy_slot = slot_number

    session.flush()

    return True
