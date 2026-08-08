from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import (
    Category,
    CategoryField,
    Household,
    HouseholdMember,
    User,
)


TEST_PASSWORD = "Admin-field-options-123"


def create_household(
    session: Session,
) -> Household:
    household = Household(
        name="Option admin household",
        slug="option-admin-household",
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


def create_category(
    session: Session,
    *,
    household: Household,
) -> Category:
    category = Category(
        household_id=household.id,
        name="Társasjáték",
        slug="option-admin-boardgame",
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


def create_field(
    session: Session,
    *,
    category: Category,
    field_type: str,
) -> CategoryField:
    field = CategoryField(
        category_id=category.id,
        name="Állapot",
        field_key="condition",
        field_type=field_type,
        description=None,
        placeholder=None,
        is_required=False,
        is_searchable=False,
        is_filterable=True,
        is_visible_in_list=True,
        is_active=True,
        sort_order=10,
        validation_rules={},
        default_value={},
    )

    session.add(field)
    session.flush()

    return field


def test_admin_can_create_and_list_options(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_household(
        db_session
    )

    admin = create_user(
        db_session,
        household=household,
        email="option-admin@example.com",
        role="admin",
    )

    category = create_category(
        db_session,
        household=household,
    )

    field = create_field(
        db_session,
        category=category,
        field_type="single_select",
    )

    login(
        test_client,
        user=admin,
    )

    create_response = test_client.post(
        (
            f"/admin/households/{household.id}"
            f"/categories/{category.id}"
            f"/fields/{field.id}/options"
        ),
        json={
            "value": "used",
            "label": "Használt",
            "sort_order": 10,
        },
    )

    assert create_response.status_code == 201

    created = create_response.json()

    assert created["value"] == "used"
    assert created["label"] == "Használt"
    assert created["sort_order"] == 10
    assert created["is_active"] is True

    list_response = test_client.get(
        (
            f"/admin/households/{household.id}"
            f"/categories/{category.id}"
            f"/fields/{field.id}/options"
        )
    )

    assert list_response.status_code == 200

    options = list_response.json()

    assert len(options) == 1
    assert options[0]["id"] == created["id"]


def test_admin_can_update_option(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_household(
        db_session
    )

    admin = create_user(
        db_session,
        household=household,
        email="option-update-admin@example.com",
        role="admin",
    )

    category = create_category(
        db_session,
        household=household,
    )

    field = create_field(
        db_session,
        category=category,
        field_type="single_select",
    )

    login(
        test_client,
        user=admin,
    )

    create_response = test_client.post(
        (
            f"/admin/households/{household.id}"
            f"/categories/{category.id}"
            f"/fields/{field.id}/options"
        ),
        json={
            "value": "new",
            "label": "Új",
            "sort_order": 20,
        },
    )

    assert create_response.status_code == 201

    option_id = create_response.json()["id"]

    response = test_client.patch(
        (
            f"/admin/households/{household.id}"
            f"/categories/{category.id}"
            f"/fields/{field.id}"
            f"/options/{option_id}"
        ),
        json={
            "label": "Újszerű",
            "sort_order": 5,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["value"] == "new"
    assert data["label"] == "Újszerű"
    assert data["sort_order"] == 5


def test_admin_can_deactivate_option(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_household(
        db_session
    )

    admin = create_user(
        db_session,
        household=household,
        email="option-delete-admin@example.com",
        role="admin",
    )

    category = create_category(
        db_session,
        household=household,
    )

    field = create_field(
        db_session,
        category=category,
        field_type="multi_select",
    )

    login(
        test_client,
        user=admin,
    )

    create_response = test_client.post(
        (
            f"/admin/households/{household.id}"
            f"/categories/{category.id}"
            f"/fields/{field.id}/options"
        ),
        json={
            "value": "family",
            "label": "Családi",
            "sort_order": 10,
        },
    )

    assert create_response.status_code == 201

    option_id = create_response.json()["id"]

    delete_response = test_client.delete(
        (
            f"/admin/households/{household.id}"
            f"/categories/{category.id}"
            f"/fields/{field.id}"
            f"/options/{option_id}"
        )
    )

    assert delete_response.status_code == 204

    list_response = test_client.get(
        (
            f"/admin/households/{household.id}"
            f"/categories/{category.id}"
            f"/fields/{field.id}/options"
        )
    )

    assert list_response.status_code == 200

    options = list_response.json()

    assert len(options) == 1
    assert options[0]["is_active"] is False


def test_non_select_field_rejects_options(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_household(
        db_session
    )

    admin = create_user(
        db_session,
        household=household,
        email="option-text-admin@example.com",
        role="admin",
    )

    category = create_category(
        db_session,
        household=household,
    )

    field = create_field(
        db_session,
        category=category,
        field_type="text",
    )

    login(
        test_client,
        user=admin,
    )

    response = test_client.post(
        (
            f"/admin/households/{household.id}"
            f"/categories/{category.id}"
            f"/fields/{field.id}/options"
        ),
        json={
            "value": "x",
            "label": "X",
            "sort_order": 10,
        },
    )

    assert response.status_code == 400

    assert response.json() == {
        "detail": (
            "Csak egyszeres vagy többszörös "
            "választás típusú mezőhöz "
            "adható válaszlehetőség."
        )
    }


def test_viewer_cannot_manage_options(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_household(
        db_session
    )

    viewer = create_user(
        db_session,
        household=household,
        email="option-viewer@example.com",
        role="viewer",
    )

    category = create_category(
        db_session,
        household=household,
    )

    field = create_field(
        db_session,
        category=category,
        field_type="single_select",
    )

    login(
        test_client,
        user=viewer,
    )

    response = test_client.post(
        (
            f"/admin/households/{household.id}"
            f"/categories/{category.id}"
            f"/fields/{field.id}/options"
        ),
        json={
            "value": "forbidden",
            "label": "Tiltott",
            "sort_order": 10,
        },
    )

    assert response.status_code == 403
