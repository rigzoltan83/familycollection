from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from app.api.dependencies import (
    require_household_admin,
    require_household_editor,
    require_household_viewer,
)
from app.core.database import get_db_session
from app.core.security import hash_password
from app.models import (
    Household,
    HouseholdMember,
    User,
)
from settings import (
    SESSION_MAX_AGE_SECONDS,
    SESSION_SECRET_KEY,
)


TEST_EMAIL = "dependency-teszt@example.com"
TEST_PASSWORD = "Dependency-teszt-123"


def create_test_user(
    session: Session,
    *,
    is_active: bool = True,
) -> User:
    user = User(
        email=TEST_EMAIL,
        password_hash=hash_password(
            TEST_PASSWORD
        ),
        display_name="Dependency teszt user",
        is_active=is_active,
        is_platform_admin=False,
        email_verified=True,
    )

    session.add(user)
    session.flush()

    return user


def create_test_household(
    session: Session,
) -> Household:
    household = Household(
        name="Dependency teszt háztartás",
        slug="dependency-test-household",
        is_active=True,
    )

    session.add(household)
    session.flush()

    return household


def create_membership(
    session: Session,
    *,
    household: Household,
    user: User,
    role: str,
    is_active: bool = True,
) -> HouseholdMember:
    membership = HouseholdMember(
        household_id=household.id,
        user_id=user.id,
        role=role,
        is_active=is_active,
    )

    session.add(membership)
    session.flush()

    return membership


def create_dependency_test_app(
    db_session: Session,
) -> FastAPI:
    test_app = FastAPI()

    test_app.add_middleware(
        SessionMiddleware,
        secret_key=SESSION_SECRET_KEY,
        session_cookie="familycollection_session",
        max_age=SESSION_MAX_AGE_SECONDS,
        same_site="lax",
        https_only=False,
    )

    def override_get_db_session():
        yield db_session

    test_app.dependency_overrides[
        get_db_session
    ] = override_get_db_session

    @test_app.post("/test-login/{user_id}")
    def test_login(
        user_id: int,
        request: Request,
    ) -> dict[str, str]:
        request.session.clear()
        request.session["user_id"] = user_id

        return {
            "status": "authenticated",
        }

    @test_app.get(
        "/households/{household_id}/viewer"
    )
    def viewer_endpoint(
        household_id: int,
        membership=Depends(
            require_household_viewer
        ),
    ):
        return {
            "household_id":
                membership.household_id,
            "role":
                membership.role,
        }

    @test_app.get(
        "/households/{household_id}/editor"
    )
    def editor_endpoint(
        household_id: int,
        membership=Depends(
            require_household_editor
        ),
    ):
        return {
            "household_id":
                membership.household_id,
            "role":
                membership.role,
        }

    @test_app.get(
        "/households/{household_id}/admin"
    )
    def admin_endpoint(
        household_id: int,
        membership=Depends(
            require_household_admin
        ),
    ):
        return {
            "household_id":
                membership.household_id,
            "role":
                membership.role,
        }

    return test_app


def set_logged_in_user(
    client: TestClient,
    user: User,
) -> None:
    response = client.post(
        f"/test-login/{user.id}"
    )

    assert response.status_code == 200

    assert response.json() == {
        "status": "authenticated",
    }


def test_anonymous_user_gets_401(
    db_session: Session,
) -> None:
    household = create_test_household(
        db_session
    )

    test_app = create_dependency_test_app(
        db_session
    )

    with TestClient(
        test_app,
        base_url="http://testserver",
    ) as client:
        response = client.get(
            (
                f"/households/"
                f"{household.id}"
                f"/viewer"
            )
        )

    assert response.status_code == 401

    assert response.json() == {
        "detail":
            "Nincs bejelentkezve."
    }


def test_user_without_membership_gets_403(
    db_session: Session,
) -> None:
    user = create_test_user(
        db_session
    )

    household = create_test_household(
        db_session
    )

    test_app = create_dependency_test_app(
        db_session
    )

    with TestClient(
        test_app,
        base_url="http://testserver",
    ) as client:
        set_logged_in_user(
            client,
            user,
        )

        response = client.get(
            (
                f"/households/"
                f"{household.id}"
                f"/viewer"
            )
        )

    assert response.status_code == 403

    assert response.json() == {
        "detail":
            "Nincs jogosultsága ehhez "
            "a háztartáshoz."
    }


def test_inactive_membership_gets_403(
    db_session: Session,
) -> None:
    user = create_test_user(
        db_session
    )

    household = create_test_household(
        db_session
    )

    create_membership(
        db_session,
        household=household,
        user=user,
        role="owner",
        is_active=False,
    )

    test_app = create_dependency_test_app(
        db_session
    )

    with TestClient(
        test_app,
        base_url="http://testserver",
    ) as client:
        set_logged_in_user(
            client,
            user,
        )

        response = client.get(
            (
                f"/households/"
                f"{household.id}"
                f"/viewer"
            )
        )

    assert response.status_code == 403


def test_viewer_permissions(
    db_session: Session,
) -> None:
    user = create_test_user(
        db_session
    )

    household = create_test_household(
        db_session
    )

    create_membership(
        db_session,
        household=household,
        user=user,
        role="viewer",
    )

    test_app = create_dependency_test_app(
        db_session
    )

    with TestClient(
        test_app,
        base_url="http://testserver",
    ) as client:
        set_logged_in_user(
            client,
            user,
        )

        viewer_response = client.get(
            (
                f"/households/"
                f"{household.id}"
                f"/viewer"
            )
        )

        editor_response = client.get(
            (
                f"/households/"
                f"{household.id}"
                f"/editor"
            )
        )

        admin_response = client.get(
            (
                f"/households/"
                f"{household.id}"
                f"/admin"
            )
        )

    assert viewer_response.status_code == 200
    assert editor_response.status_code == 403
    assert admin_response.status_code == 403


def test_editor_permissions(
    db_session: Session,
) -> None:
    user = create_test_user(
        db_session
    )

    household = create_test_household(
        db_session
    )

    create_membership(
        db_session,
        household=household,
        user=user,
        role="editor",
    )

    test_app = create_dependency_test_app(
        db_session
    )

    with TestClient(
        test_app,
        base_url="http://testserver",
    ) as client:
        set_logged_in_user(
            client,
            user,
        )

        viewer_response = client.get(
            (
                f"/households/"
                f"{household.id}"
                f"/viewer"
            )
        )

        editor_response = client.get(
            (
                f"/households/"
                f"{household.id}"
                f"/editor"
            )
        )

        admin_response = client.get(
            (
                f"/households/"
                f"{household.id}"
                f"/admin"
            )
        )

    assert viewer_response.status_code == 200
    assert editor_response.status_code == 200
    assert admin_response.status_code == 403


def test_admin_permissions(
    db_session: Session,
) -> None:
    user = create_test_user(
        db_session
    )

    household = create_test_household(
        db_session
    )

    create_membership(
        db_session,
        household=household,
        user=user,
        role="admin",
    )

    test_app = create_dependency_test_app(
        db_session
    )

    with TestClient(
        test_app,
        base_url="http://testserver",
    ) as client:
        set_logged_in_user(
            client,
            user,
        )

        viewer_response = client.get(
            (
                f"/households/"
                f"{household.id}"
                f"/viewer"
            )
        )

        editor_response = client.get(
            (
                f"/households/"
                f"{household.id}"
                f"/editor"
            )
        )

        admin_response = client.get(
            (
                f"/households/"
                f"{household.id}"
                f"/admin"
            )
        )

    assert viewer_response.status_code == 200
    assert editor_response.status_code == 200
    assert admin_response.status_code == 200


def test_owner_permissions(
    db_session: Session,
) -> None:
    user = create_test_user(
        db_session
    )

    household = create_test_household(
        db_session
    )

    create_membership(
        db_session,
        household=household,
        user=user,
        role="owner",
    )

    test_app = create_dependency_test_app(
        db_session
    )

    with TestClient(
        test_app,
        base_url="http://testserver",
    ) as client:
        set_logged_in_user(
            client,
            user,
        )

        viewer_response = client.get(
            (
                f"/households/"
                f"{household.id}"
                f"/viewer"
            )
        )

        editor_response = client.get(
            (
                f"/households/"
                f"{household.id}"
                f"/editor"
            )
        )

        admin_response = client.get(
            (
                f"/households/"
                f"{household.id}"
                f"/admin"
            )
        )

    assert viewer_response.status_code == 200
    assert editor_response.status_code == 200
    assert admin_response.status_code == 200
