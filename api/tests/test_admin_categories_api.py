from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import (
    Category,
    Household,
    HouseholdMember,
    StorageLocation,
    User,
)


TEST_PASSWORD = "Admin-category-api-123"


def create_test_household(
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


def create_system_category(
    session: Session,
) -> Category:
    category = Category(
        household_id=None,
        name="Könyv",
        slug="book",
        description="Rendszerkategória",
        icon="book",
        is_system=True,
        is_active=True,
        supports_barcode=True,
        metadata_lookup_type="isbn",
        sort_order=10,
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


def test_admin_can_list_categories(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_test_household(
        db_session,
        name="Admin list household",
        slug="admin-category-list",
    )

    create_system_category(
        db_session
    )

    admin = create_test_user(
        db_session,
        household=household,
        email="category-admin-list@example.com",
        username="category-admin-list",
        role="admin",
    )

    login(
        test_client,
        user=admin,
    )

    response = test_client.get(
        f"/admin/households/"
        f"{household.id}/categories"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["name"] == "Könyv"
    assert data[0]["is_system"] is True


def test_admin_can_create_category(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_test_household(
        db_session,
        name="Admin create household",
        slug="admin-category-create",
    )

    admin = create_test_user(
        db_session,
        household=household,
        email="category-admin-create@example.com",
        username="category-admin-create",
        role="admin",
    )

    login(
        test_client,
        user=admin,
    )

    response = test_client.post(
        f"/admin/households/"
        f"{household.id}/categories",
        json={
            "name": "Társasjátékok",
            "description": (
                "Saját társasjáték-gyűjtemény"
            ),
            "icon": "game",
            "supports_barcode": True,
            "sort_order": 20,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["household_id"] == household.id
    assert data["name"] == "Társasjátékok"
    assert data["slug"] == "tarsasjatekok"
    assert data["description"] == (
        "Saját társasjáték-gyűjtemény"
    )
    assert data["icon"] == "game"
    assert data["is_system"] is False
    assert data["is_active"] is True
    assert data["supports_barcode"] is True
    assert data["metadata_lookup_type"] == "manual"
    assert data["sort_order"] == 20


def test_admin_can_update_category(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_test_household(
        db_session,
        name="Admin update household",
        slug="admin-category-update",
    )

    admin = create_test_user(
        db_session,
        household=household,
        email="category-admin-update@example.com",
        username="category-admin-update",
        role="admin",
    )

    login(
        test_client,
        user=admin,
    )

    create_response = test_client.post(
        f"/admin/households/"
        f"{household.id}/categories",
        json={
            "name": "Régi kategória",
        },
    )

    assert create_response.status_code == 201

    category_id = (
        create_response.json()["id"]
    )

    response = test_client.patch(
        f"/admin/households/"
        f"{household.id}/categories/"
        f"{category_id}",
        json={
            "name": "Új kategória",
            "icon": "star",
            "supports_barcode": True,
            "sort_order": 30,
            "is_active": False,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Új kategória"
    assert data["slug"] == "uj-kategoria"
    assert data["icon"] == "star"
    assert data["supports_barcode"] is True
    assert data["sort_order"] == 30
    assert data["is_active"] is False


def test_system_category_cannot_be_updated(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_test_household(
        db_session,
        name="System category household",
        slug="admin-category-system",
    )

    system_category = create_system_category(
        db_session
    )

    admin = create_test_user(
        db_session,
        household=household,
        email="category-admin-system@example.com",
        username="category-admin-system",
        role="admin",
    )

    login(
        test_client,
        user=admin,
    )

    response = test_client.patch(
        f"/admin/households/"
        f"{household.id}/categories/"
        f"{system_category.id}",
        json={
            "name": "Átírt könyv",
        },
    )

    assert response.status_code == 400

    assert response.json() == {
        "detail": (
            "Rendszerkategória nem módosítható."
        )
    }


def test_viewer_cannot_list_categories(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_test_household(
        db_session,
        name="Viewer household",
        slug="admin-category-viewer",
    )

    viewer = create_test_user(
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
        f"/admin/households/"
        f"{household.id}/categories"
    )

    assert response.status_code == 403


def test_editor_cannot_create_category(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_test_household(
        db_session,
        name="Editor household",
        slug="admin-category-editor",
    )

    editor = create_test_user(
        db_session,
        household=household,
        email="category-editor@example.com",
        username="category-editor",
        role="editor",
    )

    login(
        test_client,
        user=editor,
    )

    response = test_client.post(
        f"/admin/households/"
        f"{household.id}/categories",
        json={
            "name": "Tiltott kategória",
        },
    )

    assert response.status_code == 403


def test_admin_cannot_access_other_household_categories(
    test_client: TestClient,
    db_session: Session,
) -> None:
    own_household = create_test_household(
        db_session,
        name="Saját household",
        slug="admin-category-own",
    )

    other_household = create_test_household(
        db_session,
        name="Másik household",
        slug="admin-category-other",
    )

    admin = create_test_user(
        db_session,
        household=own_household,
        email="category-cross-admin@example.com",
        username="category-cross-admin",
        role="admin",
    )

    login(
        test_client,
        user=admin,
    )

    response = test_client.get(
        f"/admin/households/"
        f"{other_household.id}/categories"
    )

    assert response.status_code == 403


def test_owner_can_create_category(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_test_household(
        db_session,
        name="Owner household",
        slug="admin-category-owner",
    )

    owner = create_test_user(
        db_session,
        household=household,
        email="category-owner@example.com",
        username="category-owner",
        role="owner",
    )

    login(
        test_client,
        user=owner,
    )

    response = test_client.post(
        f"/admin/households/"
        f"{household.id}/categories",
        json={
            "name": "Owner kategória",
        },
    )

    assert response.status_code == 201
    assert response.json()["name"] == (
        "Owner kategória"
    )


def test_empty_patch_is_rejected(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_test_household(
        db_session,
        name="Empty patch household",
        slug="admin-category-empty-patch",
    )

    admin = create_test_user(
        db_session,
        household=household,
        email="category-empty-patch@example.com",
        username="category-empty-patch",
        role="admin",
    )

    login(
        test_client,
        user=admin,
    )

    create_response = test_client.post(
        f"/admin/households/"
        f"{household.id}/categories",
        json={
            "name": "Patch kategória",
        },
    )

    assert create_response.status_code == 201

    category_id = (
        create_response.json()["id"]
    )

    response = test_client.patch(
        f"/admin/households/"
        f"{household.id}/categories/"
        f"{category_id}",
        json={},
    )

    assert response.status_code == 400

    assert response.json() == {
        "detail": (
            "Legalább egy módosítandó mezőt "
            "meg kell adni."
        )
    }


def test_admin_can_get_empty_category_storage_rules(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_test_household(
        db_session,
        name="Storage rules GET household",
        slug="storage-rules-get",
    )

    category = create_system_category(
        db_session
    )

    admin = create_test_user(
        db_session,
        household=household,
        email="storage-rules-get@example.com",
        username="storage-rules-get",
        role="admin",
    )

    login(
        test_client,
        user=admin,
    )

    response = test_client.get(
        f"/admin/households/"
        f"{household.id}/categories/"
        f"{category.id}/storage-rules"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["category_id"] == category.id
    assert data["restricted"] is False
    assert data["rules"] == []


def test_admin_can_replace_and_read_category_storage_rules(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_test_household(
        db_session,
        name="Storage rules PUT household",
        slug="storage-rules-put",
    )

    category = create_system_category(
        db_session
    )

    admin = create_test_user(
        db_session,
        household=household,
        email="storage-rules-put@example.com",
        username="storage-rules-put",
        role="admin",
    )

    location = StorageLocation(
        household_id=household.id,
        parent_id=None,
        name="Teszt tárhely",
        slug="teszt-tarhely",
        location_type="slot",
        sort_order=0,
        is_active=True,
    )

    db_session.add(location)
    db_session.flush()

    login(
        test_client,
        user=admin,
    )

    response = test_client.put(
        f"/admin/households/"
        f"{household.id}/categories/"
        f"{category.id}/storage-rules",
        json={
            "rules": [
                {
                    "storage_location_public_id":
                        location.public_id,
                    "include_descendants":
                        True,
                }
            ]
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["category_id"] == category.id
    assert data["restricted"] is True
    assert len(data["rules"]) == 1
    assert (
        data["rules"][0]["storage_location_public_id"]
        == location.public_id
    )
    assert (
        data["rules"][0]["include_descendants"]
        is True
    )

    get_response = test_client.get(
        f"/admin/households/"
        f"{household.id}/categories/"
        f"{category.id}/storage-rules"
    )

    assert get_response.status_code == 200

    get_data = get_response.json()

    assert get_data["restricted"] is True
    assert len(get_data["rules"]) == 1
    assert (
        get_data["rules"][0]["storage_location_public_id"]
        == location.public_id
    )


def test_admin_can_remove_category_storage_restriction(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_test_household(
        db_session,
        name="Storage rules clear household",
        slug="storage-rules-clear",
    )

    category = create_system_category(
        db_session
    )

    admin = create_test_user(
        db_session,
        household=household,
        email="storage-rules-clear@example.com",
        username="storage-rules-clear",
        role="admin",
    )

    location = StorageLocation(
        household_id=household.id,
        parent_id=None,
        name="Törlendő tárhely",
        slug="torlendo-tarhely",
        location_type="slot",
        sort_order=0,
        is_active=True,
    )

    db_session.add(location)
    db_session.flush()

    login(
        test_client,
        user=admin,
    )

    first_response = test_client.put(
        f"/admin/households/"
        f"{household.id}/categories/"
        f"{category.id}/storage-rules",
        json={
            "rules": [
                {
                    "storage_location_public_id":
                        location.public_id,
                    "include_descendants":
                        False,
                }
            ]
        },
    )

    assert first_response.status_code == 200
    assert (
        first_response.json()["restricted"]
        is True
    )

    clear_response = test_client.put(
        f"/admin/households/"
        f"{household.id}/categories/"
        f"{category.id}/storage-rules",
        json={
            "rules": []
        },
    )

    assert clear_response.status_code == 200

    data = clear_response.json()

    assert data["category_id"] == category.id
    assert data["restricted"] is False
    assert data["rules"] == []


def test_admin_category_storage_rules_reject_other_household_location(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_test_household(
        db_session,
        name="Storage rules own household",
        slug="storage-rules-own",
    )

    other_household = create_test_household(
        db_session,
        name="Storage rules other household",
        slug="storage-rules-other",
    )

    category = create_system_category(
        db_session
    )

    admin = create_test_user(
        db_session,
        household=household,
        email="storage-rules-other@example.com",
        username="storage-rules-other",
        role="admin",
    )

    foreign_location = StorageLocation(
        household_id=other_household.id,
        parent_id=None,
        name="Másik household tárhely",
        slug="foreign-storage",
        location_type="slot",
        sort_order=0,
        is_active=True,
    )

    db_session.add(foreign_location)
    db_session.flush()

    login(
        test_client,
        user=admin,
    )

    response = test_client.put(
        f"/admin/households/"
        f"{household.id}/categories/"
        f"{category.id}/storage-rules",
        json={
            "rules": [
                {
                    "storage_location_public_id":
                        foreign_location.public_id,
                    "include_descendants":
                        False,
                }
            ]
        },
    )

    assert response.status_code == 400

    assert response.json() == {
        "detail": (
            "A megadott tárhely nem létezik "
            "ebben a háztartásban."
        )
    }


def test_admin_category_storage_rules_reject_duplicate_location(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_test_household(
        db_session,
        name="Storage rules duplicate household",
        slug="storage-rules-duplicate",
    )

    category = create_system_category(
        db_session
    )

    admin = create_test_user(
        db_session,
        household=household,
        email="storage-rules-duplicate@example.com",
        username="storage-rules-duplicate",
        role="admin",
    )

    location = StorageLocation(
        household_id=household.id,
        parent_id=None,
        name="Duplikált tárhely",
        slug="duplicate-storage",
        location_type="slot",
        sort_order=0,
        is_active=True,
    )

    db_session.add(location)
    db_session.flush()

    login(
        test_client,
        user=admin,
    )

    response = test_client.put(
        f"/admin/households/"
        f"{household.id}/categories/"
        f"{category.id}/storage-rules",
        json={
            "rules": [
                {
                    "storage_location_public_id":
                        location.public_id,
                    "include_descendants":
                        False,
                },
                {
                    "storage_location_public_id":
                        location.public_id,
                    "include_descendants":
                        True,
                },
            ]
        },
    )

    assert response.status_code == 400

    assert response.json() == {
        "detail": (
            "Ugyanaz a tárhely csak egyszer "
            "szerepelhet a szabályok között."
        )
    }
