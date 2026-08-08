from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import (
    Category,
    CategoryStorageLocation,
    Household,
    HouseholdMember,
    StorageLocation,
    User,
)


TEST_PASSWORD = "Categories-api-test-123"


def create_household(
    session: Session,
    *,
    name: str,
    slug: str,
) -> Household:
    household = Household(
        name=name,
        slug=slug,
        is_active=True,
    )

    session.add(household)
    session.flush()

    return household


def create_user(
    session: Session,
    *,
    household: Household,
    email: str,
    role: str,
    username: str | None = None,
) -> User:
    user = User(
        email=email,
        username=(
            username
            or email.split("@", 1)[0].lower()
        ),

        password_hash=hash_password(
            TEST_PASSWORD
        ),
        display_name=email,
        is_active=True,
        is_platform_admin=False,
        email_verified=True,
    )

    session.add(user)
    session.flush()

    membership = HouseholdMember(
        household_id=household.id,
        user_id=user.id,
        role=role,
        is_active=True,
    )

    session.add(membership)
    session.flush()

    return user


def create_category(
    session: Session,
    *,
    household_id: int | None,
    name: str,
    slug: str,
    is_system: bool,
    is_active: bool,
    sort_order: int,
) -> Category:
    category = Category(
        household_id=household_id,
        name=name,
        slug=slug,
        description=None,
        icon=None,
        is_system=is_system,
        is_active=is_active,
        supports_barcode=False,
        metadata_lookup_type="manual",
        sort_order=sort_order,
    )

    session.add(category)
    session.flush()

    return category


def login(
    client: TestClient,
    *,
    user: User,
) -> None:
    response = client.post(
        "/auth/login",
        json={
            "identifier": user.email,
            "password": TEST_PASSWORD,
        },
    )

    assert response.status_code == 200


def test_viewer_gets_active_available_categories(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_household(
        db_session,
        name="Category household",
        slug="category-api-household",
    )

    other_household = create_household(
        db_session,
        name="Other household",
        slug="category-api-other",
    )

    system_category = create_category(
        db_session,
        household_id=None,
        name="Könyv",
        slug="book",
        is_system=True,
        is_active=True,
        sort_order=10,
    )

    own_category = create_category(
        db_session,
        household_id=household.id,
        name="Társasjáték",
        slug="tarsasjatek",
        is_system=False,
        is_active=True,
        sort_order=20,
    )

    create_category(
        db_session,
        household_id=household.id,
        name="Inaktív",
        slug="inaktiv",
        is_system=False,
        is_active=False,
        sort_order=30,
    )

    create_category(
        db_session,
        household_id=other_household.id,
        name="Másiké",
        slug="masike",
        is_system=False,
        is_active=True,
        sort_order=40,
    )

    viewer = create_user(
        db_session,
        household=household,
        email="category-viewer@example.com",
        username="category-viewer",
        role="viewer",
    )

    login(
        test_client,
        user=viewer,
    )

    response = test_client.get(
        f"/households/"
        f"{household.id}/categories"
    )

    assert response.status_code == 200

    data = response.json()

    ids = {
        category["id"]
        for category in data
    }

    assert system_category.id in ids
    assert own_category.id in ids
    assert len(data) == 2

    assert [
        category["name"]
        for category in data
    ] == [
        "Könyv",
        "Társasjáték",
    ]


def test_other_household_is_forbidden(
    test_client: TestClient,
    db_session: Session,
) -> None:
    own_household = create_household(
        db_session,
        name="Own",
        slug="category-api-own",
    )

    other_household = create_household(
        db_session,
        name="Other",
        slug="category-api-forbidden",
    )

    viewer = create_user(
        db_session,
        household=own_household,
        email="category-cross@example.com",
        username="category-cross",
        role="viewer",
    )

    login(
        test_client,
        user=viewer,
    )

    response = test_client.get(
        f"/households/"
        f"{other_household.id}/categories"
    )

    assert response.status_code == 403


def test_anonymous_user_is_rejected(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_household(
        db_session,
        name="Anon",
        slug="category-api-anon",
    )

    response = test_client.get(
        f"/households/"
        f"{household.id}/categories"
    )

    assert response.status_code == 401


def test_viewer_gets_all_active_storage_without_rules(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_household(
        db_session,
        name="Allowed storage household",
        slug="allowed-storage-all",
    )

    category = create_category(
        db_session,
        household_id=None,
        name="Könyv",
        slug="allowed-storage-book",
        is_system=True,
        is_active=True,
        sort_order=10,
    )

    room = StorageLocation(
        household_id=household.id,
        parent_id=None,
        name="Szoba",
        slug="allowed-storage-room",
        location_type="room",
        sort_order=0,
        is_active=True,
    )

    db_session.add(room)
    db_session.flush()

    slot = StorageLocation(
        household_id=household.id,
        parent_id=room.id,
        name="1. hely",
        slug="allowed-storage-slot",
        location_type="slot",
        sort_order=10,
        is_active=True,
    )

    inactive_slot = StorageLocation(
        household_id=household.id,
        parent_id=room.id,
        name="Inaktív hely",
        slug="allowed-storage-inactive",
        location_type="slot",
        sort_order=20,
        is_active=False,
    )

    db_session.add_all(
        [
            slot,
            inactive_slot,
        ]
    )

    db_session.flush()

    viewer = create_user(
        db_session,
        household=household,
        email="allowed-storage-all@example.com",
        username="allowed-storage-all",
        role="viewer",
    )

    login(
        test_client,
        user=viewer,
    )

    response = test_client.get(
        f"/households/"
        f"{household.id}/categories/"
        f"{category.id}/allowed-storage"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["category_id"] == category.id
    assert data["restricted"] is False

    assert set(
        data["storage_public_ids"]
    ) == {
        room.public_id,
        slot.public_id,
    }

    assert (
        inactive_slot.public_id
        not in data["storage_public_ids"]
    )


def test_viewer_gets_restricted_storage_with_descendants(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_household(
        db_session,
        name="Restricted storage household",
        slug="allowed-storage-restricted",
    )

    category = create_category(
        db_session,
        household_id=None,
        name="Könyv",
        slug="allowed-storage-restricted-book",
        is_system=True,
        is_active=True,
        sort_order=10,
    )

    room = StorageLocation(
        household_id=household.id,
        parent_id=None,
        name="Szoba",
        slug="restricted-room",
        location_type="room",
        sort_order=0,
        is_active=True,
    )

    db_session.add(room)
    db_session.flush()

    shelf = StorageLocation(
        household_id=household.id,
        parent_id=room.id,
        name="Könyvespolc",
        slug="restricted-shelf",
        location_type="shelf",
        sort_order=10,
        is_active=True,
    )

    db_session.add(shelf)
    db_session.flush()

    first_slot = StorageLocation(
        household_id=household.id,
        parent_id=shelf.id,
        name="1. hely",
        slug="restricted-slot-1",
        location_type="slot",
        sort_order=10,
        is_active=True,
    )

    second_slot = StorageLocation(
        household_id=household.id,
        parent_id=shelf.id,
        name="2. hely",
        slug="restricted-slot-2",
        location_type="slot",
        sort_order=20,
        is_active=True,
    )

    other_slot = StorageLocation(
        household_id=household.id,
        parent_id=room.id,
        name="Másik hely",
        slug="restricted-other-slot",
        location_type="slot",
        sort_order=30,
        is_active=True,
    )

    db_session.add_all(
        [
            first_slot,
            second_slot,
            other_slot,
        ]
    )

    db_session.flush()

    db_session.add(
        CategoryStorageLocation(
            household_id=household.id,
            category_id=category.id,
            storage_location_id=shelf.id,
            include_descendants=True,
        )
    )

    db_session.flush()

    viewer = create_user(
        db_session,
        household=household,
        email="allowed-storage-restricted@example.com",
        username="allowed-storage-restricted",
        role="viewer",
    )

    login(
        test_client,
        user=viewer,
    )

    response = test_client.get(
        f"/households/"
        f"{household.id}/categories/"
        f"{category.id}/allowed-storage"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["restricted"] is True

    assert set(
        data["storage_public_ids"]
    ) == {
        shelf.public_id,
        first_slot.public_id,
        second_slot.public_id,
    }

    assert (
        room.public_id
        not in data["storage_public_ids"]
    )

    assert (
        other_slot.public_id
        not in data["storage_public_ids"]
    )


def test_allowed_storage_other_household_is_forbidden(
    test_client: TestClient,
    db_session: Session,
) -> None:
    own_household = create_household(
        db_session,
        name="Allowed storage own",
        slug="allowed-storage-own",
    )

    other_household = create_household(
        db_session,
        name="Allowed storage other",
        slug="allowed-storage-other",
    )

    category = create_category(
        db_session,
        household_id=None,
        name="Könyv",
        slug="allowed-storage-forbidden-book",
        is_system=True,
        is_active=True,
        sort_order=10,
    )

    viewer = create_user(
        db_session,
        household=own_household,
        email="allowed-storage-forbidden@example.com",
        username="allowed-storage-forbidden",
        role="viewer",
    )

    login(
        test_client,
        user=viewer,
    )

    response = test_client.get(
        f"/households/"
        f"{other_household.id}/categories/"
        f"{category.id}/allowed-storage"
    )

    assert response.status_code == 403
