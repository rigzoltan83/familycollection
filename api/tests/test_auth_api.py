from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import (
    Household,
    HouseholdMember,
    User,
)


TEST_EMAIL = "api-teszt@example.com"
TEST_PASSWORD = "FamilyCollection-api-teszt-123"


def create_api_test_user(
    session: Session,
) -> User:
    user = User(
        email=TEST_EMAIL,
        password_hash=hash_password(TEST_PASSWORD),
        display_name="API teszt felhasználó",
        is_active=True,
        is_platform_admin=True,
        email_verified=True,
    )

    session.add(user)
    session.flush()

    return user


def test_login_returns_authenticated_user(
    test_client: TestClient,
    db_session: Session,
) -> None:
    user = create_api_test_user(db_session)

    response = test_client.post(
        "/auth/login",
        json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "authenticated"
    assert data["user"]["id"] == user.id
    assert data["user"]["email"] == TEST_EMAIL
    assert data["user"]["display_name"] == "API teszt felhasználó"
    assert data["user"]["is_platform_admin"] is True
    assert "password_hash" not in data["user"]


def test_login_rejects_wrong_password(
    test_client: TestClient,
    db_session: Session,
) -> None:
    create_api_test_user(db_session)

    response = test_client.post(
        "/auth/login",
        json={
            "email": TEST_EMAIL,
            "password": "rossz-jelszo",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Hibás e-mail cím vagy jelszó."
    }


def test_auth_context_returns_active_households(
    test_client: TestClient,
    db_session: Session,
) -> None:
    user = create_api_test_user(
        db_session
    )

    active_household = Household(
        name="Aktív család",
        slug="aktiv-csalad",
        is_active=True,
    )

    inactive_household = Household(
        name="Inaktív család",
        slug="inaktiv-csalad",
        is_active=False,
    )

    db_session.add_all(
        [
            active_household,
            inactive_household,
        ]
    )

    db_session.flush()

    db_session.add_all(
        [
            HouseholdMember(
                household_id=active_household.id,
                user_id=user.id,
                role="admin",
                is_active=True,
            ),
            HouseholdMember(
                household_id=inactive_household.id,
                user_id=user.id,
                role="owner",
                is_active=True,
            ),
        ]
    )

    db_session.flush()

    login_response = test_client.post(
        "/auth/login",
        json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
        },
    )

    assert login_response.status_code == 200

    response = test_client.get(
        "/auth/context"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["user"]["id"] == user.id
    assert data["user"]["email"] == TEST_EMAIL

    assert data["households"] == [
        {
            "id": active_household.id,
            "name": "Aktív család",
            "slug": "aktiv-csalad",
            "role": "admin",
        }
    ]
