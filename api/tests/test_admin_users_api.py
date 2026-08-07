from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import (
    Household,
    HouseholdMember,
    User,
)


TEST_PASSWORD = "Admin-api-teszt-123"


def create_household(
    session: Session,
) -> Household:
    household = Household(
        name="Admin API teszt",
        slug="admin-api-test",
        is_active=True,
    )

    session.add(household)
    session.flush()

    return household


def create_user_with_membership(
    session: Session,
    household: Household,
    *,
    email: str,
    role: str,
) -> tuple[User, HouseholdMember]:
    user = User(
        email=email,
        username=email.split("@", 1)[0].lower(),
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

    return user, membership


def login(
    client: TestClient,
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


def test_admin_users_requires_login(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_household(
        db_session
    )

    response = test_client.get(
        f"/admin/households/"
        f"{household.id}/users"
    )

    assert response.status_code == 401


def test_viewer_cannot_list_admin_users(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_household(
        db_session
    )

    user, _ = create_user_with_membership(
        db_session,
        household,
        email="viewer-api@example.com",
        role="viewer",
    )

    login(
        test_client,
        user.email,
    )

    response = test_client.get(
        f"/admin/households/"
        f"{household.id}/users"
    )

    assert response.status_code == 403


def test_editor_cannot_list_admin_users(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_household(
        db_session
    )

    user, _ = create_user_with_membership(
        db_session,
        household,
        email="editor-api@example.com",
        role="editor",
    )

    login(
        test_client,
        user.email,
    )

    response = test_client.get(
        f"/admin/households/"
        f"{household.id}/users"
    )

    assert response.status_code == 403


def test_admin_can_create_list_and_update_user(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_household(
        db_session
    )

    admin, _ = create_user_with_membership(
        db_session,
        household,
        email="admin-api@example.com",
        role="admin",
    )

    login(
        test_client,
        admin.email,
    )

    create_response = test_client.post(
        f"/admin/households/"
        f"{household.id}/users",
        json={
            "email": "NEW.USER@EXAMPLE.COM",
            "username": "newuser",
            "display_name": "Új API user",
            "password": "Uj-api-user-12345",
            "role": "viewer",
        },
    )

    assert create_response.status_code == 201

    created = create_response.json()

    assert (
        created["email"]
        == "new.user@example.com"
    )

    assert created["username"] == "newuser"

    assert (
        created["display_name"]
        == "Új API user"
    )

    assert created["role"] == "viewer"
    assert (
        created["membership_is_active"]
        is True
    )

    user_id = created["user_id"]

    list_response = test_client.get(
        f"/admin/households/"
        f"{household.id}/users"
    )

    assert list_response.status_code == 200

    users = list_response.json()

    assert len(users) == 2

    assert any(
        user["user_id"] == user_id
        for user in users
    )

    update_response = test_client.patch(
        f"/admin/households/"
        f"{household.id}/users/"
        f"{user_id}",
        json={
            "display_name": "Módosított user",
            "role": "editor",
            "membership_is_active": False,
        },
    )

    assert update_response.status_code == 200

    updated = update_response.json()

    assert (
        updated["display_name"]
        == "Módosított user"
    )

    assert updated["role"] == "editor"
    assert (
        updated["membership_is_active"]
        is False
    )


def test_owner_can_access_admin_users(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_household(
        db_session
    )

    owner, _ = create_user_with_membership(
        db_session,
        household,
        email="owner-api@example.com",
        role="owner",
    )

    login(
        test_client,
        owner.email,
    )

    response = test_client.get(
        f"/admin/households/"
        f"{household.id}/users"
    )

    assert response.status_code == 200


def test_admin_cannot_assign_owner_role(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_household(
        db_session
    )

    admin, _ = create_user_with_membership(
        db_session,
        household,
        email="admin-owner-api@example.com",
        role="admin",
    )

    login(
        test_client,
        admin.email,
    )

    response = test_client.post(
        f"/admin/households/"
        f"{household.id}/users",
        json={
            "email": "forbidden-owner@example.com",
            "display_name": "Tiltott owner",
            "password": "Tiltott-owner-123",
            "role": "owner",
        },
    )

    # A Pydantic Literal már a service előtt
    # elutasítja az owner értéket.
    assert response.status_code == 422


def test_admin_cannot_change_own_role(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_household(
        db_session
    )

    admin, _ = create_user_with_membership(
        db_session,
        household,
        email="self-role-api@example.com",
        role="admin",
    )

    login(
        test_client,
        admin.email,
    )

    response = test_client.patch(
        f"/admin/households/"
        f"{household.id}/users/"
        f"{admin.id}",
        json={
            "role": "viewer",
        },
    )

    assert response.status_code == 400

    assert response.json() == {
        "detail": (
            "A saját szerepkör nem "
            "módosítható."
        )
    }


def test_admin_cannot_deactivate_own_membership(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_household(
        db_session
    )

    admin, _ = create_user_with_membership(
        db_session,
        household,
        email="self-disable-api@example.com",
        role="admin",
    )

    login(
        test_client,
        admin.email,
    )

    response = test_client.patch(
        f"/admin/households/"
        f"{household.id}/users/"
        f"{admin.id}",
        json={
            "membership_is_active": False,
        },
    )

    assert response.status_code == 400

    assert response.json() == {
        "detail": (
            "A saját háztartási tagság "
            "nem tiltható le."
        )
    }


def test_admin_cannot_modify_owner(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_household(
        db_session
    )

    admin, _ = create_user_with_membership(
        db_session,
        household,
        email="admin-target-owner@example.com",
        role="admin",
    )

    owner, _ = create_user_with_membership(
        db_session,
        household,
        email="target-owner@example.com",
        role="owner",
    )

    login(
        test_client,
        admin.email,
    )

    response = test_client.patch(
        f"/admin/households/"
        f"{household.id}/users/"
        f"{owner.id}",
        json={
            "display_name": "Piszkált owner",
        },
    )

    assert response.status_code == 400

    assert response.json() == {
        "detail": (
            "Az owner tagság ezen a felületen "
            "nem módosítható."
        )
    }
