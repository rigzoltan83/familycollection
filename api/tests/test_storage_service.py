from sqlalchemy.orm import Session

from app.models import (
    Category,
    CollectionItem,
    Household,
    ItemStorageAssignment,
    StorageLocation,
)
from app.services import (
    StorageLocationCreateInput,
    StorageLocationUpdateInput,
    create_storage_location,
    delete_storage_location,
    list_storage_tree,
    update_storage_location,
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


def test_update_storage_location_updates_selected_fields(
    db_session: Session,
) -> None:
    household = create_test_household(db_session)

    location = create_storage_location(
        session=db_session,
        data=StorageLocationCreateInput(
            household_id=household.id,
            name="Régi név",
            slug="regi-nev",
            location_type="other",
            description="Régi leírás",
            sort_order=10,
            is_active=True,
        ),
    )

    updated = update_storage_location(
        session=db_session,
        public_id=location.public_id,
        data=StorageLocationUpdateInput(
            name="  Új név  ",
            slug="  Új slug  ",
            location_type="SHELF",
            description="  Új leírás  ",
            sort_order=20,
            is_active=False,
            fields_set={
                "name",
                "slug",
                "location_type",
                "description",
                "sort_order",
                "is_active",
            },
        ),
    )

    assert updated is not None
    assert updated.id == location.id
    assert updated.name == "Új név"
    assert updated.slug == "uj-slug"
    assert updated.location_type == "shelf"
    assert updated.description == "Új leírás"
    assert updated.sort_order == 20
    assert updated.is_active is False


def test_update_storage_location_preserves_unspecified_fields(
    db_session: Session,
) -> None:
    household = create_test_household(db_session)

    location = create_storage_location(
        session=db_session,
        data=StorageLocationCreateInput(
            household_id=household.id,
            name="Eredeti név",
            slug="eredeti-nev",
            location_type="cabinet",
            description="Eredeti leírás",
            sort_order=15,
            is_active=True,
        ),
    )

    updated = update_storage_location(
        session=db_session,
        public_id=location.public_id,
        data=StorageLocationUpdateInput(
            name="Módosított név",
            fields_set={
                "name",
            },
        ),
    )

    assert updated is not None
    assert updated.name == "Módosított név"
    assert updated.slug == "eredeti-nev"
    assert updated.location_type == "cabinet"
    assert updated.description == "Eredeti leírás"
    assert updated.sort_order == 15
    assert updated.is_active is True


def test_update_storage_location_rejects_duplicate_slug(
    db_session: Session,
) -> None:
    household = create_test_household(db_session)

    first_location = create_storage_location(
        session=db_session,
        data=StorageLocationCreateInput(
            household_id=household.id,
            name="Első hely",
            slug="elso-hely",
            location_type="room",
        ),
    )

    second_location = create_storage_location(
        session=db_session,
        data=StorageLocationCreateInput(
            household_id=household.id,
            name="Második hely",
            slug="masodik-hely",
            location_type="room",
        ),
    )

    try:
        update_storage_location(
            session=db_session,
            public_id=second_location.public_id,
            data=StorageLocationUpdateInput(
                slug=first_location.slug,
                fields_set={
                    "slug",
                },
            ),
        )
    except ValueError as error:
        assert "már létezik tárhely" in str(error)
    else:
        raise AssertionError(
            "ValueError kivételre számítottunk."
        )


def test_update_storage_location_rejects_invalid_location_type(
    db_session: Session,
) -> None:
    household = create_test_household(db_session)

    location = create_storage_location(
        session=db_session,
        data=StorageLocationCreateInput(
            household_id=household.id,
            name="Teszt hely",
            location_type="other",
        ),
    )

    try:
        update_storage_location(
            session=db_session,
            public_id=location.public_id,
            data=StorageLocationUpdateInput(
                location_type="spaceship",
                fields_set={
                    "location_type",
                },
            ),
        )
    except ValueError as error:
        assert "Nem támogatott tárhelytípus" in str(error)
    else:
        raise AssertionError(
            "ValueError kivételre számítottunk."
        )


def test_update_storage_location_returns_none_when_missing(
    db_session: Session,
) -> None:
    updated = update_storage_location(
        session=db_session,
        public_id="01KZZZZZZZZZZZZZZZZZZZZZZZ",
        data=StorageLocationUpdateInput(
            name="Bármi",
            fields_set={
                "name",
            },
        ),
    )

    assert updated is None


def test_delete_storage_location_deletes_unused_leaf(
    db_session: Session,
) -> None:
    household = create_test_household(db_session)

    location = create_storage_location(
        session=db_session,
        data=StorageLocationCreateInput(
            household_id=household.id,
            name="Törölhető hely",
            location_type="slot",
        ),
    )

    deleted = delete_storage_location(
        session=db_session,
        public_id=location.public_id,
    )

    assert deleted is True

    assert (
        db_session.get(
            StorageLocation,
            location.id,
        )
        is None
    )


def test_delete_storage_location_rejects_location_with_children(
    db_session: Session,
) -> None:
    household = create_test_household(db_session)

    parent = create_storage_location(
        session=db_session,
        data=StorageLocationCreateInput(
            household_id=household.id,
            name="Szülő",
            location_type="room",
        ),
    )

    create_storage_location(
        session=db_session,
        data=StorageLocationCreateInput(
            household_id=household.id,
            parent_public_id=parent.public_id,
            name="Gyermek",
            location_type="shelf",
        ),
    )

    try:
        delete_storage_location(
            session=db_session,
            public_id=parent.public_id,
        )
    except ValueError as error:
        assert "gyermekelemek tartoznak hozzá" in str(error)
    else:
        raise AssertionError(
            "ValueError kivételre számítottunk."
        )


def test_delete_storage_location_rejects_location_with_assignment_history(
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

    slot = create_storage_location(
        session=db_session,
        data=StorageLocationCreateInput(
            household_id=household.id,
            name="Használt tárhely",
            location_type="slot",
        ),
    )

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
        storage_location_id=slot.id,
        is_active=False,
        movement_reason="test_history",
    )

    db_session.add(assignment)
    db_session.flush()

    try:
        delete_storage_location(
            session=db_session,
            public_id=slot.public_id,
        )
    except ValueError as error:
        assert "tárhelyelőzménye kapcsolódik hozzá" in str(error)
    else:
        raise AssertionError(
            "ValueError kivételre számítottunk."
        )
