from sqlalchemy.orm import Session

from app.models import Household, StorageLocation
from app.services import (
    StorageLocationCreateInput,
    create_storage_location,
    list_storage_tree,
)

def create_test_household(
    session: Session,
) -> Household:
    household = Household(
        name="Storage service teszt",
        slug="storage-service-test",
        is_active=True,
    )

    session.add(household)
    session.flush()

    return household


def test_list_storage_tree_returns_hierarchy_in_order(
    db_session: Session,
) -> None:
    household = create_test_household(db_session)

    bedroom = StorageLocation(
        household_id=household.id,
        parent_id=None,
        name="Hálószoba",
        slug="haloszoba",
        location_type="room",
        sort_order=20,
        is_active=True,
    )

    living_room = StorageLocation(
        household_id=household.id,
        parent_id=None,
        name="Nappali",
        slug="nappali",
        location_type="room",
        sort_order=10,
        is_active=True,
    )

    db_session.add_all([
        bedroom,
        living_room,
    ])
    db_session.flush()

    second_shelf = StorageLocation(
        household_id=household.id,
        parent_id=living_room.id,
        name="Második polc",
        slug="masodik-polc",
        location_type="shelf",
        sort_order=20,
        is_active=True,
    )

    first_shelf = StorageLocation(
        household_id=household.id,
        parent_id=living_room.id,
        name="Első polc",
        slug="elso-polc",
        location_type="shelf",
        sort_order=10,
        is_active=True,
    )

    db_session.add_all([
        second_shelf,
        first_shelf,
    ])
    db_session.flush()

    second_slot = StorageLocation(
        household_id=household.id,
        parent_id=first_shelf.id,
        name="2. hely",
        slug="slot-2",
        location_type="slot",
        sort_order=20,
        is_active=True,
    )

    first_slot = StorageLocation(
        household_id=household.id,
        parent_id=first_shelf.id,
        name="1. hely",
        slug="slot-1",
        location_type="slot",
        sort_order=10,
        is_active=True,
    )

    db_session.add_all([
        second_slot,
        first_slot,
    ])
    db_session.flush()

    tree = list_storage_tree(
        db_session,
        household_id=household.id,
    )

    assert [
        node.name
        for node in tree
    ] == [
        "Nappali",
        "Hálószoba",
    ]

    assert [
        node.name
        for node in tree[0].children
    ] == [
        "Első polc",
        "Második polc",
    ]

    assert [
        node.name
        for node in tree[0].children[0].children
    ] == [
        "1. hely",
        "2. hely",
    ]

    first_slot_node = tree[0].children[0].children[0]

    assert first_slot_node.id == first_slot.id
    assert first_slot_node.public_id == first_slot.public_id
    assert first_slot_node.household_id == household.id
    assert first_slot_node.parent_id == first_shelf.id
    assert first_slot_node.slug == "slot-1"
    assert first_slot_node.location_type == "slot"
    assert first_slot_node.sort_order == 10
    assert first_slot_node.is_active is True


def test_list_storage_tree_excludes_inactive_locations_by_default(
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

    active_shelf = StorageLocation(
        household_id=household.id,
        parent_id=active_room.id,
        name="Aktív polc",
        slug="aktiv-polc",
        location_type="shelf",
        sort_order=10,
        is_active=True,
    )

    inactive_shelf = StorageLocation(
        household_id=household.id,
        parent_id=active_room.id,
        name="Inaktív polc",
        slug="inaktiv-polc",
        location_type="shelf",
        sort_order=20,
        is_active=False,
    )

    db_session.add_all([
        active_shelf,
        inactive_shelf,
    ])
    db_session.flush()

    tree = list_storage_tree(
        db_session,
        household_id=household.id,
    )

    assert [
        node.name
        for node in tree
    ] == [
        "Aktív szoba",
    ]

    assert [
        node.name
        for node in tree[0].children
    ] == [
        "Aktív polc",
    ]


def test_list_storage_tree_includes_inactive_locations_when_requested(
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

    tree = list_storage_tree(
        db_session,
        household_id=household.id,
        include_inactive=True,
    )

    assert [
        node.name
        for node in tree
    ] == [
        "Aktív szoba",
        "Inaktív szoba",
    ]

    assert tree[0].is_active is True
    assert tree[1].is_active is False


def test_create_storage_location_creates_root_location(
    db_session: Session,
) -> None:
    household = create_test_household(db_session)

    location = create_storage_location(
        session=db_session,
        data=StorageLocationCreateInput(
            household_id=household.id,
            name="  Gyerekszoba  ",
            location_type="ROOM",
            description="  Felső emeleti szoba  ",
            sort_order=20,
        ),
    )

    assert location.id is not None
    assert location.household_id == household.id
    assert location.parent_id is None
    assert location.name == "Gyerekszoba"
    assert location.slug == "gyerekszoba"
    assert location.location_type == "room"
    assert location.description == "Felső emeleti szoba"
    assert location.sort_order == 20
    assert location.is_active is True


def test_create_storage_location_creates_child_location(
    db_session: Session,
) -> None:
    household = create_test_household(db_session)

    room = create_storage_location(
        session=db_session,
        data=StorageLocationCreateInput(
            household_id=household.id,
            name="Nappali",
            location_type="room",
        ),
    )

    shelf = create_storage_location(
        session=db_session,
        data=StorageLocationCreateInput(
            household_id=household.id,
            parent_public_id=room.public_id,
            name="Új polc",
            location_type="shelf",
            slug="  Új POLC  ",
            sort_order=10,
        ),
    )

    assert shelf.parent_id == room.id
    assert shelf.household_id == household.id
    assert shelf.name == "Új polc"
    assert shelf.slug == "uj-polc"
    assert shelf.location_type == "shelf"

    tree = list_storage_tree(
        db_session,
        household_id=household.id,
    )

    assert len(tree) == 1
    assert tree[0].public_id == room.public_id
    assert len(tree[0].children) == 1
    assert tree[0].children[0].public_id == shelf.public_id


def test_create_storage_location_rejects_duplicate_slug_on_same_level(
    db_session: Session,
) -> None:
    household = create_test_household(db_session)

    create_storage_location(
        session=db_session,
        data=StorageLocationCreateInput(
            household_id=household.id,
            name="Nappali",
            location_type="room",
            slug="nappali",
        ),
    )

    try:
        create_storage_location(
            session=db_session,
            data=StorageLocationCreateInput(
                household_id=household.id,
                name="Másik nappali",
                location_type="room",
                slug="nappali",
            ),
        )
    except ValueError as error:
        assert "már létezik tárhely" in str(error)
    else:
        raise AssertionError(
            "ValueError kivételre számítottunk."
        )


def test_create_storage_location_rejects_parent_from_other_household(
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

    parent = create_storage_location(
        session=db_session,
        data=StorageLocationCreateInput(
            household_id=first_household.id,
            name="Nappali",
            location_type="room",
        ),
    )

    try:
        create_storage_location(
            session=db_session,
            data=StorageLocationCreateInput(
                household_id=second_household.id,
                parent_public_id=parent.public_id,
                name="Polc",
                location_type="shelf",
            ),
        )
    except ValueError as error:
        assert "nem ehhez a háztartáshoz tartozik" in str(error)
    else:
        raise AssertionError(
            "ValueError kivételre számítottunk."
        )


def test_create_storage_location_rejects_negative_sort_order(
    db_session: Session,
) -> None:
    household = create_test_household(db_session)

    try:
        create_storage_location(
            session=db_session,
            data=StorageLocationCreateInput(
                household_id=household.id,
                name="Hibás tárhely",
                location_type="room",
                sort_order=-1,
            ),
        )
    except ValueError as error:
        assert "sort_order nem lehet negatív" in str(error)
    else:
        raise AssertionError(
            "ValueError kivételre számítottunk."
        )
