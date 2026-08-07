from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import (
    Category,
    Household,
    HouseholdMember,
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
