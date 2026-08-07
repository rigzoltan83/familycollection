from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import User


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

