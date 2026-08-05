from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Household, StorageLocation


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
