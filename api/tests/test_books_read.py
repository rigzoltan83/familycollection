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
    soft_delete_book_by_legacy_id,
    update_collection_item_title,
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
