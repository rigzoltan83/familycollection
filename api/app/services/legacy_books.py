"""
Régi books rekordok migrációját előkészítő segédfüggvények.

Ez a modul egyelőre csak:

- a forrásadatokat normalizálja;
- azonosítótípust állapít meg;
- megjelenési évet értelmez;
- figyelmeztetéseket gyűjt.

Adatbázisba még nem ír.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models import (
    Category,
    CollectionItem,
    ItemStorageAssignment,
    LegacyBookMigration,
    StorageLocation,
)
from app.services.collection_items import (
    CollectionItemCreateInput,
    IdentifierInput,
    create_collection_item,
)

@dataclass(slots=True)
class LegacyBookSource:
    legacy_book_id: int
    isbn: str | None
    title: str | None
    author: str | None
    publisher: str | None
    publish_year: str | None
    location_id: int | None
    borrowed_to: str | None
    created: datetime | None
    updated: datetime | None


@dataclass(slots=True)
class LegacyLocationSource:
    legacy_location_id: int
    room: str
    shelf: str
    slot: int


@dataclass(slots=True)
class LegacyBookMigrationResult:
    migration: LegacyBookMigration
    item: CollectionItem
    created: bool


@dataclass(slots=True)
class LegacyBookBatchError:
    legacy_book_id: int
    message: str


@dataclass(slots=True)
class LegacyBookBatchResult:
    total_source_records: int = 0
    created_count: int = 0
    skipped_count: int = 0
    migrated_count: int = 0
    warning_count: int = 0
    error_count: int = 0
    errors: list[LegacyBookBatchError] = field(
        default_factory=list
    )


@dataclass(slots=True)
class NormalizedLegacyIdentifier:
    identifier_type: str
    identifier_value: str


@dataclass(slots=True)
class PreparedLegacyBook:
    legacy_book_id: int
    title: str
    author: str | None
    publisher: str | None
    publish_year: int | None
    identifier: NormalizedLegacyIdentifier | None
    legacy_isbn: str | None
    legacy_location_id: int | None
    legacy_borrowed_to: str | None
    created_at: datetime | None
    updated_at: datetime | None
    warnings: list[str] = field(default_factory=list)


def _clean_optional_text(
    value: str | None,
) -> str | None:
    if value is None:
        return None

    cleaned = value.strip()

    return cleaned or None


def normalize_legacy_identifier(
    value: str | None,
) -> NormalizedLegacyIdentifier | None:
    """
    A régi isbn mezőből ItemIdentifier-kompatibilis értéket készít.

    Szabályok:

    - X vagy üres: nincs azonosító;
    - ISSN kezdetű érték: issn;
    - MSZ kezdetű érték: custom;
    - 10 karakteres normalizált érték: isbn10;
    - 13 karakteres normalizált érték: isbn13;
    - minden más nem üres érték: custom.
    """
    cleaned = _clean_optional_text(value)

    if cleaned is None:
        return None

    if cleaned.upper() == "X":
        return None

    upper_value = cleaned.upper()

    if upper_value.startswith("ISSN"):
        issn_value = re.sub(
            r"^ISSN\s*",
            "",
            cleaned,
            flags=re.IGNORECASE,
        ).strip()

        return NormalizedLegacyIdentifier(
            identifier_type="issn",
            identifier_value=issn_value,
        )

    if upper_value.startswith("MSZ"):
        normalized_custom = re.sub(
            r"\s+",
            " ",
            cleaned,
        )

        return NormalizedLegacyIdentifier(
            identifier_type="custom",
            identifier_value=normalized_custom,
        )

    compact_value = re.sub(
        r"[^0-9Xx]",
        "",
        cleaned,
    ).upper()

    if len(compact_value) == 10:
        return NormalizedLegacyIdentifier(
            identifier_type="isbn10",
            identifier_value=compact_value,
        )

    if len(compact_value) == 13:
        return NormalizedLegacyIdentifier(
            identifier_type="isbn13",
            identifier_value=compact_value,
        )

    return NormalizedLegacyIdentifier(
        identifier_type="custom",
        identifier_value=cleaned,
    )


def normalize_publish_year(
    value: str | None,
) -> tuple[int | None, str | None]:
    """
    Megjelenési év normalizálása.

    Visszatérési érték:

    - normalizált év vagy None;
    - opcionális figyelmeztetés.
    """
    cleaned = _clean_optional_text(value)

    if cleaned is None:
        return None, None

    if not re.fullmatch(r"[0-9]{4}", cleaned):
        return (
            None,
            f"Érvénytelen megjelenési év: {cleaned}",
        )

    year = int(cleaned)

    if year < 1000 or year > 9999:
        return (
            None,
            f"Tartományon kívüli megjelenési év: {cleaned}",
        )

    return year, None


def prepare_legacy_book(
    source: LegacyBookSource,
) -> PreparedLegacyBook:
    """
    Egy régi books rekord normalizálása migrációhoz.
    """
    warnings: list[str] = []

    title = _clean_optional_text(source.title)

    if title is None:
        raise ValueError(
            f"A régi könyv címe üres: books.id={source.legacy_book_id}"
        )

    author = _clean_optional_text(source.author)
    publisher = _clean_optional_text(source.publisher)

    publish_year, year_warning = normalize_publish_year(
        source.publish_year
    )

    if year_warning is not None:
        warnings.append(year_warning)

    identifier = normalize_legacy_identifier(
        source.isbn
    )

    cleaned_legacy_isbn = _clean_optional_text(
        source.isbn
    )

    if (
        cleaned_legacy_isbn is not None
        and cleaned_legacy_isbn.upper() == "X"
    ):
        warnings.append(
            "Az X helykitöltő ISBN nem került azonosítóként migrálásra."
        )

    return PreparedLegacyBook(
        legacy_book_id=source.legacy_book_id,
        title=title,
        author=author,
        publisher=publisher,
        publish_year=publish_year,
        identifier=identifier,
        legacy_isbn=cleaned_legacy_isbn,
        legacy_location_id=source.location_id,
        legacy_borrowed_to=_clean_optional_text(
            source.borrowed_to
        ),
        created_at=source.created,
        updated_at=source.updated,
        warnings=warnings,
    )

def _slugify_legacy_location_part(
    value: str,
) -> str:
    """
    Ugyanazt a sluglogikát használja, mint a legacy
    storage-location seed migráció.
    """
    import unicodedata

    normalized = unicodedata.normalize(
        "NFKD",
        value.strip(),
    )

    ascii_value = "".join(
        character
        for character in normalized
        if not unicodedata.combining(character)
    )

    slug = re.sub(
        r"[^a-zA-Z0-9]+",
        "-",
        ascii_value,
    ).strip("-").lower()

    return slug or "location"


def _find_legacy_storage_location(
    session: Session,
    *,
    household_id: int,
    location: LegacyLocationSource,
) -> StorageLocation:
    room_slug = _slugify_legacy_location_part(
        location.room
    )

    shelf_slug = _slugify_legacy_location_part(
        location.shelf
    )

    slot_slug = f"slot-{location.slot}"

    room = session.scalar(
        select(StorageLocation).where(
            StorageLocation.household_id == household_id,
            StorageLocation.parent_id.is_(None),
            StorageLocation.slug == room_slug,
            StorageLocation.is_active.is_(True),
        )
    )

    if room is None:
        raise ValueError(
            "A régi tárolóhely helyisége nem található: "
            f"{location.room}"
        )

    shelf = session.scalar(
        select(StorageLocation).where(
            StorageLocation.household_id == household_id,
            StorageLocation.parent_id == room.id,
            StorageLocation.slug == shelf_slug,
            StorageLocation.is_active.is_(True),
        )
    )

    if shelf is None:
        raise ValueError(
            "A régi tárolóhely polca nem található: "
            f"{location.room} / {location.shelf}"
        )

    slot = session.scalar(
        select(StorageLocation).where(
            StorageLocation.household_id == household_id,
            StorageLocation.parent_id == shelf.id,
            StorageLocation.slug == slot_slug,
            StorageLocation.is_active.is_(True),
        )
    )

    if slot is None:
        raise ValueError(
            "A régi tárolóhely rekesze nem található: "
            f"{location.room} / {location.shelf} / "
            f"{location.slot}"
        )

    return slot


def _get_existing_legacy_migration(
    session: Session,
    legacy_book_id: int,
) -> LegacyBookMigration | None:
    return session.scalar(
        select(LegacyBookMigration).where(
            LegacyBookMigration.legacy_book_id
            == legacy_book_id
        )
    )


def migrate_legacy_book(
    session: Session,
    *,
    source: LegacyBookSource,
    location: LegacyLocationSource,
    household_id: int,
    category_id: int,
) -> LegacyBookMigrationResult:
    """
    Egyetlen régi books rekord átmigrálása.

    A hívó kezeli a commitot vagy rollbacket.
    A művelet legacy_book_id alapján idempotens.
    """
    existing_migration = _get_existing_legacy_migration(
        session=session,
        legacy_book_id=source.legacy_book_id,
    )

    if existing_migration is not None:
        if existing_migration.collection_item is None:
            raise ValueError(
                "A meglévő migrációs naplóhoz nem tartozik "
                "gyűjteményi elem."
            )

        return LegacyBookMigrationResult(
            migration=existing_migration,
            item=existing_migration.collection_item,
            created=False,
        )

    prepared = prepare_legacy_book(source)

    category = session.get(Category, category_id)

    if category is None:
        raise ValueError(
            "A migrációhoz megadott kategória nem létezik."
        )

    if category.slug != "book":
        raise ValueError(
            "A legacy könyvek csak a book kategóriába "
            "migrálhatók."
        )

    storage_location = _find_legacy_storage_location(
        session=session,
        household_id=household_id,
        location=location,
    )

    identifiers: list[IdentifierInput] = []

    if prepared.identifier is not None:
        identifiers.append(
            IdentifierInput(
                identifier_type=(
                    prepared.identifier.identifier_type
                ),
                identifier_value=(
                    prepared.identifier.identifier_value
                ),
                provider_code=None,
                is_primary=True,
            )
        )

    field_values: dict[str, object] = {}

    if prepared.author is not None:
        field_values["author"] = prepared.author

    if prepared.publisher is not None:
        field_values["publisher"] = prepared.publisher

    if prepared.publish_year is not None:
        field_values["publish_year"] = (
            prepared.publish_year
        )

    item_status = (
        "loaned"
        if prepared.legacy_borrowed_to is not None
        else "active"
    )

    item = create_collection_item(
        session=session,
        data=CollectionItemCreateInput(
            household_id=household_id,
            category_id=category_id,
            title=prepared.title,
            status=item_status,
            identifiers=identifiers,
            field_values=field_values,
        ),
    )

    if prepared.created_at is not None:
        item.created_at = prepared.created_at

    if prepared.updated_at is not None:
        item.updated_at = prepared.updated_at

    storage_assignment = ItemStorageAssignment(
        item=item,
        storage_location=storage_location,
        is_active=True,
        assigned_at=(
            prepared.created_at
            if prepared.created_at is not None
            else datetime.now()
        ),
        movement_reason="legacy_book_migration",
        notes=(
            "A régi books és locations táblákból "
            "automatikusan létrehozott tárolási rekord."
        ),
    )

    session.add(storage_assignment)

    migration_status = (
        "warning"
        if prepared.warnings
        else "migrated"
    )

    migration_notes = (
        "\n".join(prepared.warnings)
        if prepared.warnings
        else None
    )

    migration = LegacyBookMigration(
        legacy_book_id=prepared.legacy_book_id,
        collection_item=item,
        legacy_location_id=(
            prepared.legacy_location_id
        ),
        legacy_isbn=prepared.legacy_isbn,
        legacy_borrowed_to=(
            prepared.legacy_borrowed_to
        ),
        legacy_room=location.room.strip(),
        legacy_shelf=location.shelf.strip(),
        legacy_slot=location.slot,
        migration_status=migration_status,
        migration_notes=migration_notes,
    )

    session.add(migration)
    session.flush()

    return LegacyBookMigrationResult(
        migration=migration,
        item=item,
        created=True,
    )

def load_legacy_book_sources_from_database(
    session: Session,
) -> list[tuple[LegacyBookSource, LegacyLocationSource]]:
    """
    A régi books és locations táblákból betölti a migrációhoz
    szükséges forrásrekordokat.

    Ez adatforrás-adapter, nem része a batch migráció üzleti
    logikájának.
    """
    rows = session.execute(
        text(
            """
            SELECT
                b.id AS legacy_book_id,
                b.isbn,
                b.title,
                b.author,
                b.publisher,
                b.publish_year,
                b.location_id,
                b.borrowed_to,
                b.created,
                b.updated,
                l.room,
                l.shelf,
                l.slot
            FROM books AS b
            LEFT JOIN locations AS l
                ON l.id = b.location_id
            ORDER BY b.id
            """
        )
    ).mappings().all()

    result: list[
        tuple[LegacyBookSource, LegacyLocationSource]
    ] = []

    for row in rows:
        legacy_book_id = int(row["legacy_book_id"])

        if row["location_id"] is None:
            raise ValueError(
                "A régi könyvhöz nem tartozik tárolóhely: "
                f"books.id={legacy_book_id}"
            )

        if (
            row["room"] is None
            or row["shelf"] is None
            or row["slot"] is None
        ):
            raise ValueError(
                "A régi könyv tárolóhelye nem található: "
                f"books.id={legacy_book_id}, "
                f"location_id={row['location_id']}"
            )

        source = LegacyBookSource(
            legacy_book_id=legacy_book_id,
            isbn=row["isbn"],
            title=row["title"],
            author=row["author"],
            publisher=row["publisher"],
            publish_year=row["publish_year"],
            location_id=int(row["location_id"]),
            borrowed_to=row["borrowed_to"],
            created=row["created"],
            updated=row["updated"],
        )

        location = LegacyLocationSource(
            legacy_location_id=int(row["location_id"]),
            room=str(row["room"]),
            shelf=str(row["shelf"]),
            slot=int(row["slot"]),
        )

        result.append(
            (
                source,
                location,
            )
        )

    return result


def migrate_legacy_books_batch(
    session: Session,
    *,
    source_records: list[
        tuple[LegacyBookSource, LegacyLocationSource]
    ],
    household_id: int,
    category_id: int,
    continue_on_error: bool = True,
) -> LegacyBookBatchResult:
    """
    Előkészített legacy könyvrekordok batch migrációja.

    A forrásadatok beolvasása nem ennek a függvénynek a feladata.
    Így a migrációs logika adatbázistól, CSV-től vagy más
    adatforrástól függetlenül tesztelhető.

    Könyvenként külön SAVEPOINT-ot használ, ezért egy hibás rekord
    nem teszi tönkre a teljes batch-et.

    A hívó kezeli a végső commitot vagy rollbacket.
    """
    result = LegacyBookBatchResult(
        total_source_records=len(source_records)
    )

    for source, location in source_records:
        try:
            with session.begin_nested():
                migration_result = migrate_legacy_book(
                    session=session,
                    source=source,
                    location=location,
                    household_id=household_id,
                    category_id=category_id,
                )

                if migration_result.created:
                    result.created_count += 1
                else:
                    result.skipped_count += 1

                migration_status = (
                    migration_result.migration.migration_status
                )

                if migration_status == "warning":
                    result.warning_count += 1
                elif migration_status == "migrated":
                    result.migrated_count += 1

        except Exception as error:
            result.error_count += 1

            result.errors.append(
                LegacyBookBatchError(
                    legacy_book_id=source.legacy_book_id,
                    message=str(error),
                )
            )

            if not continue_on_error:
                raise

    return result
