from datetime import datetime

from fastapi.testclient import TestClient
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


def create_test_household(
    session: Session,
) -> Household:
    household = Household(
        name="Books compat teszt",
        slug="books-compat-test",
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
        description="Books compat tesztkategória",
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
            legacy_location_id=5,
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


def test_books_latest_returns_legacy_compatible_json(
    test_client: TestClient,
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
        legacy_book_id=6,
        title="A három testőr Afrikában",
        author="Jenő Rejtő",
        publisher="Alexandra K.",
        publish_year=2007,
        identifier_type="isbn13",
        identifier_value="9789633694503",
        borrowed_to=None,
        created_at=datetime(2026, 7, 14, 8, 53, 42),
    )

    response = test_client.get("/books/latest")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1

    assert data[0] == {
        "id": 6,
        "title": "A három testőr Afrikában",
        "author": "Jenő Rejtő",
        "isbn": "9789633694503",
        "publisher": "Alexandra K.",
        "year": 2007,
        "added": "2026-07-14T08:53:42",
        "room": "Nappali",
        "shelf": "Újpolc",
        "slot": 5,
        "borrower": None,
    }


def test_books_all_returns_legacy_compatible_page(
    test_client: TestClient,
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

    response = test_client.get(
        "/books/all",
        params={
            "page": 1,
            "page_size": 50,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["page"] == 1
    assert data["page_size"] == 50
    assert data["total"] == 2
    assert data["total_pages"] == 1
    assert data["search"] == ""

    assert [
        book["id"]
        for book in data["books"]
    ] == [1, 2]

    assert data["books"][0]["isbn"] == "9789631111111"
    assert data["books"][0]["author"] == "Első szerző"
    assert data["books"][0]["room"] == "Nappali"
    assert data["books"][0]["shelf"] == "Újpolc"
    assert data["books"][0]["slot"] == 5

    assert data["books"][1]["borrower"] == "Teszt kölcsönző"


def test_books_all_supports_search(
    test_client: TestClient,
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

    response = test_client.get(
        "/books/all",
        params={
            "search": "Rejtő",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["search"] == "Rejtő"
    assert data["books"][0]["id"] == 1


def test_books_detail_returns_legacy_compatible_json(
    test_client: TestClient,
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
        legacy_book_id=6,
        title="A három testőr Afrikában",
        author="Jenő Rejtő",
        publisher="Alexandra K.",
        publish_year=2007,
        identifier_type="isbn13",
        identifier_value="9789633694503",
        borrowed_to=None,
        created_at=datetime(2026, 7, 14, 8, 53, 42),
    )

    response = test_client.get("/books/6")

    assert response.status_code == 200

    assert response.json() == {
        "id": 6,
        "isbn": "9789633694503",
        "title": "A három testőr Afrikában",
        "author": "Jenő Rejtő",
        "publisher": "Alexandra K.",
        "year": 2007,
        "created": "2026-07-14T08:53:42",
        "location_id": 5,
        "borrower": None,
        "room": "Nappali",
        "shelf": "Újpolc",
        "slot": 5,
    }


def test_books_detail_returns_not_found(
    test_client: TestClient,
) -> None:
    response = test_client.get("/books/999999")

    assert response.status_code == 200
    assert response.json() == {
        "status": "not_found",
        "message": "A könyv nem található.",
    }

def test_books_delete_soft_deletes_item(
    test_client: TestClient,
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

    response = test_client.delete("/books/6")

    assert response.status_code == 200
    assert response.json() == {
        "status": "deleted",
        "id": 6,
    }

    db_session.refresh(item)

    assert item.is_active is False

    detail_response = test_client.get("/books/6")

    assert detail_response.status_code == 200
    assert detail_response.json() == {
        "status": "not_found",
        "message": "A könyv nem található.",
    }


def test_books_delete_returns_not_found_for_missing_book(
    test_client: TestClient,
) -> None:
    response = test_client.delete("/books/999999")

    assert response.status_code == 200
    assert response.json() == {
        "status": "not_found",
        "message": "A könyv nem található.",
    }


def test_books_update_uses_collection_item_model(
    test_client: TestClient,
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
        description=(
            "[legacy-locations-seed:test] "
            "Régi helyiség: Dolgozó"
        ),
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
        description=(
            "[legacy-locations-seed:test] "
            "Régi polc/szekrény: Dolgozó / Könyvespolc"
        ),
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
        description=(
            "[legacy-locations-seed:test] "
            "Régi location_id=22; "
            "útvonal=Dolgozó / Könyvespolc / 2"
        ),
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

    response = test_client.put(
        "/books/6",
        json={
            "isbn": "978-963-222-222-2",
            "title": "  Új cím  ",
            "author": "  Új szerző  ",
            "publisher": "  Új kiadó  ",
            "publish_year": "2024",
            "location_id": 22,
            "borrower": "Ezt nem szabad megtartani",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "updated",
        "id": 6,
    }

    db_session.refresh(item)

    assert item.title == "Új cím"
    assert item.status == "active"

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
    assert assignments[1].is_active is True
    assert assignments[1].storage_location_id == target_slot.id

    migration = (
        db_session.query(LegacyBookMigration)
        .filter_by(
            legacy_book_id=6,
        )
        .one()
    )

    assert migration.legacy_isbn == "9789632222222"
    assert migration.legacy_borrowed_to is None
    assert migration.legacy_location_id is None
    assert migration.legacy_room == "Dolgozó"
    assert migration.legacy_shelf == "Könyvespolc"
    assert migration.legacy_slot == 2


def test_books_update_requires_borrower_for_loaned_location(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_test_book_category(db_session)

    source_slot = create_test_storage_hierarchy(
        db_session,
        household_id=household.id,
    )

    borrowed_room = StorageLocation(
        household_id=household.id,
        parent_id=None,
        name="Kölcsönadva",
        slug="kolcsonadva",
        location_type="area",
        sort_order=30,
        is_active=True,
        description=(
            "[legacy-locations-seed:test] "
            "Régi helyiség: Kölcsönadva"
        ),
    )

    db_session.add(borrowed_room)
    db_session.flush()

    borrowed_shelf = StorageLocation(
        household_id=household.id,
        parent_id=borrowed_room.id,
        name="-",
        slug="location",
        location_type="shelf",
        sort_order=10,
        is_active=True,
        description=(
            "[legacy-locations-seed:test] "
            "Régi polc/szekrény: Kölcsönadva / -"
        ),
    )

    db_session.add(borrowed_shelf)
    db_session.flush()

    borrowed_slot = StorageLocation(
        household_id=household.id,
        parent_id=borrowed_shelf.id,
        name="1. hely",
        slug="slot-1",
        location_type="slot",
        sort_order=10,
        is_active=True,
        description=(
            "[legacy-locations-seed:test] "
            "Régi location_id=26; "
            "útvonal=Kölcsönadva / - / 1"
        ),
    )

    db_session.add(borrowed_slot)
    db_session.flush()

    item = create_migrated_book(
        db_session,
        household=household,
        category=category,
        storage_location=source_slot,
        legacy_book_id=6,
        title="Tesztkönyv",
        author="Teszt szerző",
        publisher="Teszt kiadó",
        publish_year=2020,
        identifier_type="isbn13",
        identifier_value="9789631111111",
        borrowed_to=None,
        created_at=datetime(2026, 7, 14, 10, 0, 0),
    )

    missing_borrower_response = test_client.put(
        "/books/6",
        json={
            "isbn": "9789631111111",
            "title": "Tesztkönyv",
            "author": "Teszt szerző",
            "publisher": "Teszt kiadó",
            "publish_year": "2020",
            "location_id": 26,
            "borrower": None,
        },
    )

    assert missing_borrower_response.status_code == 200
    assert missing_borrower_response.json() == {
        "status": "error",
        "message": (
            "Kölcsönadásnál add meg, "
            "kinél van a könyv."
        ),
    }

    db_session.refresh(item)

    assert item.status == "active"

    successful_response = test_client.put(
        "/books/6",
        json={
            "isbn": "9789631111111",
            "title": "Tesztkönyv",
            "author": "Teszt szerző",
            "publisher": "Teszt kiadó",
            "publish_year": "2020",
            "location_id": 26,
            "borrower": "  Kovács Péter  ",
        },
    )

    assert successful_response.status_code == 200
    assert successful_response.json() == {
        "status": "updated",
        "id": 6,
    }

    db_session.refresh(item)

    assert item.status == "loaned"

    migration = (
        db_session.query(LegacyBookMigration)
        .filter_by(
            legacy_book_id=6,
        )
        .one()
    )

    assert migration.legacy_borrowed_to == "Kovács Péter"
    assert migration.legacy_room == "Kölcsönadva"
    assert migration.legacy_shelf == "-"
    assert migration.legacy_slot == 1

    active_assignment = (
        db_session.query(ItemStorageAssignment)
        .filter(
            ItemStorageAssignment.item_id == item.id,
            ItemStorageAssignment.is_active.is_(True),
        )
        .one()
    )

    assert (
        active_assignment.storage_location_id
        == borrowed_slot.id
    )


def test_books_manual_creates_book_in_collection_item_model(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_test_book_category(db_session)

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

    response = test_client.post(
        "/books/manual",
        json={
            "identifier": " Saját jelzet 42 ",
            "title": " Manuális könyv ",
            "author": " Rejtő Jenő ",
            "publisher": " Alexandra ",
            "publish_year": "2007",
            "location_id": 5,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "created"
    assert isinstance(data["id"], int)
    assert data["id"] > 0

    migration = (
        db_session.query(LegacyBookMigration)
        .filter_by(
            legacy_book_id=data["id"],
        )
        .one()
    )

    item = migration.collection_item

    assert item is not None
    assert item.title == "Manuális könyv"
    assert item.status == "active"
    assert item.household_id == household.id
    assert item.category_id == category.id

    identifier = (
        db_session.query(ItemIdentifier)
        .filter(
            ItemIdentifier.item_id == item.id,
            ItemIdentifier.is_primary.is_(True),
            ItemIdentifier.is_active.is_(True),
        )
        .one()
    )

    assert identifier.identifier_type == "custom"
    assert identifier.identifier_value == "Saját jelzet 42"

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
        .filter(
            ItemStorageAssignment.item_id == item.id,
            ItemStorageAssignment.is_active.is_(True),
        )
        .one()
    )

    assert assignment.storage_location_id == slot.id
    assert assignment.movement_reason == "manual_book_creation"

    assert migration.legacy_location_id == 5
    assert migration.legacy_isbn == "Saját jelzet 42"
    assert migration.legacy_room == "Nappali"
    assert migration.legacy_shelf == "Újpolc"
    assert migration.legacy_slot == 5


def test_books_manual_returns_error_for_unknown_location(
    test_client: TestClient,
    db_session: Session,
) -> None:
    create_test_household(db_session)
    create_test_book_category(db_session)

    response = test_client.post(
        "/books/manual",
        json={
            "identifier": "ABC-123",
            "title": "Teszt",
            "location_id": 999999,
        },
    )

    assert response.status_code == 200

    assert response.json() == {
        "status": "error",
        "message": "A kiválasztott tárhely nem található.",
    }


def test_books_manual_isbn_creates_book_in_collection_item_model(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_test_book_category(db_session)

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

    response = test_client.post(
        "/books/manual-isbn",
        json={
            "isbn": "978-963-369-450-3",
            "title": " Manuális ISBN könyv ",
            "author": " Rejtő Jenő ",
            "publisher": " Alexandra ",
            "publish_year": "2007",
            "location_id": 5,
            "borrower": "Ezt normál helyen el kell dobni",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "created"
    assert isinstance(data["id"], int)
    assert data["id"] > 0

    migration = (
        db_session.query(LegacyBookMigration)
        .filter_by(
            legacy_book_id=data["id"],
        )
        .one()
    )

    item = migration.collection_item

    assert item is not None
    assert item.title == "Manuális ISBN könyv"
    assert item.status == "active"
    assert item.household_id == household.id
    assert item.category_id == category.id

    identifier = (
        db_session.query(ItemIdentifier)
        .filter(
            ItemIdentifier.item_id == item.id,
            ItemIdentifier.is_primary.is_(True),
            ItemIdentifier.is_active.is_(True),
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
        .filter(
            ItemStorageAssignment.item_id == item.id,
            ItemStorageAssignment.is_active.is_(True),
        )
        .one()
    )

    assert assignment.storage_location_id == slot.id

    assert migration.legacy_location_id == 5
    assert migration.legacy_isbn == "9789633694503"
    assert migration.legacy_borrowed_to is None
    assert migration.legacy_room == "Nappali"
    assert migration.legacy_shelf == "Újpolc"
    assert migration.legacy_slot == 5


def test_books_manual_isbn_requires_borrower_for_loaned_location(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    create_test_book_category(db_session)

    borrowed_room = StorageLocation(
        household_id=household.id,
        parent_id=None,
        name="Kölcsönadva",
        slug="kolcsonadva",
        location_type="area",
        sort_order=30,
        is_active=True,
        description=(
            "[legacy-locations-seed:test] "
            "Régi helyiség: Kölcsönadva"
        ),
    )

    db_session.add(borrowed_room)
    db_session.flush()

    borrowed_shelf = StorageLocation(
        household_id=household.id,
        parent_id=borrowed_room.id,
        name="-",
        slug="location",
        location_type="shelf",
        sort_order=10,
        is_active=True,
        description=(
            "[legacy-locations-seed:test] "
            "Régi polc/szekrény: Kölcsönadva / -"
        ),
    )

    db_session.add(borrowed_shelf)
    db_session.flush()

    borrowed_slot = StorageLocation(
        household_id=household.id,
        parent_id=borrowed_shelf.id,
        name="1. hely",
        slug="slot-1",
        location_type="slot",
        sort_order=10,
        is_active=True,
        description=(
            "[legacy-locations-seed:test] "
            "Régi location_id=26; "
            "útvonal=Kölcsönadva / - / 1"
        ),
    )

    db_session.add(borrowed_slot)
    db_session.flush()

    missing = test_client.post(
        "/books/manual-isbn",
        json={
            "isbn": "9789633694503",
            "title": "Teszt",
            "location_id": 26,
            "borrower": None,
        },
    )

    assert missing.status_code == 200
    assert missing.json() == {
        "status": "error",
        "message": (
            "Kölcsönadásnál add meg, "
            "kinél van a könyv."
        ),
    }

    created = test_client.post(
        "/books/manual-isbn",
        json={
            "isbn": "9789633694503",
            "title": "Teszt",
            "location_id": 26,
            "borrower": "  Kovács Péter  ",
        },
    )

    assert created.status_code == 200

    data = created.json()

    migration = (
        db_session.query(LegacyBookMigration)
        .filter_by(
            legacy_book_id=data["id"],
        )
        .one()
    )

    item = migration.collection_item

    assert item.status == "loaned"
    assert migration.legacy_borrowed_to == "Kovács Péter"


def test_books_export_csv_uses_collection_item_model(
    test_client: TestClient,
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
        legacy_book_id=6,
        title="A három testőr Afrikában",
        author="Jenő Rejtő",
        publisher="Alexandra K.",
        publish_year=2007,
        identifier_type="isbn13",
        identifier_value="9789633694503",
        borrowed_to=None,
        created_at=datetime(2026, 7, 14, 8, 53, 42),
    )

    response = test_client.get(
        "/books/export.csv"
    )

    assert response.status_code == 200

    assert response.headers[
        "content-type"
    ].startswith(
        "text/csv"
    )

    assert (
        "attachment;"
        in response.headers[
            "content-disposition"
        ]
    )

    content = response.content.decode(
        "utf-8-sig"
    )

    lines = content.splitlines()

    assert lines[0] == (
        "Könyv ID;"
        "ISBN;"
        "Cím;"
        "Szerző;"
        "Kiadás éve;"
        "Kiadó;"
        "Felvitel dátuma;"
        "Utolsó módosítás;"
        "Kölcsönző;"
        "Helyiség;"
        "Polc;"
        "Tárhely;"
        "Teljes tárhely"
    )

    assert len(lines) == 2

    assert lines[1] == (
        "6;"
        "9789633694503;"
        "A három testőr Afrikában;"
        "Jenő Rejtő;"
        "2007;"
        "Alexandra K.;"
        "2026-07-14 08:53:42;"
        "2026-07-14 08:53:42;"
        ";"
        "Nappali;"
        "Újpolc;"
        "5;"
        "Nappali / Újpolc / Tárhely 5"
    )
