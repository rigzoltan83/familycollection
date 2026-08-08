from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import (
    Category,
    Household,
    HouseholdMember,
    User,
)


TEST_PASSWORD = "Admin-category-fields-123"


def create_household(
    session: Session,
    *,
    name: str = "Admin field household",
    slug: str = "admin-field-household",
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
) -> User:
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

    return user


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


def create_custom_category(
    session: Session,
    *,
    household: Household,
) -> Category:
    category = Category(
        household_id=household.id,
        name="Társasjáték",
        slug="boardgame-admin-fields",
        description=None,
        icon=None,
        is_system=False,
        is_active=True,
        supports_barcode=False,
        metadata_lookup_type="manual",
        sort_order=10,
    )

    session.add(category)
    session.flush()

    return category


def test_admin_can_create_and_list_category_field(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_household(
        db_session
    )

    admin = create_user(
        db_session,
        household=household,
        email="field-admin@example.com",
        role="admin",
    )

    category = create_custom_category(
        db_session,
        household=household,
    )

    login(
        test_client,
        user=admin,
    )

    create_response = test_client.post(
        (
            f"/admin/households/{household.id}"
            f"/categories/{category.id}/fields"
        ),
        json={
            "name": "Játékidő",
            "field_key": "play-time",
            "field_type": "integer",
            "description": "Percben",
            "placeholder": "pl. 60",
            "is_required": True,
            "is_searchable": False,
            "is_filterable": True,
            "is_visible_in_list": True,
            "sort_order": 10,
            "validation_rules": {
                "minimum": 1,
                "maximum": 1440,
            },
            "default_value": {},
        },
    )

    assert create_response.status_code == 201

    created = create_response.json()

    assert created["name"] == "Játékidő"
    assert created["field_key"] == "play_time"
    assert created["field_type"] == "integer"
    assert created["is_required"] is True
    assert created["is_filterable"] is True
    assert created["is_visible_in_list"] is True
    assert created["is_active"] is True

    list_response = test_client.get(
        (
            f"/admin/households/{household.id}"
            f"/categories/{category.id}/fields"
        )
    )

    assert list_response.status_code == 200

    fields = list_response.json()

    assert len(fields) == 1
    assert fields[0]["id"] == created["id"]


def test_admin_can_update_category_field(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_household(
        db_session,
        name="Update field household",
        slug="update-field-household",
    )

    admin = create_user(
        db_session,
        household=household,
        email="update-field-admin@example.com",
        role="admin",
    )

    category = create_custom_category(
        db_session,
        household=household,
    )

    login(
        test_client,
        user=admin,
    )

    create_response = test_client.post(
        (
            f"/admin/households/{household.id}"
            f"/categories/{category.id}/fields"
        ),
        json={
            "name": "Kiadó",
            "field_key": "publisher",
            "field_type": "text",
            "is_visible_in_list": False,
        },
    )

    assert create_response.status_code == 201

    field_id = create_response.json()["id"]

    response = test_client.patch(
        (
            f"/admin/households/{household.id}"
            f"/categories/{category.id}"
            f"/fields/{field_id}"
        ),
        json={
            "name": "Játék kiadója",
            "is_searchable": True,
            "is_visible_in_list": True,
            "sort_order": 20,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Játék kiadója"
    assert data["field_key"] == "publisher"
    assert data["field_type"] == "text"
    assert data["is_searchable"] is True
    assert data["is_visible_in_list"] is True
    assert data["sort_order"] == 20


def test_admin_can_deactivate_category_field(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_household(
        db_session,
        name="Delete field household",
        slug="delete-field-household",
    )

    admin = create_user(
        db_session,
        household=household,
        email="delete-field-admin@example.com",
        role="admin",
    )

    category = create_custom_category(
        db_session,
        household=household,
    )

    login(
        test_client,
        user=admin,
    )

    create_response = test_client.post(
        (
            f"/admin/households/{household.id}"
            f"/categories/{category.id}/fields"
        ),
        json={
            "name": "Korhatár",
            "field_key": "age_limit",
            "field_type": "integer",
        },
    )

    assert create_response.status_code == 201

    field_id = create_response.json()["id"]

    delete_response = test_client.delete(
        (
            f"/admin/households/{household.id}"
            f"/categories/{category.id}"
            f"/fields/{field_id}"
        )
    )

    assert delete_response.status_code == 204

    list_response = test_client.get(
        (
            f"/admin/households/{household.id}"
            f"/categories/{category.id}/fields"
        )
    )

    assert list_response.status_code == 200

    fields = list_response.json()

    assert len(fields) == 1
    assert fields[0]["id"] == field_id
    assert fields[0]["is_active"] is False


def test_viewer_cannot_manage_category_fields(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_household(
        db_session,
        name="Viewer field household",
        slug="viewer-field-household",
    )

    viewer = create_user(
        db_session,
        household=household,
        email="field-viewer@example.com",
        role="viewer",
    )

    category = create_custom_category(
        db_session,
        household=household,
    )

    login(
        test_client,
        user=viewer,
    )

    response = test_client.post(
        (
            f"/admin/households/{household.id}"
            f"/categories/{category.id}/fields"
        ),
        json={
            "name": "Tiltott mező",
            "field_key": "forbidden",
            "field_type": "text",
        },
    )

    assert response.status_code == 403


def test_system_category_fields_cannot_be_modified(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_household(
        db_session,
        name="System field admin household",
        slug="system-field-admin-household",
    )

    admin = create_user(
        db_session,
        household=household,
        email="system-field-admin@example.com",
        role="admin",
    )

    category = Category(
        household_id=None,
        name="Rendszer kategória",
        slug="system-admin-field-test",
        description=None,
        icon=None,
        is_system=True,
        is_active=True,
        supports_barcode=False,
        metadata_lookup_type="manual",
        sort_order=10,
    )

    db_session.add(category)
    db_session.flush()

    login(
        test_client,
        user=admin,
    )

    response = test_client.post(
        (
            f"/admin/households/{household.id}"
            f"/categories/{category.id}/fields"
        ),
        json={
            "name": "Nem engedélyezett",
            "field_key": "forbidden_system",
            "field_type": "text",
        },
    )

    assert response.status_code == 400

    assert response.json() == {
        "detail": (
            "Rendszerkategória mezői ezen a "
            "felületen nem módosíthatók."
        )
    }
