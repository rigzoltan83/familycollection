import pytest

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Category,
    CategoryStorageLocation,
    CollectionItem,
    Household,
    ItemStorageAssignment,
    StorageLocation,
)
from app.services.item_storage import (
    get_active_item_storage_assignment,
    set_item_storage_location,
)


def create_household(
    session: Session,
    *,
    name: str,
    slug: str,
) -> Household:
    household = Household(
        name=name,
        slug=slug,
    )

    session.add(household)
    session.flush()

    return household


def create_category(
    session: Session,
    *,
    name: str,
    slug: str,
) -> Category:
    category = Category(
        household_id=None,
        name=name,
        slug=slug,
        is_system=True,
        is_active=True,
        supports_barcode=False,
        metadata_lookup_type="manual",
        sort_order=10,
    )

    session.add(category)
    session.flush()

    return category


def create_item(
    session: Session,
    *,
    household: Household,
    category: Category,
    title: str,
) -> CollectionItem:
    item = CollectionItem(
        household_id=household.id,
        category_id=category.id,
        title=title,
        status="active",
        is_active=True,
    )

    session.add(item)
    session.flush()

    return item


def create_storage_location(
    session: Session,
    *,
    household: Household,
    name: str,
    slug: str,
    location_type: str = "slot",
    is_active: bool = True,
) -> StorageLocation:
    location = StorageLocation(
        household_id=household.id,
        parent_id=None,
        name=name,
        slug=slug,
        location_type=location_type,
        sort_order=10,
        is_active=is_active,
    )

    session.add(location)
    session.flush()

    return location


def test_assign_item_to_storage_location(
    db_session: Session,
) -> None:
    household = create_household(
        db_session,
        name="Teszt háztartás",
        slug="storage-test-household",
    )

    category = create_category(
        db_session,
        name="Teszt kategória",
        slug="storage-test-category",
    )

    item = create_item(
        db_session,
        household=household,
        category=category,
        title="Teszt tárgy",
    )

    location = create_storage_location(
        db_session,
        household=household,
        name="1. rekesz",
        slug="slot-1",
    )

    assignment = set_item_storage_location(
        session=db_session,
        item=item,
        storage_public_id=location.public_id,
        movement_reason="test_assignment",
    )

    assert assignment is not None
    assert assignment.item_id == item.id
    assert assignment.storage_location_id == location.id
    assert assignment.is_active is True
    assert assignment.removed_at is None
    assert assignment.movement_reason == "test_assignment"

    active_assignment = (
        get_active_item_storage_assignment(
            session=db_session,
            item_id=item.id,
        )
    )

    assert active_assignment is not None
    assert active_assignment.id == assignment.id


def test_assign_same_storage_location_twice(
    db_session: Session,
) -> None:
    household = create_household(
        db_session,
        name="Teszt háztartás 2",
        slug="storage-test-household-2",
    )

    category = create_category(
        db_session,
        name="Teszt kategória 2",
        slug="storage-test-category-2",
    )

    item = create_item(
        db_session,
        household=household,
        category=category,
        title="Teszt tárgy 2",
    )

    location = create_storage_location(
        db_session,
        household=household,
        name="2. rekesz",
        slug="slot-2",
    )

    first_assignment = set_item_storage_location(
        session=db_session,
        item=item,
        storage_public_id=location.public_id,
    )

    second_assignment = set_item_storage_location(
        session=db_session,
        item=item,
        storage_public_id=location.public_id,
    )

    assert first_assignment is not None
    assert second_assignment is not None
    assert first_assignment.id == second_assignment.id

    assignments = db_session.scalars(
        select(ItemStorageAssignment).where(
            ItemStorageAssignment.item_id == item.id
        )
    ).all()

    assert len(assignments) == 1


def test_move_item_between_storage_locations(
    db_session: Session,
) -> None:
    household = create_household(
        db_session,
        name="Teszt háztartás 3",
        slug="storage-test-household-3",
    )

    category = create_category(
        db_session,
        name="Teszt kategória 3",
        slug="storage-test-category-3",
    )

    item = create_item(
        db_session,
        household=household,
        category=category,
        title="Teszt tárgy 3",
    )

    first_location = create_storage_location(
        db_session,
        household=household,
        name="Első rekesz",
        slug="first-slot",
    )

    second_location = create_storage_location(
        db_session,
        household=household,
        name="Második rekesz",
        slug="second-slot",
    )

    first_assignment = set_item_storage_location(
        session=db_session,
        item=item,
        storage_public_id=first_location.public_id,
    )

    second_assignment = set_item_storage_location(
        session=db_session,
        item=item,
        storage_public_id=second_location.public_id,
    )

    assert first_assignment is not None
    assert second_assignment is not None

    assert first_assignment.is_active is False
    assert first_assignment.removed_at is not None

    assert second_assignment.is_active is True
    assert second_assignment.removed_at is None
    assert (
        second_assignment.storage_location_id
        == second_location.id
    )

    active_assignments = db_session.scalars(
        select(ItemStorageAssignment).where(
            ItemStorageAssignment.item_id == item.id,
            ItemStorageAssignment.is_active.is_(True),
        )
    ).all()

    assert len(active_assignments) == 1


def test_reject_storage_from_other_household(
    db_session: Session,
) -> None:
    first_household = create_household(
        db_session,
        name="Első háztartás",
        slug="storage-first-household",
    )

    second_household = create_household(
        db_session,
        name="Második háztartás",
        slug="storage-second-household",
    )

    category = create_category(
        db_session,
        name="Teszt kategória 4",
        slug="storage-test-category-4",
    )

    item = create_item(
        db_session,
        household=first_household,
        category=category,
        title="Teszt tárgy 4",
    )

    location = create_storage_location(
        db_session,
        household=second_household,
        name="Idegen rekesz",
        slug="foreign-slot",
    )

    try:
        set_item_storage_location(
            session=db_session,
            item=item,
            storage_public_id=location.public_id,
        )
    except ValueError as error:
        assert "nem ehhez a háztartáshoz" in str(error)
    else:
        raise AssertionError(
            "ValueError kivételre számítottunk."
        )


def test_reject_non_slot_storage_location(
    db_session: Session,
) -> None:
    household = create_household(
        db_session,
        name="Teszt háztartás 5",
        slug="storage-test-household-5",
    )

    category = create_category(
        db_session,
        name="Teszt kategória 5",
        slug="storage-test-category-5",
    )

    item = create_item(
        db_session,
        household=household,
        category=category,
        title="Teszt tárgy 5",
    )

    location = create_storage_location(
        db_session,
        household=household,
        name="Szekrény",
        slug="cabinet",
        location_type="cabinet",
    )

    try:
        set_item_storage_location(
            session=db_session,
            item=item,
            storage_public_id=location.public_id,
        )
    except ValueError as error:
        assert "slot típusú" in str(error)
    else:
        raise AssertionError(
            "ValueError kivételre számítottunk."
        )


def test_reject_inactive_storage_location(
    db_session: Session,
) -> None:
    household = create_household(
        db_session,
        name="Teszt háztartás 6",
        slug="storage-test-household-6",
    )

    category = create_category(
        db_session,
        name="Teszt kategória 6",
        slug="storage-test-category-6",
    )

    item = create_item(
        db_session,
        household=household,
        category=category,
        title="Teszt tárgy 6",
    )

    location = create_storage_location(
        db_session,
        household=household,
        name="Inaktív rekesz",
        slug="inactive-slot",
        is_active=False,
    )

    try:
        set_item_storage_location(
            session=db_session,
            item=item,
            storage_public_id=location.public_id,
        )
    except ValueError as error:
        assert "nem aktív" in str(error)
    else:
        raise AssertionError(
            "ValueError kivételre számítottunk."
        )


def test_remove_current_storage_assignment(
    db_session: Session,
) -> None:
    household = create_household(
        db_session,
        name="Teszt háztartás 7",
        slug="storage-test-household-7",
    )

    category = create_category(
        db_session,
        name="Teszt kategória 7",
        slug="storage-test-category-7",
    )

    item = create_item(
        db_session,
        household=household,
        category=category,
        title="Teszt tárgy 7",
    )

    location = create_storage_location(
        db_session,
        household=household,
        name="3. rekesz",
        slug="slot-3",
    )

    assignment = set_item_storage_location(
        session=db_session,
        item=item,
        storage_public_id=location.public_id,
    )

    assert assignment is not None

    result = set_item_storage_location(
        session=db_session,
        item=item,
        storage_public_id=None,
    )

    assert result is None
    assert assignment.is_active is False
    assert assignment.removed_at is not None

    active_assignment = (
        get_active_item_storage_assignment(
            session=db_session,
            item_id=item.id,
        )
    )

    assert active_assignment is None

def test_set_item_storage_location_rejects_location_not_allowed_for_category(
    db_session: Session,
) -> None:
    household = create_household(
        db_session,
        name="Kategória tárhely tiltás",
        slug="category-storage-denied",
    )

    category = create_category(
        db_session,
        name="Kategória tárhely tiltás teszt",
        slug="category-storage-denied-category",
    )

    item = create_item(
        db_session,
        household=household,
        category=category,
        title="Tiltott tárhely teszt",
    )

    allowed_location = create_storage_location(
        db_session,
        household=household,
        name="Engedélyezett hely",
        slug="allowed-category-slot",
    )

    denied_location = create_storage_location(
        db_session,
        household=household,
        name="Tiltott hely",
        slug="denied-category-slot",
    )

    db_session.add(
        CategoryStorageLocation(
            household_id=household.id,
            category_id=category.id,
            storage_location_id=(
                allowed_location.id
            ),
            include_descendants=False,
        )
    )

    db_session.flush()

    with pytest.raises(
        ValueError,
        match=(
            "nem engedélyezett ehhez "
            "a kategóriához"
        ),
    ):
        set_item_storage_location(
            session=db_session,
            item=item,
            storage_public_id=(
                denied_location.public_id
            ),
        )


def test_set_item_storage_location_accepts_location_allowed_for_category(
    db_session: Session,
) -> None:
    household = create_household(
        db_session,
        name="Kategória tárhely engedély",
        slug="category-storage-allowed",
    )

    category = create_category(
        db_session,
        name="Kategória tárhely engedély teszt",
        slug="category-storage-allowed-category",
    )

    item = create_item(
        db_session,
        household=household,
        category=category,
        title="Engedélyezett tárhely teszt",
    )

    allowed_location = create_storage_location(
        db_session,
        household=household,
        name="Engedélyezett hely",
        slug="allowed-category-storage-slot",
    )

    db_session.add(
        CategoryStorageLocation(
            household_id=household.id,
            category_id=category.id,
            storage_location_id=(
                allowed_location.id
            ),
            include_descendants=False,
        )
    )

    db_session.flush()

    assignment = set_item_storage_location(
        session=db_session,
        item=item,
        storage_public_id=(
            allowed_location.public_id
        ),
    )

    assert assignment is not None
    assert (
        assignment.storage_location_id
        == allowed_location.id
    )
    assert assignment.is_active is True
