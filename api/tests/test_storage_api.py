from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import (
    Category,
    CollectionItem,
    Household,
    ItemStorageAssignment,
    StorageLocation,
)


def create_test_household(
    session: Session,
) -> Household:
    household = Household(
        name="Storage API teszt",
        slug="storage-api-test",
        is_active=True,
    )

    session.add(household)
    session.flush()

    return household


def test_storage_tree_returns_hierarchy(
    test_client: TestClient,
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
    )

    db_session.add(room)
    db_session.flush()

    shelf = StorageLocation(
        household_id=household.id,
        parent_id=room.id,
        name="Könyvespolc",
        slug="konyvespolc",
        location_type="shelf",
        sort_order=10,
        is_active=True,
    )

    db_session.add(shelf)
    db_session.flush()

    slot = StorageLocation(
        household_id=household.id,
        parent_id=shelf.id,
        name="1. hely",
        slug="slot-1",
        location_type="slot",
        sort_order=10,
        is_active=True,
    )

    db_session.add(slot)
    db_session.flush()

    response = test_client.get(
        "/storage/tree",
        params={
            "household_id": household.id,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["household_id"] == household.id
    assert data["include_inactive"] is False
    assert len(data["locations"]) == 1

    room_data = data["locations"][0]

    assert room_data["public_id"] == room.public_id
    assert room_data["parent_public_id"] is None
    assert room_data["name"] == "Nappali"
    assert room_data["location_type"] == "room"
    assert len(room_data["children"]) == 1

    shelf_data = room_data["children"][0]

    assert shelf_data["public_id"] == shelf.public_id
    assert shelf_data["parent_public_id"] == room.public_id
    assert shelf_data["name"] == "Könyvespolc"
    assert shelf_data["location_type"] == "shelf"
    assert len(shelf_data["children"]) == 1

    slot_data = shelf_data["children"][0]

    assert slot_data["public_id"] == slot.public_id
    assert slot_data["parent_public_id"] == shelf.public_id
    assert slot_data["name"] == "1. hely"
    assert slot_data["location_type"] == "slot"
    assert slot_data["children"] == []


def test_storage_tree_can_include_inactive_locations(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_test_household(db_session)

    active_room = StorageLocation(
        household_id=household.id,
        parent_id=None,
        name="Aktív szoba",
        slug="aktiv-szoba",
        location_type="room",
        sort_order=10,
        is_active=True,
    )

    inactive_room = StorageLocation(
        household_id=household.id,
        parent_id=None,
        name="Inaktív szoba",
        slug="inaktiv-szoba",
        location_type="room",
        sort_order=20,
        is_active=False,
    )

    db_session.add_all([
        active_room,
        inactive_room,
    ])
    db_session.flush()

    default_response = test_client.get(
        "/storage/tree",
        params={
            "household_id": household.id,
        },
    )

    assert default_response.status_code == 200

    default_data = default_response.json()

    assert [
        location["name"]
        for location in default_data["locations"]
    ] == [
        "Aktív szoba",
    ]

    inactive_response = test_client.get(
        "/storage/tree",
        params={
            "household_id": household.id,
            "include_inactive": True,
        },
    )

    assert inactive_response.status_code == 200

    inactive_data = inactive_response.json()

    assert inactive_data["include_inactive"] is True

    assert [
        location["name"]
        for location in inactive_data["locations"]
    ] == [
        "Aktív szoba",
        "Inaktív szoba",
    ]

    assert inactive_data["locations"][0]["is_active"] is True
    assert inactive_data["locations"][1]["is_active"] is False


def test_storage_tree_rejects_invalid_household_id(
    test_client: TestClient,
) -> None:
    response = test_client.get(
        "/storage/tree",
        params={
            "household_id": 0,
        },
    )

    assert response.status_code == 400

    assert response.json() == {
        "detail": (
            "A household_id csak pozitív egész szám lehet."
        ),
    }


def test_create_storage_root_location(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_test_household(db_session)

    response = test_client.post(
        "/storage",
        json={
            "household_id": household.id,
            "name": "  Gyerekszoba  ",
            "location_type": "ROOM",
            "description": "  Felső emeleti szoba  ",
            "sort_order": 20,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["household_id"] == household.id
    assert data["parent_public_id"] is None
    assert data["name"] == "Gyerekszoba"
    assert data["slug"] == "gyerekszoba"
    assert data["location_type"] == "room"
    assert data["description"] == "Felső emeleti szoba"
    assert data["sort_order"] == 20
    assert data["is_active"] is True
    assert isinstance(data["public_id"], str)
    assert data["public_id"]

    location = (
        db_session.query(StorageLocation)
        .filter_by(
            public_id=data["public_id"],
        )
        .one()
    )

    assert location.parent_id is None
    assert location.household_id == household.id


def test_create_storage_child_location(
    test_client: TestClient,
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
    )

    db_session.add(room)
    db_session.flush()

    response = test_client.post(
        "/storage",
        json={
            "household_id": household.id,
            "parent_public_id": room.public_id,
            "name": "  Új polc  ",
            "slug": "  Új POLC  ",
            "location_type": "SHELF",
            "sort_order": 10,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["household_id"] == household.id
    assert data["parent_public_id"] == room.public_id
    assert data["name"] == "Új polc"
    assert data["slug"] == "uj-polc"
    assert data["location_type"] == "shelf"
    assert data["sort_order"] == 10
    assert data["is_active"] is True

    location = (
        db_session.query(StorageLocation)
        .filter_by(
            public_id=data["public_id"],
        )
        .one()
    )

    assert location.parent_id == room.id


def test_create_storage_rejects_duplicate_slug(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_test_household(db_session)

    first_response = test_client.post(
        "/storage",
        json={
            "household_id": household.id,
            "name": "Nappali",
            "slug": "nappali",
            "location_type": "room",
        },
    )

    assert first_response.status_code == 201

    duplicate_response = test_client.post(
        "/storage",
        json={
            "household_id": household.id,
            "name": "Másik nappali",
            "slug": "nappali",
            "location_type": "room",
        },
    )

    assert duplicate_response.status_code == 400

    assert duplicate_response.json() == {
        "detail": (
            "Ugyanilyen sluggal már létezik "
            "tárhely ezen a szinten."
        ),
    }


def test_create_storage_rejects_parent_from_other_household(
    test_client: TestClient,
    db_session: Session,
) -> None:
    first_household = create_test_household(db_session)

    second_household = Household(
        name="Másik háztartás",
        slug="masik-haztartas",
        is_active=True,
    )

    db_session.add(second_household)
    db_session.flush()

    parent = StorageLocation(
        household_id=first_household.id,
        parent_id=None,
        name="Nappali",
        slug="nappali",
        location_type="room",
        sort_order=10,
        is_active=True,
    )

    db_session.add(parent)
    db_session.flush()

    response = test_client.post(
        "/storage",
        json={
            "household_id": second_household.id,
            "parent_public_id": parent.public_id,
            "name": "Polc",
            "location_type": "shelf",
        },
    )

    assert response.status_code == 400

    assert response.json() == {
        "detail": (
            "A szülő tárhely nem ehhez "
            "a háztartáshoz tartozik."
        ),
    }


def test_create_storage_rejects_invalid_location_type(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_test_household(db_session)

    response = test_client.post(
        "/storage",
        json={
            "household_id": household.id,
            "name": "Hibás típus",
            "location_type": "spaceship",
        },
    )

    assert response.status_code == 400

    assert response.json() == {
        "detail": "Nem támogatott tárhelytípus.",
    }


def test_update_storage_location_updates_selected_fields(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_test_household(db_session)

    location = StorageLocation(
        household_id=household.id,
        parent_id=None,
        name="Régi név",
        slug="regi-nev",
        location_type="other",
        description="Régi leírás",
        sort_order=10,
        is_active=True,
    )

    db_session.add(location)
    db_session.flush()

    response = test_client.patch(
        f"/storage/{location.public_id}",
        json={
            "name": "  Új név  ",
            "slug": "  Új slug  ",
            "location_type": "SHELF",
            "description": "  Új leírás  ",
            "sort_order": 20,
            "is_active": False,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["public_id"] == location.public_id
    assert data["household_id"] == household.id
    assert data["parent_public_id"] is None
    assert data["name"] == "Új név"
    assert data["slug"] == "uj-slug"
    assert data["location_type"] == "shelf"
    assert data["description"] == "Új leírás"
    assert data["sort_order"] == 20
    assert data["is_active"] is False

    db_session.refresh(location)

    assert location.name == "Új név"
    assert location.slug == "uj-slug"
    assert location.location_type == "shelf"
    assert location.description == "Új leírás"
    assert location.sort_order == 20
    assert location.is_active is False


def test_update_storage_location_returns_not_found(
    test_client: TestClient,
) -> None:
    response = test_client.patch(
        "/storage/01KZZZZZZZZZZZZZZZZZZZZZZZ",
        json={
            "name": "Bármi",
        },
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "A tárhely nem található.",
    }


def test_update_storage_location_rejects_empty_request(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_test_household(db_session)

    location = StorageLocation(
        household_id=household.id,
        parent_id=None,
        name="Teszt hely",
        slug="teszt-hely",
        location_type="room",
        sort_order=10,
        is_active=True,
    )

    db_session.add(location)
    db_session.flush()

    response = test_client.patch(
        f"/storage/{location.public_id}",
        json={},
    )

    assert response.status_code == 400

    assert response.json() == {
        "detail": (
            "Legalább egy módosítandó mezőt "
            "meg kell adni."
        ),
    }


def test_delete_storage_location_deletes_unused_leaf(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_test_household(db_session)

    location = StorageLocation(
        household_id=household.id,
        parent_id=None,
        name="Törölhető hely",
        slug="torolheto-hely",
        location_type="slot",
        sort_order=10,
        is_active=True,
    )

    db_session.add(location)
    db_session.flush()

    public_id = location.public_id
    location_id = location.id

    response = test_client.delete(
        f"/storage/{public_id}"
    )

    assert response.status_code == 204
    assert response.content == b""

    assert (
        db_session.get(
            StorageLocation,
            location_id,
        )
        is None
    )


def test_delete_storage_location_rejects_location_with_children(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_test_household(db_session)

    parent = StorageLocation(
        household_id=household.id,
        parent_id=None,
        name="Szülő",
        slug="szulo",
        location_type="room",
        sort_order=10,
        is_active=True,
    )

    db_session.add(parent)
    db_session.flush()

    child = StorageLocation(
        household_id=household.id,
        parent_id=parent.id,
        name="Gyermek",
        slug="gyermek",
        location_type="shelf",
        sort_order=10,
        is_active=True,
    )

    db_session.add(child)
    db_session.flush()

    response = test_client.delete(
        f"/storage/{parent.public_id}"
    )

    assert response.status_code == 409

    assert response.json() == {
        "detail": (
            "A tárhely nem törölhető, "
            "mert gyermekelemek tartoznak hozzá."
        ),
    }


def test_delete_storage_location_rejects_assignment_history(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_test_household(db_session)

    category = Category(
        household_id=None,
        name="Könyv",
        slug="book",
        description="Teszt könyvkategória",
        icon="book",
        is_system=True,
        is_active=True,
        supports_barcode=True,
        metadata_lookup_type="manual",
        sort_order=10,
    )

    db_session.add(category)
    db_session.flush()

    location = StorageLocation(
        household_id=household.id,
        parent_id=None,
        name="Használt hely",
        slug="hasznalt-hely",
        location_type="slot",
        sort_order=10,
        is_active=True,
    )

    db_session.add(location)
    db_session.flush()

    item = CollectionItem(
        household_id=household.id,
        category_id=category.id,
        title="Tesztkönyv",
        status="active",
        is_active=True,
    )

    db_session.add(item)
    db_session.flush()

    assignment = ItemStorageAssignment(
        item_id=item.id,
        storage_location_id=location.id,
        is_active=False,
        movement_reason="test_history",
    )

    db_session.add(assignment)
    db_session.flush()

    response = test_client.delete(
        f"/storage/{location.public_id}"
    )

    assert response.status_code == 409

    assert response.json() == {
        "detail": (
            "A tárhely nem törölhető, "
            "mert gyűjteményi elem tárhelyelőzménye "
            "kapcsolódik hozzá."
        ),
    }


def test_delete_storage_location_returns_not_found(
    test_client: TestClient,
) -> None:
    response = test_client.delete(
        "/storage/01KZZZZZZZZZZZZZZZZZZZZZZZ"
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "A tárhely nem található.",
    }
