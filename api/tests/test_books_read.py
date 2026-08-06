from datetime import datetime

from sqlalchemy import select
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
from app.services import (
    get_book_by_legacy_id,
    list_books,
    list_latest_books,
    move_book_to_storage_location,
    resolve_storage_location_from_legacy_id,
    soft_delete_book_by_legacy_id,
    update_collection_item_title,
    update_book_borrow_state,
    update_book_metadata_fields,
    update_primary_identifier,
    update_book_by_legacy_id,
    create_manual_book,
    list_all_books_for_export,
)


def create_test_household(
    session: Session,
) -> Household:
    household = Household(
        name="Books read teszt",
        slug="books-read-test",
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
        description="Books read tesztkategória",
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
    room_name: str = "Nappali",
    shelf_name: str = "Újpolc",
    slot_number: int = 5,
) -> StorageLocation:
    room = StorageLocation(
        household_id=household_id,
        parent_id=None,
        name=room_name,
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
        name=shelf_name,
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
        name=f"{slot_number}. hely",
        slug=f"slot-{slot_number}",
        location_type="slot",
        sort_order=slot_number * 10,
        is_active=True,
    )

    session.add(slot)
    session.flush()

    return slot


def create_migrated_book(
    session: Session,
    *,
    household: Household,
    category: Category,
    storage_location: StorageLocation,
    legacy_book_id: int,
    title: str,
    author: str | None,
    publisher: str | None,
    publish_year: int | None,
    identifier_type: str | None,
    identifier_value: str | None,
    borrowed_to: str | None,
    created_at: datetime,
) -> CollectionItem:
    item = CollectionItem(
        household_id=household.id,
        category_id=category.id,
        title=title,
        status="loaned" if borrowed_to else "active",
        is_active=True,
        created_at=created_at,
        updated_at=created_at,
    )

    session.add(item)
    session.flush()

    fields = {
        field.field_key: field
        for field in session.scalars(
            select(CategoryField).where(
                CategoryField.category_id == category.id
            )
        ).all()
    }

    if author is not None:
        session.add(
            ItemFieldValue(
                item_id=item.id,
                field_id=fields["author"].id,
                value_text=author,
            )
        )

    if publisher is not None:
        session.add(
            ItemFieldValue(
                item_id=item.id,
                field_id=fields["publisher"].id,
                value_text=publisher,
            )
        )

    if publish_year is not None:
        session.add(
            ItemFieldValue(
                item_id=item.id,
                field_id=fields["publish_year"].id,
                value_integer=publish_year,
            )
        )

    if (
        identifier_type is not None
        and identifier_value is not None
    ):
        session.add(
            ItemIdentifier(
                item_id=item.id,
                identifier_type=identifier_type,
                identifier_value=identifier_value,
                is_primary=True,
                is_active=True,
            )
        )

    session.add(
        ItemStorageAssignment(
            item_id=item.id,
            storage_location_id=storage_location.id,
            is_active=True,
            assigned_at=created_at,
            movement_reason="test",
        )
    )

    session.add(
        LegacyBookMigration(
            legacy_book_id=legacy_book_id,
            collection_item_id=item.id,
            legacy_location_id=legacy_book_id,
            legacy_isbn=identifier_value,
            legacy_borrowed_to=borrowed_to,
            legacy_room="Nappali",
            legacy_shelf="Újpolc",
            legacy_slot=5,
            migration_status="migrated",
        )
    )

    session.flush()

    return item


def test_get_book_by_legacy_id_returns_compatible_record(
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_test_book_category(db_session)
    slot = create_test_storage_hierarchy(
        db_session,
        household_id=household.id,
    )

    created_at = datetime(2026, 7, 14, 8, 53, 42)

    create_migrated_book(
        db_session,
        household=household,
        category=category,
        storage_location=slot,
        legacy_book_id=6,
        title="A három testőr Afrikában",
        author="Jenő Rejtő",
        publisher="Alexandra K.",
        publish_year=2007,
        identifier_type="isbn13",
        identifier_value="9789633694503",
        borrowed_to=None,
        created_at=created_at,
    )

    record = get_book_by_legacy_id(
        db_session,
        6,
    )

    assert record is not None
    assert record.id == 6
    assert record.isbn == "9789633694503"
    assert record.title == "A három testőr Afrikában"
    assert record.author == "Jenő Rejtő"
    assert record.publisher == "Alexandra K."
    assert record.year == 2007
    assert record.added == created_at
    assert record.location_id == 6
    assert record.room == "Nappali"
    assert record.shelf == "Újpolc"
    assert record.slot == 5
    assert record.borrower is None
    assert record.status == "active"


def test_get_book_by_legacy_id_formats_issn(
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_test_book_category(db_session)
    slot = create_test_storage_hierarchy(
        db_session,
        household_id=household.id,
    )

    create_migrated_book(
        db_session,
        household=household,
        category=category,
        storage_location=slot,
        legacy_book_id=99,
        title="A Szépség és a Szörnyeteg",
        author=None,
        publisher=None,
        publish_year=None,
        identifier_type="issn",
        identifier_value="3103-4152",
        borrowed_to=None,
        created_at=datetime(2026, 7, 15, 10, 0, 0),
    )

    record = get_book_by_legacy_id(
        db_session,
        99,
    )

    assert record is not None
    assert record.isbn == "ISSN 3103-4152"


def test_get_book_by_legacy_id_ignores_inactive_item(
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_test_book_category(db_session)
    slot = create_test_storage_hierarchy(
        db_session,
        household_id=household.id,
    )

    item = create_migrated_book(
        db_session,
        household=household,
        category=category,
        storage_location=slot,
        legacy_book_id=10,
        title="Inaktív könyv",
        author=None,
        publisher=None,
        publish_year=None,
        identifier_type=None,
        identifier_value=None,
        borrowed_to=None,
        created_at=datetime(2026, 7, 15, 10, 0, 0),
    )

    item.is_active = False
    db_session.flush()

    assert get_book_by_legacy_id(
        db_session,
        10,
    ) is None


def test_list_latest_books_orders_by_created_descending(
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_test_book_category(db_session)
    slot = create_test_storage_hierarchy(
        db_session,
        household_id=household.id,
    )

    create_migrated_book(
        db_session,
        household=household,
        category=category,
        storage_location=slot,
        legacy_book_id=1,
        title="Régebbi könyv",
        author=None,
        publisher=None,
        publish_year=None,
        identifier_type=None,
        identifier_value=None,
        borrowed_to=None,
        created_at=datetime(2026, 7, 14, 10, 0, 0),
    )

    create_migrated_book(
        db_session,
        household=household,
        category=category,
        storage_location=slot,
        legacy_book_id=2,
        title="Újabb könyv",
        author=None,
        publisher=None,
        publish_year=None,
        identifier_type=None,
        identifier_value=None,
        borrowed_to=None,
        created_at=datetime(2026, 7, 15, 10, 0, 0),
    )

    records = list_latest_books(
        db_session,
        limit=20,
    )

    assert [
        record.id
        for record in records
    ] == [
        2,
        1,
    ]


def test_list_books_returns_compatible_page(
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_test_book_category(db_session)
    slot = create_test_storage_hierarchy(
        db_session,
        household_id=household.id,
    )

    create_migrated_book(
        db_session,
        household=household,
        category=category,
        storage_location=slot,
        legacy_book_id=2,
        title="B könyv",
        author="Második szerző",
        publisher=None,
        publish_year=2002,
        identifier_type="isbn13",
        identifier_value="9789632222222",
        borrowed_to="Teszt kölcsönző",
        created_at=datetime(2026, 7, 15, 10, 0, 0),
    )

    create_migrated_book(
        db_session,
        household=household,
        category=category,
        storage_location=slot,
        legacy_book_id=1,
        title="A könyv",
        author="Első szerző",
        publisher="Teszt kiadó",
        publish_year=2001,
        identifier_type="isbn13",
        identifier_value="9789631111111",
        borrowed_to=None,
        created_at=datetime(2026, 7, 14, 10, 0, 0),
    )

    page = list_books(
        db_session,
        page=1,
        page_size=50,
    )

    assert page.page == 1
    assert page.page_size == 50
    assert page.total == 2

    assert [
        record.id
        for record in page.records
    ] == [
        1,
        2,
    ]

    assert page.records[0].title == "A könyv"
    assert page.records[1].borrower == "Teszt kölcsönző"
    assert page.records[1].status == "loaned"

def test_list_books_searches_title_and_identifier(
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_test_book_category(db_session)
    slot = create_test_storage_hierarchy(
        db_session,
        household_id=household.id,
    )

    create_migrated_book(
        db_session,
        household=household,
        category=category,
        storage_location=slot,
        legacy_book_id=1,
        title="A három testőr Afrikában",
        author="Jenő Rejtő",
        publisher="Alexandra K.",
        publish_year=2007,
        identifier_type="isbn13",
        identifier_value="9789633694503",
        borrowed_to=None,
        created_at=datetime(2026, 7, 14, 10, 0, 0),
    )

    create_migrated_book(
        db_session,
        household=household,
        category=category,
        storage_location=slot,
        legacy_book_id=2,
        title="Másik könyv",
        author="Másik szerző",
        publisher="Másik kiadó",
        publish_year=2020,
        identifier_type="isbn13",
        identifier_value="9789632222222",
        borrowed_to=None,
        created_at=datetime(2026, 7, 15, 10, 0, 0),
    )

    title_page = list_books(
        db_session,
        search="három testőr",
    )

    assert title_page.total == 1
    assert title_page.records[0].id == 1

    identifier_page = list_books(
        db_session,
        search="9789633694503",
    )

    assert identifier_page.total == 1
    assert identifier_page.records[0].id == 1


def test_list_books_searches_dynamic_fields(
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_test_book_category(db_session)
    slot = create_test_storage_hierarchy(
        db_session,
        household_id=household.id,
    )

    create_migrated_book(
        db_session,
        household=household,
        category=category,
        storage_location=slot,
        legacy_book_id=1,
        title="Tesztkönyv",
        author="Jenő Rejtő",
        publisher="Alexandra K.",
        publish_year=2007,
        identifier_type="isbn13",
        identifier_value="9789633694503",
        borrowed_to=None,
        created_at=datetime(2026, 7, 14, 10, 0, 0),
    )

    author_page = list_books(
        db_session,
        search="Rejtő",
    )

    assert author_page.total == 1
    assert author_page.records[0].id == 1

    publisher_page = list_books(
        db_session,
        search="Alexandra",
    )

    assert publisher_page.total == 1
    assert publisher_page.records[0].id == 1

    year_page = list_books(
        db_session,
        search="2007",
    )

    assert year_page.total == 1
    assert year_page.records[0].id == 1


def test_list_books_searches_borrower_and_location(
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_test_book_category(db_session)
    slot = create_test_storage_hierarchy(
        db_session,
        household_id=household.id,
        room_name="Nappali",
        shelf_name="Újpolc",
        slot_number=5,
    )

    create_migrated_book(
        db_session,
        household=household,
        category=category,
        storage_location=slot,
        legacy_book_id=1,
        title="Kölcsönadott könyv",
        author=None,
        publisher=None,
        publish_year=None,
        identifier_type=None,
        identifier_value=None,
        borrowed_to="Teszt kölcsönző",
        created_at=datetime(2026, 7, 14, 10, 0, 0),
    )

    borrower_page = list_books(
        db_session,
        search="kölcsönző",
    )

    assert borrower_page.total == 1
    assert borrower_page.records[0].id == 1

    room_page = list_books(
        db_session,
        search="Nappali",
    )

    assert room_page.total == 1
    assert room_page.records[0].id == 1

    shelf_page = list_books(
        db_session,
        search="Újpolc",
    )

    assert shelf_page.total == 1
    assert shelf_page.records[0].id == 1

    slot_page = list_books(
        db_session,
        search="5",
    )

    assert slot_page.total == 1
    assert slot_page.records[0].id == 1


def test_list_books_paginates_results(
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_test_book_category(db_session)
    slot = create_test_storage_hierarchy(
        db_session,
        household_id=household.id,
    )

    for legacy_book_id, title in (
        (1, "A könyv"),
        (2, "B könyv"),
        (3, "C könyv"),
    ):
        create_migrated_book(
            db_session,
            household=household,
            category=category,
            storage_location=slot,
            legacy_book_id=legacy_book_id,
            title=title,
            author=None,
            publisher=None,
            publish_year=None,
            identifier_type=None,
            identifier_value=None,
            borrowed_to=None,
            created_at=datetime(
                2026,
                7,
                14,
                10,
                legacy_book_id,
                0,
            ),
        )

    first_page = list_books(
        db_session,
        page=1,
        page_size=2,
    )

    second_page = list_books(
        db_session,
        page=2,
        page_size=2,
    )

    assert first_page.total == 3
    assert first_page.page == 1
    assert first_page.page_size == 2
    assert [
        record.id
        for record in first_page.records
    ] == [1, 2]

    assert second_page.total == 3
    assert second_page.page == 2
    assert [
        record.id
        for record in second_page.records
    ] == [3]

def test_soft_delete_book_by_legacy_id_deactivates_item(
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_test_book_category(db_session)
    slot = create_test_storage_hierarchy(
        db_session,
        household_id=household.id,
    )

    item = create_migrated_book(
        db_session,
        household=household,
        category=category,
        storage_location=slot,
        legacy_book_id=6,
        title="Törlendő könyv",
        author=None,
        publisher=None,
        publish_year=None,
        identifier_type=None,
        identifier_value=None,
        borrowed_to=None,
        created_at=datetime(2026, 7, 14, 10, 0, 0),
    )

    deleted = soft_delete_book_by_legacy_id(
        db_session,
        6,
    )

    assert deleted is True
    assert item.is_active is False

    assert get_book_by_legacy_id(
        db_session,
        6,
    ) is None


def test_soft_delete_book_by_legacy_id_returns_false_when_missing(
    db_session: Session,
) -> None:
    deleted = soft_delete_book_by_legacy_id(
        db_session,
        999999,
    )

    assert deleted is False

def test_update_collection_item_title(
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_test_book_category(db_session)
    slot = create_test_storage_hierarchy(
        db_session,
        household_id=household.id,
    )

    item = create_migrated_book(
        db_session,
        household=household,
        category=category,
        storage_location=slot,
        legacy_book_id=6,
        title="Régi cím",
        author=None,
        publisher=None,
        publish_year=None,
        identifier_type=None,
        identifier_value=None,
        borrowed_to=None,
        created_at=datetime(2026, 7, 14, 10, 0, 0),
    )

    updated = update_collection_item_title(
        db_session,
        legacy_book_id=6,
        title="  Új cím  ",
    )

    assert updated is True

    db_session.refresh(item)

    assert item.title == "Új cím"


def test_update_collection_item_title_returns_false_for_missing_book(
    db_session: Session,
) -> None:
    updated = update_collection_item_title(
        db_session,
        legacy_book_id=999999,
        title="Akármi",
    )

    assert updated is False


def test_update_primary_identifier_updates_existing_identifier(
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_test_book_category(db_session)
    slot = create_test_storage_hierarchy(
        db_session,
        household_id=household.id,
    )

    item = create_migrated_book(
        db_session,
        household=household,
        category=category,
        storage_location=slot,
        legacy_book_id=6,
        title="Tesztkönyv",
        author=None,
        publisher=None,
        publish_year=None,
        identifier_type="isbn13",
        identifier_value="9789631111111",
        borrowed_to=None,
        created_at=datetime(2026, 7, 14),
    )

    updated = update_primary_identifier(
        db_session,
        legacy_book_id=6,
        identifier_type="isbn13",
        identifier_value="9789632222222",
    )

    assert updated is True

    identifiers = (
        db_session.query(ItemIdentifier)
        .filter(
            ItemIdentifier.item_id == item.id,
            ItemIdentifier.is_active.is_(True),
        )
        .all()
    )

    assert len(identifiers) == 2

    primary = next(
        identifier
        for identifier in identifiers
        if identifier.is_primary
    )

    assert primary.identifier_type == "isbn13"
    assert primary.identifier_value == "9789632222222"

    migration = (
        db_session.query(LegacyBookMigration)
        .filter_by(
            legacy_book_id=6,
        )
        .one()
    )

    assert migration.legacy_isbn == "9789632222222"


def test_update_primary_identifier_creates_identifier_when_missing(
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_test_book_category(db_session)
    slot = create_test_storage_hierarchy(
        db_session,
        household_id=household.id,
    )

    item = create_migrated_book(
        db_session,
        household=household,
        category=category,
        storage_location=slot,
        legacy_book_id=265,
        title="Grimm mesék",
        author=None,
        publisher=None,
        publish_year=None,
        identifier_type=None,
        identifier_value=None,
        borrowed_to=None,
        created_at=datetime(2026, 7, 14),
    )

    updated = update_primary_identifier(
        db_session,
        legacy_book_id=265,
        identifier_type="isbn13",
        identifier_value="9789633333333",
    )

    assert updated is True

    identifiers = (
        db_session.query(ItemIdentifier)
        .filter(
            ItemIdentifier.item_id == item.id,
            ItemIdentifier.is_active.is_(True),
        )
        .all()
    )

    assert len(identifiers) == 1

    identifier = identifiers[0]

    assert identifier.identifier_type == "isbn13"
    assert identifier.identifier_value == "9789633333333"
    assert identifier.is_primary is True

    migration = (
        db_session.query(LegacyBookMigration)
        .filter_by(
            legacy_book_id=265,
        )
        .one()
    )

    assert migration.legacy_isbn == "9789633333333"


def test_update_book_metadata_fields_updates_existing_values(
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_test_book_category(db_session)
    slot = create_test_storage_hierarchy(
        db_session,
        household_id=household.id,
    )

    item = create_migrated_book(
        db_session,
        household=household,
        category=category,
        storage_location=slot,
        legacy_book_id=6,
        title="Tesztkönyv",
        author="Régi szerző",
        publisher="Régi kiadó",
        publish_year=1999,
        identifier_type=None,
        identifier_value=None,
        borrowed_to=None,
        created_at=datetime(2026, 7, 14),
    )

    updated = update_book_metadata_fields(
        db_session,
        legacy_book_id=6,
        author="Új szerző",
        publisher="Új kiadó",
        publish_year=2024,
    )

    assert updated is True

    values = {
        value.field.field_key: value
        for value in db_session.query(ItemFieldValue)
        .filter(
            ItemFieldValue.item_id == item.id
        )
        .all()
    }

    assert values["author"].value_text == "Új szerző"
    assert values["publisher"].value_text == "Új kiadó"
    assert values["publish_year"].value_integer == 2024


def test_update_book_metadata_fields_removes_empty_values(
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_test_book_category(db_session)
    slot = create_test_storage_hierarchy(
        db_session,
        household_id=household.id,
    )

    item = create_migrated_book(
        db_session,
        household=household,
        category=category,
        storage_location=slot,
        legacy_book_id=6,
        title="Tesztkönyv",
        author="Régi szerző",
        publisher="Régi kiadó",
        publish_year=1999,
        identifier_type=None,
        identifier_value=None,
        borrowed_to=None,
        created_at=datetime(2026, 7, 14),
    )

    updated = update_book_metadata_fields(
        db_session,
        legacy_book_id=6,
        author="   ",
        publisher=None,
        publish_year=None,
    )

    assert updated is True

    values = {
        value.field.field_key: value
        for value in db_session.query(ItemFieldValue)
        .filter(
            ItemFieldValue.item_id == item.id
        )
        .all()
    }

    assert "author" not in values
    assert "publisher" not in values
    assert "publish_year" not in values


def test_move_book_to_storage_location(
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_test_book_category(db_session)

    target_slot = create_test_storage_hierarchy(
        db_session,
        household_id=household.id,
    )

    source_room = StorageLocation(
        household_id=household.id,
        parent_id=None,
        name="Dolgozó",
        slug="dolgozo",
        location_type="room",
        sort_order=20,
        is_active=True,
    )

    db_session.add(source_room)
    db_session.flush()

    source_shelf = StorageLocation(
        household_id=household.id,
        parent_id=source_room.id,
        name="Könyvespolc",
        slug="konyvespolc",
        location_type="shelf",
        sort_order=10,
        is_active=True,
    )

    db_session.add(source_shelf)
    db_session.flush()

    source_slot = StorageLocation(
        household_id=household.id,
        parent_id=source_shelf.id,
        name="2. hely",
        slug="slot-2",
        location_type="slot",
        sort_order=20,
        is_active=True,
    )

    db_session.add(source_slot)
    db_session.flush()

    item = create_migrated_book(
        db_session,
        household=household,
        category=category,
        storage_location=source_slot,
        legacy_book_id=6,
        title="Tesztkönyv",
        author=None,
        publisher=None,
        publish_year=None,
        identifier_type=None,
        identifier_value=None,
        borrowed_to=None,
        created_at=datetime(2026, 7, 14),
    )

    updated = move_book_to_storage_location(
        db_session,
        legacy_book_id=6,
        storage_location_id=target_slot.id,
    )

    assert updated is True

    assignments = (
        db_session.query(ItemStorageAssignment)
        .filter(
            ItemStorageAssignment.item_id == item.id
        )
        .order_by(ItemStorageAssignment.id)
        .all()
    )

    assert len(assignments) == 2

    assert assignments[0].is_active is False
    assert assignments[0].removed_at is not None

    assert assignments[1].is_active is True
    assert (
        assignments[1].storage_location_id
        == target_slot.id
    )

    migration = (
        db_session.query(LegacyBookMigration)
        .filter_by(
            legacy_book_id=6,
        )
        .one()
    )

    assert migration.legacy_room == "Nappali"
    assert migration.legacy_shelf == "Újpolc"
    assert migration.legacy_slot == 5


def test_move_book_to_same_storage_location_does_not_create_history(
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_test_book_category(db_session)

    slot = create_test_storage_hierarchy(
        db_session,
        household_id=household.id,
    )

    item = create_migrated_book(
        db_session,
        household=household,
        category=category,
        storage_location=slot,
        legacy_book_id=6,
        title="Tesztkönyv",
        author=None,
        publisher=None,
        publish_year=None,
        identifier_type=None,
        identifier_value=None,
        borrowed_to=None,
        created_at=datetime(2026, 7, 14),
    )

    updated = move_book_to_storage_location(
        db_session,
        legacy_book_id=6,
        storage_location_id=slot.id,
    )

    assert updated is True

    assignments = (
        db_session.query(ItemStorageAssignment)
        .filter(
            ItemStorageAssignment.item_id == item.id
        )
        .all()
    )

    assert len(assignments) == 1
    assert assignments[0].is_active is True
    assert assignments[0].removed_at is None
    assert assignments[0].storage_location_id == slot.id


def test_update_book_borrow_state_sets_loaned_status(
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_test_book_category(db_session)
    slot = create_test_storage_hierarchy(
        db_session,
        household_id=household.id,
    )

    item = create_migrated_book(
        db_session,
        household=household,
        category=category,
        storage_location=slot,
        legacy_book_id=6,
        title="Tesztkönyv",
        author=None,
        publisher=None,
        publish_year=None,
        identifier_type=None,
        identifier_value=None,
        borrowed_to=None,
        created_at=datetime(2026, 7, 14),
    )

    updated = update_book_borrow_state(
        db_session,
        legacy_book_id=6,
        borrower="  Teszt kölcsönző  ",
    )

    assert updated is True

    db_session.refresh(item)

    assert item.status == "loaned"

    migration = (
        db_session.query(LegacyBookMigration)
        .filter_by(
            legacy_book_id=6,
        )
        .one()
    )

    assert migration.legacy_borrowed_to == "Teszt kölcsönző"


def test_update_book_borrow_state_clears_borrower_and_sets_active(
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_test_book_category(db_session)
    slot = create_test_storage_hierarchy(
        db_session,
        household_id=household.id,
    )

    item = create_migrated_book(
        db_session,
        household=household,
        category=category,
        storage_location=slot,
        legacy_book_id=6,
        title="Tesztkönyv",
        author=None,
        publisher=None,
        publish_year=None,
        identifier_type=None,
        identifier_value=None,
        borrowed_to="Teszt kölcsönző",
        created_at=datetime(2026, 7, 14),
    )

    updated = update_book_borrow_state(
        db_session,
        legacy_book_id=6,
        borrower="   ",
    )

    assert updated is True

    db_session.refresh(item)

    assert item.status == "active"

    migration = (
        db_session.query(LegacyBookMigration)
        .filter_by(
            legacy_book_id=6,
        )
        .one()
    )

    assert migration.legacy_borrowed_to is None


def test_update_book_by_legacy_id_updates_complete_book(
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_test_book_category(db_session)

    source_slot = create_test_storage_hierarchy(
        db_session,
        household_id=household.id,
    )

    target_room = StorageLocation(
        household_id=household.id,
        parent_id=None,
        name="Dolgozó",
        slug="dolgozo",
        location_type="room",
        sort_order=20,
        is_active=True,
    )

    db_session.add(target_room)
    db_session.flush()

    target_shelf = StorageLocation(
        household_id=household.id,
        parent_id=target_room.id,
        name="Könyvespolc",
        slug="konyvespolc",
        location_type="shelf",
        sort_order=10,
        is_active=True,
    )

    db_session.add(target_shelf)
    db_session.flush()

    target_slot = StorageLocation(
        household_id=household.id,
        parent_id=target_shelf.id,
        name="2. hely",
        slug="slot-2",
        location_type="slot",
        sort_order=20,
        is_active=True,
    )

    db_session.add(target_slot)
    db_session.flush()

    item = create_migrated_book(
        db_session,
        household=household,
        category=category,
        storage_location=source_slot,
        legacy_book_id=6,
        title="Régi cím",
        author="Régi szerző",
        publisher="Régi kiadó",
        publish_year=1999,
        identifier_type="isbn13",
        identifier_value="9789631111111",
        borrowed_to=None,
        created_at=datetime(2026, 7, 14, 10, 0, 0),
    )

    updated = update_book_by_legacy_id(
        db_session,
        legacy_book_id=6,
        title="  Új cím  ",
        identifier_type="isbn13",
        identifier_value="9789632222222",
        author="  Új szerző  ",
        publisher="  Új kiadó  ",
        publish_year=2024,
        storage_location_id=target_slot.id,
        borrower="  Teszt kölcsönző  ",
    )

    assert updated is True

    db_session.refresh(item)

    assert item.title == "Új cím"
    assert item.status == "loaned"

    active_identifiers = (
        db_session.query(ItemIdentifier)
        .filter(
            ItemIdentifier.item_id == item.id,
            ItemIdentifier.is_active.is_(True),
        )
        .all()
    )

    primary_identifier = next(
        identifier
        for identifier in active_identifiers
        if identifier.is_primary
    )

    assert primary_identifier.identifier_type == "isbn13"
    assert primary_identifier.identifier_value == "9789632222222"

    values = {
        value.field.field_key: value
        for value in db_session.query(ItemFieldValue)
        .filter(
            ItemFieldValue.item_id == item.id
        )
        .all()
    }

    assert values["author"].value_text == "Új szerző"
    assert values["publisher"].value_text == "Új kiadó"
    assert values["publish_year"].value_integer == 2024

    assignments = (
        db_session.query(ItemStorageAssignment)
        .filter(
            ItemStorageAssignment.item_id == item.id
        )
        .order_by(ItemStorageAssignment.id)
        .all()
    )

    assert len(assignments) == 2

    assert assignments[0].is_active is False
    assert assignments[0].removed_at is not None

    assert assignments[1].is_active is True
    assert assignments[1].storage_location_id == target_slot.id
    assert assignments[1].movement_reason == "book_update"

    migration = (
        db_session.query(LegacyBookMigration)
        .filter_by(
            legacy_book_id=6,
        )
        .one()
    )

    assert migration.legacy_isbn == "9789632222222"
    assert migration.legacy_borrowed_to == "Teszt kölcsönző"
    assert migration.legacy_location_id is None
    assert migration.legacy_room == "Dolgozó"
    assert migration.legacy_shelf == "Könyvespolc"
    assert migration.legacy_slot == 2


def test_update_book_by_legacy_id_returns_false_for_missing_book(
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    create_test_book_category(db_session)

    slot = create_test_storage_hierarchy(
        db_session,
        household_id=household.id,
    )

    updated = update_book_by_legacy_id(
        session=db_session,
        legacy_book_id=999999,
        title="Bármi",
        identifier_type="isbn13",
        identifier_value="9789630000000",
        author=None,
        publisher=None,
        publish_year=None,
        storage_location_id=slot.id,
        borrower=None,
    )

    assert updated is False


def test_resolve_storage_location_from_legacy_id_returns_slot(
    db_session: Session,
) -> None:
    household = create_test_household(db_session)

    room = StorageLocation(
        household_id=household.id,
        parent_id=None,
        name="Nappali",
        slug="nappali",
        location_type="room",
        sort_order=10,
        is_active=True,
        description=(
            "[legacy-locations-seed:test] "
            "Régi helyiség: Nappali"
        ),
    )

    db_session.add(room)
    db_session.flush()

    shelf = StorageLocation(
        household_id=household.id,
        parent_id=room.id,
        name="Újpolc",
        slug="ujpolc",
        location_type="shelf",
        sort_order=10,
        is_active=True,
        description=(
            "[legacy-locations-seed:test] "
            "Régi polc/szekrény: Nappali / Újpolc"
        ),
    )

    db_session.add(shelf)
    db_session.flush()

    slot = StorageLocation(
        household_id=household.id,
        parent_id=shelf.id,
        name="5. hely",
        slug="slot-5",
        location_type="slot",
        sort_order=50,
        is_active=True,
        description=(
            "[legacy-locations-seed:test] "
            "Régi location_id=5; "
            "útvonal=Nappali / Újpolc / 5"
        ),
    )

    db_session.add(slot)
    db_session.flush()

    resolved = resolve_storage_location_from_legacy_id(
        db_session,
        household_id=household.id,
        legacy_location_id=5,
    )

    assert resolved is not None
    assert resolved.id == slot.id
    assert resolved.location_type == "slot"


def test_resolve_storage_location_from_legacy_id_returns_none_when_missing(
    db_session: Session,
) -> None:
    household = create_test_household(db_session)

    resolved = resolve_storage_location_from_legacy_id(
        db_session,
        household_id=household.id,
        legacy_location_id=999999,
    )

    assert resolved is None


def test_create_manual_book_creates_complete_structure(
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_test_book_category(db_session)

    slot = create_test_storage_hierarchy(
        db_session,
        household_id=household.id,
    )

    legacy_id, item_public_id = (
        create_manual_book(
        session=db_session,
        household_id=household.id,
        category_id=category.id,
        identifier="9789633694503",
        title=" Manuális könyv ",
        author=" Rejtő Jenő ",
        publisher=" Alexandra ",
        publish_year=2007,
        legacy_location_id=5,
        storage_location_id=slot.id,
        )
    )

    assert legacy_id > 0
    assert item_public_id

    migration = (
        db_session.query(LegacyBookMigration)
        .filter_by(
            legacy_book_id=legacy_id,
        )
        .one()
    )

    item = migration.collection_item

    assert item is not None
    assert item.title == "Manuális könyv"
    assert item.status == "active"

    identifier = (
        db_session.query(ItemIdentifier)
        .filter(
            ItemIdentifier.item_id == item.id,
            ItemIdentifier.is_primary.is_(True),
        )
        .one()
    )

    assert identifier.identifier_type == "isbn13"
    assert identifier.identifier_value == "9789633694503"

    values = {
        value.field.field_key: value
        for value in db_session.query(ItemFieldValue)
        .filter(
            ItemFieldValue.item_id == item.id
        )
        .all()
    }

    assert values["author"].value_text == "Rejtő Jenő"
    assert values["publisher"].value_text == "Alexandra"
    assert values["publish_year"].value_integer == 2007

    assignment = (
        db_session.query(ItemStorageAssignment)
        .filter_by(
            item_id=item.id,
            is_active=True,
        )
        .one()
    )

    assert assignment.storage_location_id == slot.id

    assert migration.legacy_location_id == 5


def test_create_manual_book_accepts_custom_identifier(
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_test_book_category(db_session)

    slot = create_test_storage_hierarchy(
        db_session,
        household_id=household.id,
    )

    legacy_id, item_public_id = (
        create_manual_book(
        session=db_session,
        household_id=household.id,
        category_id=category.id,
        identifier="Saját jelzet 42",
        title="Jelzetes könyv",
        author=None,
        publisher=None,
        publish_year=None,
        legacy_location_id=5,
        storage_location_id=slot.id,
        )
    )

    assert item_public_id
    migration = (
        db_session.query(LegacyBookMigration)
        .filter_by(
            legacy_book_id=legacy_id,
        )
        .one()
    )

    item = migration.collection_item

    assert item is not None

    identifier = (
        db_session.query(ItemIdentifier)
        .filter(
            ItemIdentifier.item_id == item.id,
            ItemIdentifier.is_primary.is_(True),
        )
        .one()
    )

    assert identifier.identifier_type == "custom"
    assert identifier.identifier_value == "Saját jelzet 42"

    assert migration.legacy_isbn == "Saját jelzet 42"


def test_create_manual_book_rejects_missing_storage_location(
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_test_book_category(db_session)

    try:
        create_manual_book(
            session=db_session,
            household_id=household.id,
            category_id=category.id,
            identifier="9789633694503",
            title="Tesztkönyv",
            author=None,
            publisher=None,
            publish_year=None,
            legacy_location_id=5,
            storage_location_id=999999,
        )
    except ValueError as error:
        assert "tárolóhely nem létezik" in str(error)
    else:
        raise AssertionError(
            "ValueError kivételre számítottunk."
        )


def test_create_manual_book_rejects_non_book_category(
    db_session: Session,
) -> None:
    household = create_test_household(db_session)

    category = Category(
        household_id=None,
        name="Társasjáték",
        slug="boardgame",
        description="Nem könyvkategória",
        icon="dice",
        is_system=True,
        is_active=True,
        supports_barcode=True,
        metadata_lookup_type="manual",
        sort_order=20,
    )

    db_session.add(category)
    db_session.flush()

    slot = create_test_storage_hierarchy(
        db_session,
        household_id=household.id,
    )

    try:
        create_manual_book(
            session=db_session,
            household_id=household.id,
            category_id=category.id,
            identifier="9789633694503",
            title="Tesztkönyv",
            author=None,
            publisher=None,
            publish_year=None,
            legacy_location_id=5,
            storage_location_id=slot.id,
        )
    except ValueError as error:
        assert "book kategória" in str(error)
    else:
        raise AssertionError(
            "ValueError kivételre számítottunk."
        )


def test_list_all_books_for_export_returns_active_books_in_legacy_id_order(
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_test_book_category(db_session)

    slot = create_test_storage_hierarchy(
        db_session,
        household_id=household.id,
    )

    create_migrated_book(
        db_session,
        household=household,
        category=category,
        storage_location=slot,
        legacy_book_id=20,
        title="Második könyv",
        author="Második szerző",
        publisher="Második kiadó",
        publish_year=2020,
        identifier_type="isbn13",
        identifier_value="9789632222222",
        borrowed_to=None,
        created_at=datetime(2026, 7, 15, 10, 0, 0),
    )

    create_migrated_book(
        db_session,
        household=household,
        category=category,
        storage_location=slot,
        legacy_book_id=10,
        title="Első könyv",
        author="Első szerző",
        publisher="Első kiadó",
        publish_year=2010,
        identifier_type="isbn13",
        identifier_value="9789631111111",
        borrowed_to=None,
        created_at=datetime(2026, 7, 14, 10, 0, 0),
    )

    inactive_item = create_migrated_book(
        db_session,
        household=household,
        category=category,
        storage_location=slot,
        legacy_book_id=30,
        title="Inaktív könyv",
        author=None,
        publisher=None,
        publish_year=None,
        identifier_type=None,
        identifier_value=None,
        borrowed_to=None,
        created_at=datetime(2026, 7, 16, 10, 0, 0),
    )

    inactive_item.is_active = False
    db_session.flush()

    records = list_all_books_for_export(
        db_session
    )

    assert [
        record.id
        for record in records
    ] == [
        10,
        20,
    ]

    assert records[0].title == "Első könyv"
    assert records[0].isbn == "9789631111111"
    assert records[0].author == "Első szerző"
    assert records[0].publisher == "Első kiadó"
    assert records[0].year == 2010
    assert records[0].room == "Nappali"
    assert records[0].shelf == "Újpolc"
    assert records[0].slot == 5
