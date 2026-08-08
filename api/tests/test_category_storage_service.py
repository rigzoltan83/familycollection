from sqlalchemy.orm import Session

from app.models import (
    Category,
    CategoryStorageLocation,
    Household,
    StorageLocation,
)
from app.services import (
    get_allowed_storage_location_ids,
    is_storage_location_allowed,
    list_category_storage_rules,
    replace_category_storage_rules,
)

def create_household(
    session: Session,
) -> Household:
    household = Household(
        name="Category storage test",
        slug="category-storage-test",
        is_active=True,
    )

    session.add(household)
    session.flush()

    return household


def create_category(
    session: Session,
    household: Household,
) -> Category:
    category = Category(
        household_id=household.id,
        name="Teszt kategória",
        slug="teszt-kategoria",
        description=None,
        icon=None,
        is_system=False,
        is_active=True,
        supports_barcode=False,
        metadata_lookup_type="manual",
        sort_order=0,
    )

    session.add(category)
    session.flush()

    return category


def create_storage_tree(
    session: Session,
    household: Household,
) -> tuple[
    StorageLocation,
    StorageLocation,
    StorageLocation,
    StorageLocation,
]:
    room = StorageLocation(
        household_id=household.id,
        parent_id=None,
        name="Szoba",
        slug="szoba",
        location_type="room",
        sort_order=0,
        is_active=True,
    )

    session.add(room)
    session.flush()

    shelf = StorageLocation(
        household_id=household.id,
        parent_id=room.id,
        name="Polc",
        slug="polc",
        location_type="shelf",
        sort_order=0,
        is_active=True,
    )

    session.add(shelf)
    session.flush()

    first_slot = StorageLocation(
        household_id=household.id,
        parent_id=shelf.id,
        name="1. hely",
        slug="1-hely",
        location_type="slot",
        sort_order=0,
        is_active=True,
    )

    second_slot = StorageLocation(
        household_id=household.id,
        parent_id=shelf.id,
        name="2. hely",
        slug="2-hely",
        location_type="slot",
        sort_order=10,
        is_active=True,
    )

    session.add_all(
        [
            first_slot,
            second_slot,
        ]
    )

    session.flush()

    return (
        room,
        shelf,
        first_slot,
        second_slot,
    )


def test_without_rules_all_active_locations_are_allowed(
    db_session: Session,
) -> None:
    household = create_household(
        db_session
    )

    category = create_category(
        db_session,
        household,
    )

    (
        room,
        shelf,
        first_slot,
        second_slot,
    ) = create_storage_tree(
        db_session,
        household,
    )

    allowed_ids = (
        get_allowed_storage_location_ids(
            session=db_session,
            household_id=household.id,
            category_id=category.id,
        )
    )

    assert allowed_ids == {
        room.id,
        shelf.id,
        first_slot.id,
        second_slot.id,
    }


def test_exact_rule_without_descendants(
    db_session: Session,
) -> None:
    household = create_household(
        db_session
    )

    category = create_category(
        db_session,
        household,
    )

    (
        room,
        shelf,
        first_slot,
        second_slot,
    ) = create_storage_tree(
        db_session,
        household,
    )

    rule = CategoryStorageLocation(
        household_id=household.id,
        category_id=category.id,
        storage_location_id=shelf.id,
        include_descendants=False,
    )

    db_session.add(rule)
    db_session.flush()

    allowed_ids = (
        get_allowed_storage_location_ids(
            session=db_session,
            household_id=household.id,
            category_id=category.id,
        )
    )

    assert allowed_ids == {
        shelf.id,
    }

    assert is_storage_location_allowed(
        session=db_session,
        household_id=household.id,
        category_id=category.id,
        storage_location_id=shelf.id,
    )

    assert not is_storage_location_allowed(
        session=db_session,
        household_id=household.id,
        category_id=category.id,
        storage_location_id=first_slot.id,
    )

    assert not is_storage_location_allowed(
        session=db_session,
        household_id=household.id,
        category_id=category.id,
        storage_location_id=second_slot.id,
    )

    assert not is_storage_location_allowed(
        session=db_session,
        household_id=household.id,
        category_id=category.id,
        storage_location_id=room.id,
    )


def test_rule_with_descendants(
    db_session: Session,
) -> None:
    household = create_household(
        db_session
    )

    category = create_category(
        db_session,
        household,
    )

    (
        room,
        shelf,
        first_slot,
        second_slot,
    ) = create_storage_tree(
        db_session,
        household,
    )

    rule = CategoryStorageLocation(
        household_id=household.id,
        category_id=category.id,
        storage_location_id=shelf.id,
        include_descendants=True,
    )

    db_session.add(rule)
    db_session.flush()

    allowed_ids = (
        get_allowed_storage_location_ids(
            session=db_session,
            household_id=household.id,
            category_id=category.id,
        )
    )

    assert allowed_ids == {
        shelf.id,
        first_slot.id,
        second_slot.id,
    }

    assert not is_storage_location_allowed(
        session=db_session,
        household_id=household.id,
        category_id=category.id,
        storage_location_id=room.id,
    )


def test_inactive_locations_are_not_allowed(
    db_session: Session,
) -> None:
    household = create_household(
        db_session
    )

    category = create_category(
        db_session,
        household,
    )

    (
        room,
        shelf,
        first_slot,
        second_slot,
    ) = create_storage_tree(
        db_session,
        household,
    )

    second_slot.is_active = False

    rule = CategoryStorageLocation(
        household_id=household.id,
        category_id=category.id,
        storage_location_id=shelf.id,
        include_descendants=True,
    )

    db_session.add(rule)
    db_session.flush()

    allowed_ids = (
        get_allowed_storage_location_ids(
            session=db_session,
            household_id=household.id,
            category_id=category.id,
        )
    )

    assert room.id not in allowed_ids
    assert shelf.id in allowed_ids
    assert first_slot.id in allowed_ids
    assert second_slot.id not in allowed_ids


def test_replace_category_storage_rules_replaces_all_rules(
    db_session: Session,
) -> None:
    household = create_household(
        db_session
    )

    category = create_category(
        db_session,
        household,
    )

    (
        room,
        shelf,
        first_slot,
        second_slot,
    ) = create_storage_tree(
        db_session,
        household,
    )

    db_session.add(
        CategoryStorageLocation(
            household_id=household.id,
            category_id=category.id,
            storage_location_id=room.id,
            include_descendants=True,
        )
    )

    db_session.flush()

    rules = replace_category_storage_rules(
        session=db_session,
        household_id=household.id,
        category_id=category.id,
        rules=[
            (
                first_slot.public_id,
                False,
            ),
            (
                second_slot.public_id,
                True,
            ),
        ],
    )

    assert len(rules) == 2

    stored_rules = list_category_storage_rules(
        session=db_session,
        household_id=household.id,
        category_id=category.id,
    )

    assert len(stored_rules) == 2

    stored_by_location_id = {
        rule.storage_location_id: rule
        for rule in stored_rules
    }

    assert room.id not in stored_by_location_id

    assert (
        stored_by_location_id[
            first_slot.id
        ].include_descendants
        is False
    )

    assert (
        stored_by_location_id[
            second_slot.id
        ].include_descendants
        is True
    )


def test_replace_category_storage_rules_empty_list_removes_restriction(
    db_session: Session,
) -> None:
    household = create_household(
        db_session
    )

    category = create_category(
        db_session,
        household,
    )

    (
        room,
        shelf,
        first_slot,
        second_slot,
    ) = create_storage_tree(
        db_session,
        household,
    )

    db_session.add(
        CategoryStorageLocation(
            household_id=household.id,
            category_id=category.id,
            storage_location_id=shelf.id,
            include_descendants=True,
        )
    )

    db_session.flush()

    rules = replace_category_storage_rules(
        session=db_session,
        household_id=household.id,
        category_id=category.id,
        rules=[],
    )

    assert rules == []

    stored_rules = list_category_storage_rules(
        session=db_session,
        household_id=household.id,
        category_id=category.id,
    )

    assert stored_rules == []

    allowed_ids = (
        get_allowed_storage_location_ids(
            session=db_session,
            household_id=household.id,
            category_id=category.id,
        )
    )

    assert allowed_ids == {
        room.id,
        shelf.id,
        first_slot.id,
        second_slot.id,
    }


def test_replace_category_storage_rules_rejects_duplicate_location(
    db_session: Session,
) -> None:
    household = create_household(
        db_session
    )

    category = create_category(
        db_session,
        household,
    )

    (
        room,
        shelf,
        first_slot,
        second_slot,
    ) = create_storage_tree(
        db_session,
        household,
    )

    try:
        replace_category_storage_rules(
            session=db_session,
            household_id=household.id,
            category_id=category.id,
            rules=[
                (
                    first_slot.public_id,
                    False,
                ),
                (
                    first_slot.public_id,
                    True,
                ),
            ],
        )
    except ValueError as error:
        assert (
            str(error)
            == (
                "Ugyanaz a tárhely csak egyszer "
                "szerepelhet a szabályok között."
            )
        )
    else:
        raise AssertionError(
            "Duplikált tárhelyszabály "
            "nem okozott hibát."
        )


def test_replace_category_storage_rules_rejects_other_household_location(
    db_session: Session,
) -> None:
    household = create_household(
        db_session
    )

    category = create_category(
        db_session,
        household,
    )

    other_household = Household(
        name="Másik háztartás",
        slug="masik-haztartas",
        is_active=True,
    )

    db_session.add(
        other_household
    )

    db_session.flush()

    foreign_location = StorageLocation(
        household_id=other_household.id,
        parent_id=None,
        name="Másik háztartás tárhelye",
        slug="masik-haztartas-tarhely",
        location_type="slot",
        sort_order=0,
        is_active=True,
    )

    db_session.add(
        foreign_location
    )

    db_session.flush()

    try:
        replace_category_storage_rules(
            session=db_session,
            household_id=household.id,
            category_id=category.id,
            rules=[
                (
                    foreign_location.public_id,
                    False,
                ),
            ],
        )
    except ValueError as error:
        assert (
            str(error)
            == (
                "A megadott tárhely nem létezik "
                "ebben a háztartásban."
            )
        )
    else:
        raise AssertionError(
            "Másik háztartás tárhelye "
            "nem okozott hibát."
        )
