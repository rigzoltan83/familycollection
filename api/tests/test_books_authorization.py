from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import (
    Household,
    HouseholdMember,
    User,
)


TEST_PASSWORD = "Books-auth-test-123"


def create_test_household(
    session: Session,
) -> Household:
    household = Household(
        name="Books auth teszt",
        slug="books-auth-test",
        is_active=True,
    )

    session.add(household)
    session.flush()

    return household


def create_test_user(
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


def login(
    client: TestClient,
    *,
    email: str,
) -> None:
    response = client.post(
        "/auth/login",
        json={
            "identifier": email,
            "password": TEST_PASSWORD,
        },
    )

    assert response.status_code == 200


def test_viewer_cannot_delete_book(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_test_household(
        db_session
    )

    viewer = create_test_user(
        db_session,
        household=household,
        email="books-viewer@example.com",
        username="books-viewer",
        role="viewer",
    )

    login(
        test_client,
        email=viewer.email,
    )

    response = test_client.delete(
        "/books/999999999"
    )

    assert response.status_code == 403

    assert response.json() == {
        "detail": (
            "Nincs megfelelő jogosultsága "
            "ehhez a művelethez."
        )
    }


def test_editor_can_reach_delete_book(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_test_household(
        db_session
    )

    editor = create_test_user(
        db_session,
        household=household,
        email="books-editor@example.com",
        username="books-editor",
        role="editor",
    )

    login(
        test_client,
        email=editor.email,
    )

    response = test_client.delete(
        "/books/999999999"
    )

    assert response.status_code == 200

    assert response.json() == {
        "status": "not_found",
        "message": "A könyv nem található.",
    }


def test_anonymous_user_cannot_delete_book(
    test_client: TestClient,
) -> None:
    response = test_client.delete(
        "/books/999999999"
    )

    assert response.status_code == 401

    assert response.json() == {
        "detail": "Nincs bejelentkezve."
    }


def test_viewer_can_list_books(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_test_household(
        db_session
    )

    viewer = create_test_user(
        db_session,
        household=household,
        email="books-list-viewer@example.com",
        username="books-list-viewer",
        role="viewer",
    )

    login(
        test_client,
        email=viewer.email,
    )

    response = test_client.get(
        "/books/all"
    )

    assert response.status_code == 200


def test_anonymous_user_cannot_list_books(
    test_client: TestClient,
) -> None:
    response = test_client.get(
        "/books/all"
    )

    assert response.status_code == 401

    assert response.json() == {
        "detail": "Nincs bejelentkezve."
    }


def test_viewer_cannot_create_manual_book(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_test_household(
        db_session
    )

    viewer = create_test_user(
        db_session,
        household=household,
        email="books-create-viewer@example.com",
        username="books-create-viewer",
        role="viewer",
    )

    login(
        test_client,
        email=viewer.email,
    )

    response = test_client.post(
        "/books/manual",
        json={
            "identifier": "TEST-001",
            "title": "Tiltott könyv",
            "author": None,
            "publisher": None,
            "publish_year": None,
            "storage_public_id": None,
            "location_id": None,
        },
    )

    assert response.status_code == 403

    assert response.json() == {
        "detail": (
            "Nincs megfelelő jogosultsága "
            "ehhez a művelethez."
        )
    }


def test_viewer_cannot_update_book(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_test_household(
        db_session
    )

    viewer = create_test_user(
        db_session,
        household=household,
        email="books-update-viewer@example.com",
        username="books-update-viewer",
        role="viewer",
    )

    login(
        test_client,
        email=viewer.email,
    )

    response = test_client.put(
        "/books/999999999",
        json={
            "isbn": "9789631234567",
            "title": "Tiltott módosítás",
            "author": None,
            "publisher": None,
            "publish_year": None,
            "location_id": None,
            "storage_public_id": None,
            "borrower": None,
        },
    )

    assert response.status_code == 403


def test_viewer_can_export_books(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_test_household(
        db_session
    )

    viewer = create_test_user(
        db_session,
        household=household,
        email="books-export-viewer@example.com",
        username="books-export-viewer",
        role="viewer",
    )

    login(
        test_client,
        email=viewer.email,
    )

    response = test_client.get(
        "/books/export.csv"
    )

    assert response.status_code == 200


def test_anonymous_user_cannot_export_books(
    test_client: TestClient,
) -> None:
    response = test_client.get(
        "/books/export.csv"
    )

    assert response.status_code == 401

    assert response.json() == {
        "detail": "Nincs bejelentkezve."
    }
