from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import (
    Category,
    Household,
    HouseholdMember,
    User,
)


TEST_PASSWORD = "Items-auth-test-123"


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


def create_category(
    session: Session,
) -> Category:
    category = Category(
        household_id=None,
        name="Items auth kategória",
        slug="items-auth-category",
        description=None,
        icon=None,
        is_system=True,
        is_active=True,
        supports_barcode=False,
        metadata_lookup_type="manual",
        sort_order=10,
    )

    session.add(category)
    session.flush()

    return category


def create_user(
    session: Session,
    *,
    household: Household,
    email: str,
    role: str,
) -> User:
    user = User(
        email=email,
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


def login(
    client: TestClient,
    *,
    user: User,
) -> None:
    response = client.post(
        "/auth/login",
        json={
            "email": user.email,
            "password": TEST_PASSWORD,
        },
    )

    assert response.status_code == 200


def create_item_as_editor(
    client: TestClient,
    *,
    household: Household,
    category: Category,
) -> dict:
    response = client.post(
        "/items",
        json={
            "household_id": household.id,
            "category_id": category.id,
            "title": "Authorization teszt tárgy",
        },
    )

    assert response.status_code == 201

    return response.json()


def test_anonymous_user_cannot_list_items(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_household(
        db_session,
        name="Anon household",
        slug="items-auth-anon",
    )

    response = test_client.get(
        "/items",
        params={
            "household_id": household.id,
        },
    )

    assert response.status_code == 401

    assert response.json() == {
        "detail": "Nincs bejelentkezve."
    }


def test_viewer_can_list_own_household_items(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_household(
        db_session,
        name="Viewer household",
        slug="items-auth-viewer",
    )

    viewer = create_user(
        db_session,
        household=household,
        email="items-viewer@example.com",
        role="viewer",
    )

    login(
        test_client,
        user=viewer,
    )

    response = test_client.get(
        "/items",
        params={
            "household_id": household.id,
        },
    )

    assert response.status_code == 200


def test_viewer_cannot_create_item(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_household(
        db_session,
        name="Viewer create household",
        slug="items-auth-viewer-create",
    )

    category = create_category(
        db_session
    )

    viewer = create_user(
        db_session,
        household=household,
        email="items-viewer-create@example.com",
        role="viewer",
    )

    login(
        test_client,
        user=viewer,
    )

    response = test_client.post(
        "/items",
        json={
            "household_id": household.id,
            "category_id": category.id,
            "title": "Tiltott tárgy",
        },
    )

    assert response.status_code == 403

    assert response.json() == {
        "detail": (
            "Nincs megfelelő jogosultsága "
            "ehhez a művelethez."
        )
    }


def test_editor_can_create_item(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_household(
        db_session,
        name="Editor household",
        slug="items-auth-editor",
    )

    category = create_category(
        db_session
    )

    editor = create_user(
        db_session,
        household=household,
        email="items-editor@example.com",
        role="editor",
    )

    login(
        test_client,
        user=editor,
    )

    response = test_client.post(
        "/items",
        json={
            "household_id": household.id,
            "category_id": category.id,
            "title": "Engedélyezett tárgy",
        },
    )

    assert response.status_code == 201


def test_user_cannot_list_other_household_items(
    test_client: TestClient,
    db_session: Session,
) -> None:
    own_household = create_household(
        db_session,
        name="Saját household",
        slug="items-auth-own",
    )

    other_household = create_household(
        db_session,
        name="Másik household",
        slug="items-auth-other",
    )

    viewer = create_user(
        db_session,
        household=own_household,
        email="items-cross-viewer@example.com",
        role="viewer",
    )

    login(
        test_client,
        user=viewer,
    )

    response = test_client.get(
        "/items",
        params={
            "household_id": other_household.id,
        },
    )

    assert response.status_code == 403

    assert response.json() == {
        "detail": (
            "Nincs jogosultsága ehhez "
            "a háztartáshoz."
        )
    }


def test_viewer_can_get_item_from_own_household(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_household(
        db_session,
        name="Get own household",
        slug="items-auth-get-own",
    )

    category = create_category(
        db_session
    )

    editor = create_user(
        db_session,
        household=household,
        email="items-get-editor@example.com",
        role="editor",
    )

    login(
        test_client,
        user=editor,
    )

    item = create_item_as_editor(
        test_client,
        household=household,
        category=category,
    )

    test_client.post(
        "/auth/logout"
    )

    viewer = create_user(
        db_session,
        household=household,
        email="items-get-viewer@example.com",
        role="viewer",
    )

    login(
        test_client,
        user=viewer,
    )

    response = test_client.get(
        f"/items/{item['public_id']}"
    )

    assert response.status_code == 200


def test_user_cannot_get_other_household_item(
    test_client: TestClient,
    db_session: Session,
) -> None:
    first_household = create_household(
        db_session,
        name="Első household",
        slug="items-auth-first",
    )

    second_household = create_household(
        db_session,
        name="Második household",
        slug="items-auth-second",
    )

    category = create_category(
        db_session
    )

    editor = create_user(
        db_session,
        household=first_household,
        email="items-first-editor@example.com",
        role="editor",
    )

    login(
        test_client,
        user=editor,
    )

    item = create_item_as_editor(
        test_client,
        household=first_household,
        category=category,
    )

    test_client.post(
        "/auth/logout"
    )

    other_viewer = create_user(
        db_session,
        household=second_household,
        email="items-second-viewer@example.com",
        role="viewer",
    )

    login(
        test_client,
        user=other_viewer,
    )

    response = test_client.get(
        f"/items/{item['public_id']}"
    )

    assert response.status_code == 403


def test_viewer_cannot_delete_item(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_household(
        db_session,
        name="Delete household",
        slug="items-auth-delete",
    )

    category = create_category(
        db_session
    )

    editor = create_user(
        db_session,
        household=household,
        email="items-delete-editor@example.com",
        role="editor",
    )

    login(
        test_client,
        user=editor,
    )

    item = create_item_as_editor(
        test_client,
        household=household,
        category=category,
    )

    test_client.post(
        "/auth/logout"
    )

    viewer = create_user(
        db_session,
        household=household,
        email="items-delete-viewer@example.com",
        role="viewer",
    )

    login(
        test_client,
        user=viewer,
    )

    response = test_client.delete(
        f"/items/{item['public_id']}"
    )

    assert response.status_code == 403
