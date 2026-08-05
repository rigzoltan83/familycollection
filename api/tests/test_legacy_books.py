from datetime import datetime

import pytest

from app.services import (
    LegacyBookSource,
    normalize_legacy_identifier,
    normalize_publish_year,
    prepare_legacy_book,
    LegacyLocationSource,
    migrate_legacy_book,
    migrate_legacy_books_batch,
)

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    Category,
    CategoryField,
    CollectionItem,
    Household,
    ItemFieldValue,
    ItemIdentifier,
    ItemStorageAssignment,
    LegacyBookMigration,
    StorageLocation,
)


def test_normalize_isbn13() -> None:
    identifier = normalize_legacy_identifier(
        "978-963-369-450-3"
    )

    assert identifier is not None
    assert identifier.identifier_type == "isbn13"
    assert identifier.identifier_value == "9789633694503"


def test_normalize_isbn10() -> None:
    identifier = normalize_legacy_identifier(
        "963 11 5174 3"
    )

    assert identifier is not None
    assert identifier.identifier_type == "isbn10"
    assert identifier.identifier_value == "9631151743"


def test_normalize_issn() -> None:
    identifier = normalize_legacy_identifier(
        "ISSN 3103-4152"
    )

    assert identifier is not None
    assert identifier.identifier_type == "issn"
    assert identifier.identifier_value == "3103-4152"


def test_normalize_msz_as_custom() -> None:
    identifier = normalize_legacy_identifier(
        "MSZ 5601-59"
    )

    assert identifier is not None
    assert identifier.identifier_type == "custom"
    assert identifier.identifier_value == "MSZ 5601-59"


def test_placeholder_x_does_not_create_identifier() -> None:
    assert normalize_legacy_identifier("X") is None
    assert normalize_legacy_identifier(" x ") is None


def test_normalize_valid_publish_year() -> None:
    year, warning = normalize_publish_year(" 2007 ")

    assert year == 2007
    assert warning is None


def test_prepare_legacy_book() -> None:
    created = datetime(2026, 7, 14, 8, 53, 42)
    updated = datetime(2026, 7, 14, 8, 54, 22)

    prepared = prepare_legacy_book(
        LegacyBookSource(
            legacy_book_id=6,
            isbn="9789633694503",
            title=" A három testőr Afrikában ",
            author=" Jenő Rejtő ",
            publisher=" Alexandra K. ",
            publish_year="2007",
            location_id=5,
            borrowed_to="",
            created=created,
            updated=updated,
        )
    )

    assert prepared.legacy_book_id == 6
    assert prepared.title == "A három testőr Afrikában"
    assert prepared.author == "Jenő Rejtő"
    assert prepared.publisher == "Alexandra K."
    assert prepared.publish_year == 2007
    assert prepared.legacy_location_id == 5
    assert prepared.legacy_borrowed_to is None
    assert prepared.created_at == created
    assert prepared.updated_at == updated
    assert prepared.warnings == []

    assert prepared.identifier is not None
    assert prepared.identifier.identifier_type == "isbn13"
    assert prepared.identifier.identifier_value == "9789633694503"


def test_prepare_placeholder_x_adds_warning() -> None:
    prepared = prepare_legacy_book(
        LegacyBookSource(
            legacy_book_id=265,
            isbn="X",
            title="Grimm mesék",
            author=None,
            publisher=None,
            publish_year=None,
            location_id=1,
            borrowed_to=None,
            created=None,
            updated=None,
        )
    )

    assert prepared.identifier is None
    assert len(prepared.warnings) == 1
    assert "helykitöltő ISBN" in prepared.warnings[0]


def test_prepare_rejects_empty_title() -> None:
    with pytest.raises(
        ValueError,
        match="A régi könyv címe üres",
    ):
        prepare_legacy_book(
            LegacyBookSource(
                legacy_book_id=999,
                isbn="9789630000000",
                title="   ",
                author=None,
                publisher=None,
                publish_year=None,
                location_id=None,
                borrowed_to=None,
                created=None,
                updated=None,
            )
        )

def create_test_household(
    session: Session,
) -> Household:
    household = Household(
        name="Legacy migrációs teszt",
        slug="legacy-migration-test",
        is_active=True,
    )

    session.add(household)
    session.flush()

    return household


def create_test_book_category(
    session: Session,
) -> Category:
    category = Category(
        household_id=None,
        name="Könyv",
        slug="book",
        description="Legacy migrációs könyvkategória",
        icon="book",
        is_system=True,
        is_active=True,
        supports_barcode=True,
        metadata_lookup_type="manual",
        sort_order=10,
    )

    session.add(category)
    session.flush()

    session.add_all(
        [
            CategoryField(
                category_id=category.id,
                name="Szerző",
                field_key="author",
                field_type="text",
                is_required=False,
                is_searchable=True,
                is_filterable=False,
                is_visible_in_list=True,
                is_active=True,
                sort_order=10,
                validation_rules={},
                default_value={},
            ),
            CategoryField(
                category_id=category.id,
                name="Kiadó",
                field_key="publisher",
                field_type="text",
                is_required=False,
                is_searchable=True,
                is_filterable=True,
                is_visible_in_list=False,
                is_active=True,
                sort_order=20,
                validation_rules={},
                default_value={},
            ),
            CategoryField(
                category_id=category.id,
                name="Megjelenési év",
                field_key="publish_year",
                field_type="year",
                is_required=False,
                is_searchable=False,
                is_filterable=True,
                is_visible_in_list=True,
                is_active=True,
                sort_order=30,
                validation_rules={
                    "minimum": 1000,
                    "maximum": 9999,
                },
                default_value={},
            ),
        ]
    )

    session.flush()

    return category


def create_test_storage_hierarchy(
    session: Session,
    *,
    household_id: int,
) -> StorageLocation:
    room = StorageLocation(
        household_id=household_id,
        parent_id=None,
        name="Nappali",
        slug="nappali",
        location_type="room",
        sort_order=10,
        is_active=True,
    )

    session.add(room)
    session.flush()

    shelf = StorageLocation(
        household_id=household_id,
        parent_id=room.id,
        name="Újpolc",
        slug="ujpolc",
        location_type="shelf",
        sort_order=10,
        is_active=True,
    )

    session.add(shelf)
    session.flush()

    slot = StorageLocation(
        household_id=household_id,
        parent_id=shelf.id,
        name="5. hely",
        slug="slot-5",
        location_type="slot",
        sort_order=50,
        is_active=True,
    )

    session.add(slot)
    session.flush()

    return slot


def test_migrate_legacy_book_creates_complete_item(
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_test_book_category(db_session)

    storage_location = create_test_storage_hierarchy(
        db_session,
        household_id=household.id,
    )

    created_at = datetime(2026, 7, 14, 8, 53, 42)
    updated_at = datetime(2026, 7, 14, 8, 54, 22)

    result = migrate_legacy_book(
        session=db_session,
        source=LegacyBookSource(
            legacy_book_id=6,
            isbn="9789633694503",
            title="A három testőr Afrikában",
            author="Jenő Rejtő",
            publisher="Alexandra K.",
            publish_year="2007",
            location_id=5,
            borrowed_to=None,
            created=created_at,
            updated=updated_at,
        ),
        location=LegacyLocationSource(
            legacy_location_id=5,
            room="Nappali",
            shelf="Újpolc",
            slot=5,
        ),
        household_id=household.id,
        category_id=category.id,
    )

    assert result.created is True
    assert result.item.id is not None
    assert result.migration.id is not None

    item = db_session.get(
        CollectionItem,
        result.item.id,
    )

    assert item is not None
    assert item.title == "A három testőr Afrikában"
    assert item.status == "active"
    assert item.household_id == household.id
    assert item.category_id == category.id
    assert item.created_at == created_at
    assert item.updated_at == updated_at

    identifier = db_session.scalar(
        select(ItemIdentifier).where(
            ItemIdentifier.item_id == item.id
        )
    )

    assert identifier is not None
    assert identifier.identifier_type == "isbn13"
    assert identifier.identifier_value == "9789633694503"
    assert identifier.is_primary is True

    values = db_session.scalars(
        select(ItemFieldValue).where(
            ItemFieldValue.item_id == item.id
        )
    ).all()

    values_by_key = {
        value.field.field_key: value
        for value in values
    }

    assert len(values) == 3
    assert values_by_key["author"].value_text == "Jenő Rejtő"
    assert values_by_key["publisher"].value_text == "Alexandra K."
    assert values_by_key["publish_year"].value_integer == 2007

    assignment = db_session.scalar(
        select(ItemStorageAssignment).where(
            ItemStorageAssignment.item_id == item.id,
            ItemStorageAssignment.is_active.is_(True),
        )
    )

    assert assignment is not None
    assert assignment.storage_location_id == storage_location.id
    assert assignment.assigned_at == created_at
    assert assignment.movement_reason == "legacy_book_migration"

    migration = db_session.scalar(
        select(LegacyBookMigration).where(
            LegacyBookMigration.legacy_book_id == 6
        )
    )

    assert migration is not None
    assert migration.collection_item_id == item.id
    assert migration.legacy_location_id == 5
    assert migration.legacy_isbn == "9789633694503"
    assert migration.legacy_room == "Nappali"
    assert migration.legacy_shelf == "Újpolc"
    assert migration.legacy_slot == 5
    assert migration.migration_status == "migrated"
    assert migration.migration_notes is None


def test_migrate_legacy_book_is_idempotent(
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_test_book_category(db_session)

    create_test_storage_hierarchy(
        db_session,
        household_id=household.id,
    )

    source = LegacyBookSource(
        legacy_book_id=6,
        isbn="9789633694503",
        title="A három testőr Afrikában",
        author="Jenő Rejtő",
        publisher="Alexandra K.",
        publish_year="2007",
        location_id=5,
        borrowed_to=None,
        created=None,
        updated=None,
    )

    location = LegacyLocationSource(
        legacy_location_id=5,
        room="Nappali",
        shelf="Újpolc",
        slot=5,
    )

    first_result = migrate_legacy_book(
        session=db_session,
        source=source,
        location=location,
        household_id=household.id,
        category_id=category.id,
    )

    second_result = migrate_legacy_book(
        session=db_session,
        source=source,
        location=location,
        household_id=household.id,
        category_id=category.id,
    )

    assert first_result.created is True
    assert second_result.created is False
    assert second_result.item.id == first_result.item.id
    assert second_result.migration.id == first_result.migration.id

    item_count = db_session.scalar(
        select(func.count(CollectionItem.id)).where(
            CollectionItem.household_id == household.id
        )
    )

    migration_count = db_session.scalar(
        select(func.count(LegacyBookMigration.id)).where(
            LegacyBookMigration.legacy_book_id == 6
        )
    )

    assert item_count == 1
    assert migration_count == 1


def test_migrate_placeholder_x_creates_warning_without_identifier(
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_test_book_category(db_session)

    create_test_storage_hierarchy(
        db_session,
        household_id=household.id,
    )

    result = migrate_legacy_book(
        session=db_session,
        source=LegacyBookSource(
            legacy_book_id=265,
            isbn="X",
            title="Grimm mesék",
            author=None,
            publisher=None,
            publish_year=None,
            location_id=5,
            borrowed_to=None,
            created=None,
            updated=None,
        ),
        location=LegacyLocationSource(
            legacy_location_id=5,
            room="Nappali",
            shelf="Újpolc",
            slot=5,
        ),
        household_id=household.id,
        category_id=category.id,
    )

    identifier = db_session.scalar(
        select(ItemIdentifier).where(
            ItemIdentifier.item_id == result.item.id
        )
    )

    assert identifier is None
    assert result.migration.migration_status == "warning"
    assert result.migration.migration_notes is not None
    assert "helykitöltő ISBN" in result.migration.migration_notes


def test_migrate_legacy_books_batch_creates_all_records(
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_test_book_category(db_session)

    create_test_storage_hierarchy(
        db_session,
        household_id=household.id,
    )

    source_records = [
        (
            LegacyBookSource(
                legacy_book_id=1001,
                isbn="9789633694503",
                title="A három testőr Afrikában",
                author="Jenő Rejtő",
                publisher="Alexandra K.",
                publish_year="2007",
                location_id=5,
                borrowed_to=None,
                created=None,
                updated=None,
            ),
            LegacyLocationSource(
                legacy_location_id=5,
                room="Nappali",
                shelf="Újpolc",
                slot=5,
            ),
        ),
        (
            LegacyBookSource(
                legacy_book_id=1002,
                isbn="9631151743",
                title="Minden napra egy kérdés",
                author="László S. Tóth",
                publisher="Móra",
                publish_year="1987",
                location_id=5,
                borrowed_to="Teszt kölcsönző",
                created=None,
                updated=None,
            ),
            LegacyLocationSource(
                legacy_location_id=5,
                room="Nappali",
                shelf="Újpolc",
                slot=5,
            ),
        ),
    ]

    result = migrate_legacy_books_batch(
        session=db_session,
        source_records=source_records,
        household_id=household.id,
        category_id=category.id,
    )

    assert result.total_source_records == 2
    assert result.created_count == 2
    assert result.skipped_count == 0
    assert result.migrated_count == 2
    assert result.warning_count == 0
    assert result.error_count == 0
    assert result.errors == []

    migrated_legacy_ids = set(
        db_session.scalars(
            select(
                LegacyBookMigration.legacy_book_id
            ).order_by(
                LegacyBookMigration.legacy_book_id
            )
        ).all()
    )

    assert migrated_legacy_ids == {
        1001,
        1002,
    }

    loaned_item = db_session.scalar(
        select(CollectionItem)
        .join(
            LegacyBookMigration,
            LegacyBookMigration.collection_item_id
            == CollectionItem.id,
        )
        .where(
            LegacyBookMigration.legacy_book_id
            == 1002
        )
    )

    assert loaned_item is not None
    assert loaned_item.status == "loaned"


def test_migrate_legacy_books_batch_counts_warning(
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_test_book_category(db_session)

    create_test_storage_hierarchy(
        db_session,
        household_id=household.id,
    )

    legacy_book_id = 1265

    source_records = [
        (
            LegacyBookSource(
                legacy_book_id=legacy_book_id,
                isbn="X",
                title="Grimm mesék",
                author=None,
                publisher=None,
                publish_year=None,
                location_id=5,
                borrowed_to=None,
                created=None,
                updated=None,
            ),
            LegacyLocationSource(
                legacy_location_id=5,
                room="Nappali",
                shelf="Újpolc",
                slot=5,
            ),
        )
    ]

    result = migrate_legacy_books_batch(
        session=db_session,
        source_records=source_records,
        household_id=household.id,
        category_id=category.id,
    )

    assert result.total_source_records == 1
    assert result.created_count == 1
    assert result.skipped_count == 0
    assert result.migrated_count == 0
    assert result.warning_count == 1
    assert result.error_count == 0

    migration = db_session.scalar(
        select(LegacyBookMigration).where(
            LegacyBookMigration.legacy_book_id
            == legacy_book_id
        )
    )

    assert migration is not None
    assert migration.migration_status == "warning"
    assert migration.migration_notes is not None
    assert "helykitöltő ISBN" in migration.migration_notes


def test_migrate_legacy_books_batch_is_idempotent(
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_test_book_category(db_session)

    create_test_storage_hierarchy(
        db_session,
        household_id=household.id,
    )

    source_records = [
        (
            LegacyBookSource(
                legacy_book_id=1006,
                isbn="9789633694503",
                title="A három testőr Afrikában",
                author="Jenő Rejtő",
                publisher="Alexandra K.",
                publish_year="2007",
                location_id=5,
                borrowed_to=None,
                created=None,
                updated=None,
            ),
            LegacyLocationSource(
                legacy_location_id=5,
                room="Nappali",
                shelf="Újpolc",
                slot=5,
            ),
        )
    ]

    first_result = migrate_legacy_books_batch(
        session=db_session,
        source_records=source_records,
        household_id=household.id,
        category_id=category.id,
    )

    second_result = migrate_legacy_books_batch(
        session=db_session,
        source_records=source_records,
        household_id=household.id,
        category_id=category.id,
    )

    assert first_result.total_source_records == 1
    assert first_result.created_count == 1
    assert first_result.skipped_count == 0

    assert second_result.total_source_records == 1
    assert second_result.created_count == 0
    assert second_result.skipped_count == 1
    assert second_result.error_count == 0

    item_count = db_session.scalar(
        select(func.count(CollectionItem.id)).where(
            CollectionItem.household_id == household.id
        )
    )

    migration_count = db_session.scalar(
        select(func.count(LegacyBookMigration.id))
    )

    assert item_count == 1
    assert migration_count == 1


def test_migrate_legacy_books_batch_continues_after_record_error(
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_test_book_category(db_session)

    create_test_storage_hierarchy(
        db_session,
        household_id=household.id,
    )

    invalid_book_id = 1999
    valid_book_id = 2000

    source_records = [
        (
            LegacyBookSource(
                legacy_book_id=invalid_book_id,
                isbn="9789630000000",
                title="   ",
                author=None,
                publisher=None,
                publish_year=None,
                location_id=5,
                borrowed_to=None,
                created=None,
                updated=None,
            ),
            LegacyLocationSource(
                legacy_location_id=5,
                room="Nappali",
                shelf="Újpolc",
                slot=5,
            ),
        ),
        (
            LegacyBookSource(
                legacy_book_id=valid_book_id,
                isbn="9789633694503",
                title="Érvényes könyv",
                author="Teszt szerző",
                publisher="Teszt kiadó",
                publish_year="2020",
                location_id=5,
                borrowed_to=None,
                created=None,
                updated=None,
            ),
            LegacyLocationSource(
                legacy_location_id=5,
                room="Nappali",
                shelf="Újpolc",
                slot=5,
            ),
        ),
    ]

    result = migrate_legacy_books_batch(
        session=db_session,
        source_records=source_records,
        household_id=household.id,
        category_id=category.id,
        continue_on_error=True,
    )

    assert result.total_source_records == 2
    assert result.created_count == 1
    assert result.migrated_count == 1
    assert result.warning_count == 0
    assert result.error_count == 1

    assert len(result.errors) == 1
    assert result.errors[0].legacy_book_id == invalid_book_id
    assert "könyv címe üres" in result.errors[0].message

    valid_migration = db_session.scalar(
        select(LegacyBookMigration).where(
            LegacyBookMigration.legacy_book_id
            == valid_book_id
        )
    )

    invalid_migration = db_session.scalar(
        select(LegacyBookMigration).where(
            LegacyBookMigration.legacy_book_id
            == invalid_book_id
        )
    )

    assert valid_migration is not None
    assert invalid_migration is None
