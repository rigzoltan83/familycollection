from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import (
    Category,
    Household,
    HouseholdMember,
    User,
)


TEST_PASSWORD = "Item-images-auth-123"


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
        name="Kép auth kategória",
        slug="item-image-auth-category",
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


def logout(
    client: TestClient,
) -> None:
    response = client.post(
        "/auth/logout"
    )

    assert response.status_code == 200


def create_item(
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
            "title": "Kép jogosultsági teszt",
        },
    )

    assert response.status_code == 201

    return response.json()


def create_jpeg() -> bytes:
    image = Image.new(
        "RGB",
        (160, 120),
        "white",
    )

    buffer = BytesIO()

    image.save(
        buffer,
        format="JPEG",
    )

    image.close()

    return buffer.getvalue()


def upload_image(
    client: TestClient,
    *,
    item_public_id: str,
) -> dict:
    response = client.post(
        f"/items/{item_public_id}/images",
        files={
            "file": (
                "auth-test.jpg",
                create_jpeg(),
                "image/jpeg",
            ),
        },
        data={
            "caption": "Auth teszt",
            "is_primary": "true",
            "sort_order": "0",
        },
    )

    assert response.status_code == 201

    return response.json()


def prepare_item_with_image(
    test_client: TestClient,
    db_session: Session,
    tmp_path,
    monkeypatch,
    *,
    household_name: str,
    household_slug: str,
    editor_email: str,
) -> tuple[Household, dict, dict]:
    from app.services import image_storage

    monkeypatch.setattr(
        image_storage,
        "ITEM_IMAGE_ROOT",
        tmp_path,
    )

    household = create_household(
        db_session,
        name=household_name,
        slug=household_slug,
    )

    category = create_category(
        db_session
    )

    editor = create_user(
        db_session,
        household=household,
        email=editor_email,
        role="editor",
    )

    login(
        test_client,
        user=editor,
    )

    item = create_item(
        test_client,
        household=household,
        category=category,
    )

    image = upload_image(
        test_client,
        item_public_id=item["public_id"],
    )

    return household, item, image


def test_anonymous_user_cannot_get_image_content(
    test_client: TestClient,
) -> None:
    response = test_client.get(
        "/item-images/"
        "01AAAAAAAAAAAAAAAAAAAAAAAA"
        "/content"
    )

    assert response.status_code == 401

    assert response.json() == {
        "detail": "Nincs bejelentkezve."
    }


def test_viewer_can_get_own_household_image_content(
    test_client: TestClient,
    db_session: Session,
    tmp_path,
    monkeypatch,
) -> None:
    household, _, image = (
        prepare_item_with_image(
            test_client,
            db_session,
            tmp_path,
            monkeypatch,
            household_name="Image viewer household",
            household_slug="image-auth-viewer",
            editor_email=(
                "image-editor-content@example.com"
            ),
        )
    )

    logout(test_client)

    viewer = create_user(
        db_session,
        household=household,
        email="image-viewer-content@example.com",
        username="image-viewer-content",
        role="viewer",
    )

    login(
        test_client,
        user=viewer,
    )

    response = test_client.get(
        image["content_url"]
    )

    assert response.status_code == 200
    assert response.headers[
        "content-type"
    ] == "image/webp"


def test_viewer_can_get_own_household_thumbnail(
    test_client: TestClient,
    db_session: Session,
    tmp_path,
    monkeypatch,
) -> None:
    household, _, image = (
        prepare_item_with_image(
            test_client,
            db_session,
            tmp_path,
            monkeypatch,
            household_name="Thumbnail viewer household",
            household_slug="image-auth-thumbnail",
            editor_email=(
                "image-editor-thumb@example.com"
            ),
        )
    )

    logout(test_client)

    viewer = create_user(
        db_session,
        household=household,
        email="image-viewer-thumb@example.com",
        username="image-viewer-thumb",
        role="viewer",
    )

    login(
        test_client,
        user=viewer,
    )

    response = test_client.get(
        f"/item-images/"
        f"{image['public_id']}"
        f"/thumbnail"
    )

    assert response.status_code == 200
    assert response.headers[
        "content-type"
    ] == "image/webp"


def test_viewer_cannot_update_image(
    test_client: TestClient,
    db_session: Session,
    tmp_path,
    monkeypatch,
) -> None:
    household, _, image = (
        prepare_item_with_image(
            test_client,
            db_session,
            tmp_path,
            monkeypatch,
            household_name="Image update household",
            household_slug="image-auth-update",
            editor_email=(
                "image-editor-update@example.com"
            ),
        )
    )

    logout(test_client)

    viewer = create_user(
        db_session,
        household=household,
        email="image-viewer-update@example.com",
        username="image-viewer-update",
        role="viewer",
    )

    login(
        test_client,
        user=viewer,
    )

    response = test_client.patch(
        f"/item-images/"
        f"{image['public_id']}",
        json={
            "caption": "Tiltott módosítás",
        },
    )

    assert response.status_code == 403

    assert response.json() == {
        "detail": (
            "Nincs megfelelő jogosultsága "
            "ehhez a művelethez."
        )
    }


def test_viewer_cannot_delete_image(
    test_client: TestClient,
    db_session: Session,
    tmp_path,
    monkeypatch,
) -> None:
    household, _, image = (
        prepare_item_with_image(
            test_client,
            db_session,
            tmp_path,
            monkeypatch,
            household_name="Image delete household",
            household_slug="image-auth-delete",
            editor_email=(
                "image-editor-delete@example.com"
            ),
        )
    )

    logout(test_client)

    viewer = create_user(
        db_session,
        household=household,
        email="image-viewer-delete@example.com",
        username="image-viewer-delete",
        role="viewer",
    )

    login(
        test_client,
        user=viewer,
    )

    response = test_client.delete(
        f"/item-images/"
        f"{image['public_id']}"
    )

    assert response.status_code == 403


def test_other_household_cannot_get_image(
    test_client: TestClient,
    db_session: Session,
    tmp_path,
    monkeypatch,
) -> None:
    _, _, image = (
        prepare_item_with_image(
            test_client,
            db_session,
            tmp_path,
            monkeypatch,
            household_name="Image source household",
            household_slug="image-auth-source",
            editor_email=(
                "image-source-editor@example.com"
            ),
        )
    )

    logout(test_client)

    other_household = create_household(
        db_session,
        name="Image other household",
        slug="image-auth-other",
    )

    other_viewer = create_user(
        db_session,
        household=other_household,
        email="image-other-viewer@example.com",
        username="image-other-viewer",
        role="viewer",
    )

    login(
        test_client,
        user=other_viewer,
    )

    response = test_client.get(
        image["content_url"]
    )

    assert response.status_code == 403

    assert response.json() == {
        "detail": (
            "Nincs jogosultsága ehhez "
            "a háztartáshoz."
        )
    }


def test_editor_can_update_image(
    test_client: TestClient,
    db_session: Session,
    tmp_path,
    monkeypatch,
) -> None:
    _, _, image = (
        prepare_item_with_image(
            test_client,
            db_session,
            tmp_path,
            monkeypatch,
            household_name="Image editor household",
            household_slug="image-auth-editor",
            editor_email=(
                "image-editor-edit@example.com"
            ),
        )
    )

    response = test_client.patch(
        f"/item-images/"
        f"{image['public_id']}",
        json={
            "caption": "Sikeres módosítás",
        },
    )

    assert response.status_code == 200

    assert response.json()[
        "caption"
    ] == "Sikeres módosítás"
