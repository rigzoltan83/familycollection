from io import BytesIO

import pytest
from PIL import Image

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from main import app

from PIL import Image

from app.core.security import hash_password
from app.models import (
    Category,
    CategoryField,
    Household,
    HouseholdMember,
    User,
)

def create_test_household(
    session: Session,
) -> Household:
    household = Household(
        name="API teszt háztartás",
        slug="api-test-household",
        is_active=True,
    )

    session.add(household)
    session.flush()

    return household


TEST_PASSWORD = "Items-api-test-123"


def create_test_user(
    session: Session,
) -> User:
    user = User(
        email="items-api@example.com",
        password_hash="test-hash",
        display_name="Items API teszt",
        is_active=True,
        is_platform_admin=False,
        email_verified=True,
    )

    session.add(user)
    session.flush()

    return user

@pytest.fixture(autouse=True)
def bypass_items_authorization(
    test_client: TestClient,
    monkeypatch,
):
    """
    Az items API funkcionális tesztjeiben
    az autentikációt és jogosultságot nem
    teszteljük újra.

    A valódi jogosultsági viselkedést külön
    authorization tesztek ellenőrzik.
    """
    test_user = User(
        id=999999,
        email="items-auth-bypass@example.com",
        password_hash="unused",
        display_name="Items auth bypass",
        is_active=True,
        is_platform_admin=False,
        email_verified=True,
    )

    app.dependency_overrides[
        get_current_user
    ] = lambda: test_user

    monkeypatch.setattr(
        "app.api.routers.items."
        "require_household_viewer_by_id",
        lambda **kwargs: None,
    )

    monkeypatch.setattr(
        "app.api.routers.items."
        "require_household_editor_by_id",
        lambda **kwargs: None,
    )

    try:
        yield
    finally:
        app.dependency_overrides.pop(
            get_current_user,
            None,
        )


def create_test_book_category(
    session: Session,
) -> Category:
    category = Category(
        household_id=None,
        name="Könyv API teszt",
        slug="book-api-test",
        description="API tesztkategória",
        icon="book",
        is_system=True,
        is_active=True,
        supports_barcode=True,
        metadata_lookup_type="manual",
        sort_order=10,
    )

    session.add(category)
    session.flush()

    session.add_all(
        [
            CategoryField(
                category_id=category.id,
                name="Szerző",
                field_key="author",
                field_type="text",
                is_required=False,
                is_searchable=True,
                is_filterable=False,
                is_visible_in_list=True,
                is_active=True,
                sort_order=10,
                validation_rules={},
                default_value={},
            ),
            CategoryField(
                category_id=category.id,
                name="Megjelenési év",
                field_key="publish_year",
                field_type="year",
                is_required=False,
                is_searchable=False,
                is_filterable=True,
                is_visible_in_list=True,
                is_active=True,
                sort_order=20,
                validation_rules={
                    "minimum": 1000,
                    "maximum": 9999,
                },
                default_value={},
            ),
        ]
    )

    session.flush()

    return category


def test_create_collection_item_api(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    user = create_test_user(db_session)
    category = create_test_book_category(db_session)

    response = test_client.post(
        "/items",
        json={
            "household_id": household.id,
            "category_id": category.id,
            "title": "Az",
            "created_by_user_id": user.id,
            "identifiers": [
                {
                    "identifier_type": "isbn13",
                    "identifier_value": "9789631234567",
                    "is_primary": True,
                }
            ],
            "field_values": {
                "author": "Stephen King",
                "publish_year": 1986,
            },
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert len(data["public_id"]) == 26
    assert data["title"] == "Az"
    assert data["household_id"] == household.id
    assert data["category_id"] == category.id
    assert data["status"] == "active"
    assert data["created_by_user_id"] == user.id
    assert data["updated_by_user_id"] == user.id

    assert len(data["identifiers"]) == 1

    identifier = data["identifiers"][0]

    assert identifier["identifier_type"] == "isbn13"
    assert identifier["identifier_value"] == "9789631234567"
    assert identifier["is_primary"] is True

    values_by_key = {
        field_value["field_key"]: field_value
        for field_value in data["field_values"]
    }

    assert values_by_key["author"]["value_text"] == "Stephen King"
    assert values_by_key["publish_year"]["value_integer"] == 1986


def test_create_collection_item_api_rejects_invalid_year(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_test_book_category(db_session)

    response = test_client.post(
        "/items",
        json={
            "household_id": household.id,
            "category_id": category.id,
            "title": "Hibás évű könyv",
            "field_values": {
                "publish_year": 999,
            },
        },
    )

    assert response.status_code == 400
    assert "nem lehet kisebb mint 1000" in response.json()["detail"]

def test_get_collection_item_by_public_id(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    user = create_test_user(db_session)
    category = create_test_book_category(db_session)

    create_response = test_client.post(
        "/items",
        json={
            "household_id": household.id,
            "category_id": category.id,
            "title": "Ragyogás",
            "created_by_user_id": user.id,
            "identifiers": [
                {
                    "identifier_type": "isbn13",
                    "identifier_value": "9789631234000",
                    "is_primary": True,
                }
            ],
            "field_values": {
                "author": "Stephen King",
                "publish_year": 1977,
            },
        },
    )

    assert create_response.status_code == 201

    public_id = create_response.json()["public_id"]

    response = test_client.get(
        f"/items/{public_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["public_id"] == public_id
    assert data["title"] == "Ragyogás"
    assert len(data["identifiers"]) == 1

    values_by_key = {
        field_value["field_key"]: field_value
        for field_value in data["field_values"]
    }

    assert values_by_key["author"]["value_text"] == "Stephen King"
    assert values_by_key["publish_year"]["value_integer"] == 1977


def test_get_collection_item_returns_404_for_unknown_public_id(
    test_client: TestClient,
) -> None:
    response = test_client.get(
        "/items/01AAAAAAAAAAAAAAAAAAAAAAAA"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "A gyűjteményi elem nem található."
    }

def test_list_collection_items(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_test_book_category(db_session)

    for title in [
        "B könyv",
        "A könyv",
        "C könyv",
    ]:
        response = test_client.post(
            "/items",
            json={
                "household_id": household.id,
                "category_id": category.id,
                "title": title,
            },
        )

        assert response.status_code == 201

    response = test_client.get(
        "/items",
        params={
            "household_id": household.id,
            "limit": 2,
            "offset": 0,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 3
    assert data["limit"] == 2
    assert data["offset"] == 0
    assert len(data["items"]) == 2

    assert [
        item["title"]
        for item in data["items"]
    ] == [
        "A könyv",
        "B könyv",
    ]


def test_list_collection_items_filters_by_category(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    first_category = create_test_book_category(db_session)

    second_category = Category(
        household_id=None,
        name="Második kategória",
        slug="second-list-category",
        is_system=True,
        is_active=True,
        supports_barcode=False,
        metadata_lookup_type="manual",
        sort_order=20,
    )

    db_session.add(second_category)
    db_session.flush()

    first_response = test_client.post(
        "/items",
        json={
            "household_id": household.id,
            "category_id": first_category.id,
            "title": "Első kategóriás",
        },
    )

    second_response = test_client.post(
        "/items",
        json={
            "household_id": household.id,
            "category_id": second_category.id,
            "title": "Második kategóriás",
        },
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    response = test_client.get(
        "/items",
        params={
            "household_id": household.id,
            "category_id": second_category.id,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["title"] == "Második kategóriás"


def test_list_collection_items_rejects_invalid_limit(
    test_client: TestClient,
) -> None:
    response = test_client.get(
        "/items",
        params={
            "household_id": 1,
            "limit": 201,
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "A limit értéke 1 és 200 közötti lehet."
    }

def test_list_collection_items_searches_title_case_insensitively(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_test_book_category(db_session)

    for title in [
        "A Ragyogás",
        "Az",
        "Tűzgyújtó",
    ]:
        response = test_client.post(
            "/items",
            json={
                "household_id": household.id,
                "category_id": category.id,
                "title": title,
            },
        )

        assert response.status_code == 201

    response = test_client.get(
        "/items",
        params={
            "household_id": household.id,
            "query": "ragy",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["title"] == "A Ragyogás"


def test_list_collection_items_searches_subtitle(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_test_book_category(db_session)

    first_response = test_client.post(
        "/items",
        json={
            "household_id": household.id,
            "category_id": category.id,
            "title": "Tesztkönyv",
            "subtitle": "Különleges alcím",
        },
    )

    second_response = test_client.post(
        "/items",
        json={
            "household_id": household.id,
            "category_id": category.id,
            "title": "Másik könyv",
        },
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    response = test_client.get(
        "/items",
        params={
            "household_id": household.id,
            "query": "különleges",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["title"] == "Tesztkönyv"


def test_list_collection_items_ignores_blank_query(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_test_book_category(db_session)

    response = test_client.post(
        "/items",
        json={
            "household_id": household.id,
            "category_id": category.id,
            "title": "Teszt könyv",
        },
    )

    assert response.status_code == 201

    response = test_client.get(
        "/items",
        params={
            "household_id": household.id,
            "query": "   ",
        },
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1

def test_list_collection_items_searches_identifier(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_test_book_category(db_session)

    first_response = test_client.post(
        "/items",
        json={
            "household_id": household.id,
            "category_id": category.id,
            "title": "Első könyv",
            "identifiers": [
                {
                    "identifier_type": "isbn13",
                    "identifier_value": "9789631111111",
                    "is_primary": True,
                }
            ],
        },
    )

    second_response = test_client.post(
        "/items",
        json={
            "household_id": household.id,
            "category_id": category.id,
            "title": "Második könyv",
            "identifiers": [
                {
                    "identifier_type": "isbn13",
                    "identifier_value": "9789632222222",
                    "is_primary": True,
                }
            ],
        },
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    response = test_client.get(
        "/items",
        params={
            "household_id": household.id,
            "identifier": "9789632222222",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["title"] == "Második könyv"


def test_list_collection_items_ignores_blank_identifier(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_test_book_category(db_session)

    response = test_client.post(
        "/items",
        json={
            "household_id": household.id,
            "category_id": category.id,
            "title": "Teszt könyv",
        },
    )

    assert response.status_code == 201

    response = test_client.get(
        "/items",
        params={
            "household_id": household.id,
            "identifier": "   ",
        },
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1

def test_list_collection_items_searches_searchable_dynamic_field(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_test_book_category(db_session)

    first_response = test_client.post(
        "/items",
        json={
            "household_id": household.id,
            "category_id": category.id,
            "title": "Első könyv",
            "field_values": {
                "author": "Stephen King",
                "publish_year": 1986,
            },
        },
    )

    second_response = test_client.post(
        "/items",
        json={
            "household_id": household.id,
            "category_id": category.id,
            "title": "Második könyv",
            "field_values": {
                "author": "Neil Gaiman",
                "publish_year": 2001,
            },
        },
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    response = test_client.get(
        "/items",
        params={
            "household_id": household.id,
            "query": "gaiman",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["title"] == "Második könyv"


def test_list_collection_items_does_not_search_non_searchable_field(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_test_book_category(db_session)

    response = test_client.post(
        "/items",
        json={
            "household_id": household.id,
            "category_id": category.id,
            "title": "Tesztkönyv",
            "field_values": {
                "author": "Ismeretlen szerző",
                "publish_year": 1986,
            },
        },
    )

    assert response.status_code == 201

    response = test_client.get(
        "/items",
        params={
            "household_id": household.id,
            "query": "1986",
        },
    )

    assert response.status_code == 200
    assert response.json()["total"] == 0

def test_list_collection_items_sorts_title_descending(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_test_book_category(db_session)

    for title in [
        "A könyv",
        "C könyv",
        "B könyv",
    ]:
        response = test_client.post(
            "/items",
            json={
                "household_id": household.id,
                "category_id": category.id,
                "title": title,
            },
        )

        assert response.status_code == 201

    response = test_client.get(
        "/items",
        params={
            "household_id": household.id,
            "sort_by": "title",
            "sort_direction": "desc",
        },
    )

    assert response.status_code == 200

    assert [
        item["title"]
        for item in response.json()["items"]
    ] == [
        "C könyv",
        "B könyv",
        "A könyv",
    ]


def test_list_collection_items_rejects_invalid_sort_field(
    test_client: TestClient,
) -> None:
    response = test_client.get(
        "/items",
        params={
            "household_id": 1,
            "sort_by": "invalid",
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": (
            "A sort_by értéke csak title, created_at "
            "vagy updated_at lehet."
        )
    }


def test_list_collection_items_rejects_invalid_sort_direction(
    test_client: TestClient,
) -> None:
    response = test_client.get(
        "/items",
        params={
            "household_id": 1,
            "sort_direction": "sideways",
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": (
            "A sort_direction értéke csak asc vagy desc lehet."
        )
    }

def test_list_collection_items_filters_by_status(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_test_book_category(db_session)

    first = test_client.post(
        "/items",
        json={
            "household_id": household.id,
            "category_id": category.id,
            "title": "Aktív könyv",
        },
    )

    second = test_client.post(
        "/items",
        json={
            "household_id": household.id,
            "category_id": category.id,
            "title": "Kölcsönadott könyv",
        },
    )

    assert first.status_code == 201
    assert second.status_code == 201

    second_public_id = second.json()["public_id"]

    from app.models import CollectionItem

    item = db_session.query(CollectionItem).filter_by(
        public_id=second_public_id
    ).one()

    item.status = "loaned"
    db_session.commit()

    response = test_client.get(
        "/items",
        params={
            "household_id": household.id,
            "item_status": "loaned",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["title"] == "Kölcsönadott könyv"


def test_list_collection_items_rejects_invalid_status(
    test_client: TestClient,
) -> None:
    response = test_client.get(
        "/items",
        params={
            "household_id": 1,
            "item_status": "foobar",
        },
    )

    assert response.status_code == 400

    assert response.json() == {
        "detail": (
            "A status értéke csak active, loaned, archived, "
            "missing vagy disposed lehet."
        )
    }

def test_update_collection_item_api(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    user = create_test_user(db_session)
    category = create_test_book_category(db_session)

    create_response = test_client.post(
        "/items",
        json={
            "household_id": household.id,
            "category_id": category.id,
            "title": "Régi cím",
            "subtitle": "Régi alcím",
            "notes": "Régi megjegyzés",
            "created_by_user_id": user.id,
            "identifiers": [
                {
                    "identifier_type": "isbn13",
                    "identifier_value": "9789631111111",
                    "is_primary": True,
                }
            ],
            "field_values": {
                "author": "Régi szerző",
                "publish_year": 1980,
            },
        },
    )

    assert create_response.status_code == 201

    public_id = create_response.json()["public_id"]

    response = test_client.patch(
        f"/items/{public_id}",
        json={
            "title": "Új cím",
            "subtitle": "Új alcím",
            "notes": "Új megjegyzés",
            "status": "archived",
            "updated_by_user_id": user.id,
            "identifiers": [
                {
                    "identifier_type": "isbn10",
                    "identifier_value": "9632222222",
                    "is_primary": True,
                }
            ],
            "field_values": {
                "author": "Új szerző",
                "publish_year": 2020,
            },
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["public_id"] == public_id
    assert data["title"] == "Új cím"
    assert data["subtitle"] == "Új alcím"
    assert data["notes"] == "Új megjegyzés"
    assert data["status"] == "archived"
    assert data["updated_by_user_id"] == user.id

    assert len(data["identifiers"]) == 1
    assert data["identifiers"][0]["identifier_type"] == "isbn10"
    assert data["identifiers"][0]["identifier_value"] == "9632222222"

    values_by_key = {
        field_value["field_key"]: field_value
        for field_value in data["field_values"]
    }

    assert values_by_key["author"]["value_text"] == "Új szerző"
    assert values_by_key["publish_year"]["value_integer"] == 2020


def test_update_collection_item_api_keeps_unspecified_fields(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_test_book_category(db_session)

    create_response = test_client.post(
        "/items",
        json={
            "household_id": household.id,
            "category_id": category.id,
            "title": "Eredeti cím",
            "subtitle": "Eredeti alcím",
            "notes": "Eredeti megjegyzés",
        },
    )

    assert create_response.status_code == 201

    public_id = create_response.json()["public_id"]

    response = test_client.patch(
        f"/items/{public_id}",
        json={
            "title": "Módosított cím",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["title"] == "Módosított cím"
    assert data["subtitle"] == "Eredeti alcím"
    assert data["notes"] == "Eredeti megjegyzés"
    assert data["status"] == "active"


def test_update_collection_item_api_can_clear_nullable_fields(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_test_book_category(db_session)

    create_response = test_client.post(
        "/items",
        json={
            "household_id": household.id,
            "category_id": category.id,
            "title": "Teszt könyv",
            "subtitle": "Törlendő alcím",
            "notes": "Törlendő megjegyzés",
        },
    )

    assert create_response.status_code == 201

    public_id = create_response.json()["public_id"]

    response = test_client.patch(
        f"/items/{public_id}",
        json={
            "subtitle": None,
            "notes": None,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["subtitle"] is None
    assert data["notes"] is None


def test_update_collection_item_api_can_clear_identifiers_and_fields(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_test_book_category(db_session)

    create_response = test_client.post(
        "/items",
        json={
            "household_id": household.id,
            "category_id": category.id,
            "title": "Teszt könyv",
            "identifiers": [
                {
                    "identifier_type": "isbn13",
                    "identifier_value": "9789633333333",
                    "is_primary": True,
                }
            ],
            "field_values": {
                "author": "Teszt szerző",
                "publish_year": 2000,
            },
        },
    )

    assert create_response.status_code == 201

    public_id = create_response.json()["public_id"]

    response = test_client.patch(
        f"/items/{public_id}",
        json={
            "identifiers": [],
            "field_values": {},
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["identifiers"] == []
    assert data["field_values"] == []


def test_update_collection_item_api_returns_404(
    test_client: TestClient,
) -> None:
    response = test_client.patch(
        "/items/01AAAAAAAAAAAAAAAAAAAAAAAA",
        json={
            "title": "Új cím",
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "A gyűjteményi elem nem található."
    }


def test_update_collection_item_api_rejects_invalid_field(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_test_book_category(db_session)

    create_response = test_client.post(
        "/items",
        json={
            "household_id": household.id,
            "category_id": category.id,
            "title": "Teszt könyv",
        },
    )

    assert create_response.status_code == 201

    public_id = create_response.json()["public_id"]

    response = test_client.patch(
        f"/items/{public_id}",
        json={
            "field_values": {
                "unknown_field": "érték",
            },
        },
    )

    assert response.status_code == 400
    assert "Ismeretlen kategóriamezők" in response.json()["detail"]

def test_delete_collection_item_soft_deletes_item(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_test_book_category(db_session)

    create_response = test_client.post(
        "/items",
        json={
            "household_id": household.id,
            "category_id": category.id,
            "title": "Törlendő könyv",
        },
    )

    assert create_response.status_code == 201

    public_id = create_response.json()["public_id"]

    response = test_client.delete(
        f"/items/{public_id}"
    )

    assert response.status_code == 204
    assert response.content == b""

    detail_response = test_client.get(
        f"/items/{public_id}"
    )

    assert detail_response.status_code == 404

    list_response = test_client.get(
        "/items",
        params={
            "household_id": household.id,
        },
    )

    assert list_response.status_code == 200
    assert list_response.json()["total"] == 0

    from app.models import CollectionItem

    item = db_session.query(CollectionItem).filter_by(
        public_id=public_id
    ).one()

    assert item.is_active is False


def test_delete_collection_item_returns_404_for_unknown_item(
    test_client: TestClient,
) -> None:
    response = test_client.delete(
        "/items/01AAAAAAAAAAAAAAAAAAAAAAAA"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "A gyűjteményi elem nem található."
    }


def test_delete_collection_item_returns_404_when_already_deleted(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_test_book_category(db_session)

    create_response = test_client.post(
        "/items",
        json={
            "household_id": household.id,
            "category_id": category.id,
            "title": "Egyszer törölhető könyv",
        },
    )

    assert create_response.status_code == 201

    public_id = create_response.json()["public_id"]

    first_response = test_client.delete(
        f"/items/{public_id}"
    )

    second_response = test_client.delete(
        f"/items/{public_id}"
    )

    assert first_response.status_code == 204
    assert second_response.status_code == 404

def test_restore_collection_item(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_test_book_category(db_session)

    create_response = test_client.post(
        "/items",
        json={
            "household_id": household.id,
            "category_id": category.id,
            "title": "Visszaállítandó könyv",
        },
    )

    assert create_response.status_code == 201

    public_id = create_response.json()["public_id"]

    delete_response = test_client.delete(
        f"/items/{public_id}"
    )

    assert delete_response.status_code == 204

    restore_response = test_client.post(
        f"/items/{public_id}/restore"
    )

    assert restore_response.status_code == 200

    data = restore_response.json()

    assert data["public_id"] == public_id
    assert data["title"] == "Visszaállítandó könyv"
    assert data["is_active"] is True

    detail_response = test_client.get(
        f"/items/{public_id}"
    )

    assert detail_response.status_code == 200

    list_response = test_client.get(
        "/items",
        params={
            "household_id": household.id,
        },
    )

    assert list_response.status_code == 200
    assert list_response.json()["total"] == 1


def test_restore_collection_item_returns_404_for_active_item(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_test_book_category(db_session)

    create_response = test_client.post(
        "/items",
        json={
            "household_id": household.id,
            "category_id": category.id,
            "title": "Aktív könyv",
        },
    )

    assert create_response.status_code == 201

    public_id = create_response.json()["public_id"]

    response = test_client.post(
        f"/items/{public_id}/restore"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "A törölt gyűjteményi elem nem található."
    }


def test_restore_collection_item_returns_404_for_unknown_item(
    test_client: TestClient,
) -> None:
    response = test_client.post(
        "/items/01AAAAAAAAAAAAAAAAAAAAAAAA/restore"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "A törölt gyűjteményi elem nem található."
    }


def test_upload_item_image_api(
    test_client: TestClient,
    db_session: Session,
    tmp_path,
    monkeypatch,
) -> None:
    from app.services import image_storage

    monkeypatch.setattr(
        image_storage,
        "ITEM_IMAGE_ROOT",
        tmp_path,
    )

    household = create_test_household(db_session)
    category = create_test_book_category(db_session)

    create_response = test_client.post(
        "/items",
        json={
            "household_id": household.id,
            "category_id": category.id,
            "title": "Képes könyv",
        },
    )

    assert create_response.status_code == 201

    public_id = create_response.json()["public_id"]

    image = Image.new(
        "RGB",
        (320, 240),
        "white",
    )

    buffer = BytesIO()

    image.save(
        buffer,
        format="JPEG",
    )

    image.close()

    jpeg = buffer.getvalue()

    response = test_client.post(
        f"/items/{public_id}/images",
        files={
            "file": (
                "borito.jpg",
                jpeg,
                "image/jpeg",
            ),
        },
        data={
            "caption": "Borító",
            "is_primary": "true",
            "sort_order": "0",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["caption"] == "Borító"
    assert data["is_primary"] is True
    assert data["sort_order"] == 0
    assert data["mime_type"] == "image/webp"
    assert data["content_url"].startswith(
        "/item-images/"
    )

    stored_files = list(
        tmp_path.rglob("*.webp")
    )

    assert len(stored_files) == 2

    original_files = [
        path
        for path in stored_files
        if not path.name.endswith(
            ".thumb.webp"
        )
    ]

    thumbnail_files = [
        path
        for path in stored_files
        if path.name.endswith(
            ".thumb.webp"
        )
    ]

    assert len(original_files) == 1
    assert len(thumbnail_files) == 1

    with Image.open(
        original_files[0]
    ) as stored_image:
        assert stored_image.format == "WEBP"
        assert stored_image.size == (320, 240)

    with Image.open(
        thumbnail_files[0]
    ) as thumbnail_image:
        assert thumbnail_image.format == "WEBP"
        assert thumbnail_image.size == (320, 240)

def test_upload_item_image_rejects_invalid_file(
    test_client: TestClient,
    db_session: Session,
    tmp_path,
    monkeypatch,
) -> None:
    from app.services import image_storage

    monkeypatch.setattr(
        image_storage,
        "ITEM_IMAGE_ROOT",
        tmp_path,
    )

    household = create_test_household(db_session)
    category = create_test_book_category(db_session)

    create_response = test_client.post(
        "/items",
        json={
            "household_id": household.id,
            "category_id": category.id,
            "title": "Hibás képes könyv",
        },
    )

    public_id = create_response.json()["public_id"]

    response = test_client.post(
        f"/items/{public_id}/images",
        files={
            "file": (
                "nem-kep.jpg",
                b"this is not an image",
                "image/jpeg",
            ),
        },
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "A feltöltött fájl nem érvényes kép."
    )

    assert list(
        tmp_path.rglob("*")
    ) == []


def test_upload_item_image_returns_404_for_unknown_item(
    test_client: TestClient,
    tmp_path,
    monkeypatch,
) -> None:
    from app.services import image_storage

    monkeypatch.setattr(
        image_storage,
        "ITEM_IMAGE_ROOT",
        tmp_path,
    )

    response = test_client.post(
        (
            "/items/"
            "01AAAAAAAAAAAAAAAAAAAAAAAA"
            "/images"
        ),
        files={
            "file": (
                "borito.jpg",
                b"irrelevant",
                "image/jpeg",
            ),
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "A gyűjteményi elem nem található."
    }

    assert list(
        tmp_path.rglob("*")
    ) == []


def test_upload_item_image_rejects_negative_sort_order(
    test_client: TestClient,
    db_session: Session,
    tmp_path,
    monkeypatch,
) -> None:
    from app.services import image_storage

    monkeypatch.setattr(
        image_storage,
        "ITEM_IMAGE_ROOT",
        tmp_path,
    )

    household = create_test_household(db_session)
    category = create_test_book_category(db_session)

    create_response = test_client.post(
        "/items",
        json={
            "household_id": household.id,
            "category_id": category.id,
            "title": "Rendezési teszt",
        },
    )

    public_id = create_response.json()["public_id"]

    response = test_client.post(
        f"/items/{public_id}/images",
        files={
            "file": (
                "borito.jpg",
                b"irrelevant",
                "image/jpeg",
            ),
        },
        data={
            "sort_order": "-1",
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": (
            "A kép rendezési sorrendje "
            "nem lehet negatív."
        )
    }

    assert list(
        tmp_path.rglob("*")
    ) == []


def test_get_item_image_content_api(
    test_client: TestClient,
    db_session: Session,
    tmp_path,
    monkeypatch,
) -> None:
    from io import BytesIO

    from PIL import Image

    from app.services import image_storage

    monkeypatch.setattr(
        image_storage,
        "ITEM_IMAGE_ROOT",
        tmp_path,
    )

    household = create_test_household(
        db_session
    )

    category = create_test_book_category(
        db_session
    )

    create_response = test_client.post(
        "/items",
        json={
            "household_id": household.id,
            "category_id": category.id,
            "title": "Kép lekérési teszt",
        },
    )

    assert create_response.status_code == 201

    item_public_id = (
        create_response.json()["public_id"]
    )

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

    upload_response = test_client.post(
        f"/items/{item_public_id}/images",
        files={
            "file": (
                "borito.jpg",
                buffer.getvalue(),
                "image/jpeg",
            ),
        },
    )

    assert upload_response.status_code == 201

    image_public_id = (
        upload_response.json()["public_id"]
    )

    response = test_client.get(
        (
            f"/item-images/"
            f"{image_public_id}/content"
        )
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == (
        "image/webp"
    )

    assert response.headers["cache-control"] == (
        "public, max-age=86400"
    )

    assert len(response.content) > 0

    with Image.open(
        BytesIO(response.content)
    ) as returned_image:
        assert returned_image.format == "WEBP"
        assert returned_image.size == (160, 120)


def test_get_item_image_thumbnail_api(
    test_client: TestClient,
    db_session: Session,
    tmp_path,
    monkeypatch,
) -> None:
    from io import BytesIO

    from PIL import Image

    from app.services import image_storage

    monkeypatch.setattr(
        image_storage,
        "ITEM_IMAGE_ROOT",
        tmp_path,
    )

    household = create_test_household(
        db_session
    )

    category = create_test_book_category(
        db_session
    )

    create_response = test_client.post(
        "/items",
        json={
            "household_id": household.id,
            "category_id": category.id,
            "title": "Thumbnail API teszt",
        },
    )

    assert create_response.status_code == 201

    item_public_id = (
        create_response.json()["public_id"]
    )

    image = Image.new(
        "RGB",
        (1200, 800),
        "white",
    )

    buffer = BytesIO()

    image.save(
        buffer,
        format="JPEG",
    )

    image.close()

    upload_response = test_client.post(
        f"/items/{item_public_id}/images",
        files={
            "file": (
                "large-cover.jpg",
                buffer.getvalue(),
                "image/jpeg",
            ),
        },
    )

    assert upload_response.status_code == 201

    image_public_id = (
        upload_response.json()["public_id"]
    )

    response = test_client.get(
        (
            f"/item-images/"
            f"{image_public_id}"
            f"/thumbnail"
        )
    )

    assert response.status_code == 200
    assert response.headers[
        "content-type"
    ].startswith("image/webp")

    with Image.open(
        BytesIO(response.content)
    ) as thumbnail:
        assert thumbnail.format == "WEBP"
        assert thumbnail.size == (
            400,
            267,
        )


def test_get_item_image_content_returns_404_for_unknown_image(
    test_client: TestClient,
) -> None:
    response = test_client.get(
        (
            "/item-images/"
            "01AAAAAAAAAAAAAAAAAAAAAAAA"
            "/content"
        )
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "A kép nem található."
    }


def test_get_item_image_content_returns_404_for_missing_file(
    test_client: TestClient,
    db_session: Session,
) -> None:
    from app.models import ItemImage
    from app.services import (
        CollectionItemCreateInput,
        ItemImageCreateInput,
        create_collection_item,
        create_item_image,
    )

    household = create_test_household(
        db_session
    )

    category = create_test_book_category(
        db_session
    )

    item = create_collection_item(
        session=db_session,
        data=CollectionItemCreateInput(
            household_id=household.id,
            category_id=category.id,
            title="Hiányzó képfájl teszt",
        ),
    )

    image = create_item_image(
        session=db_session,
        item=item,
        data=ItemImageCreateInput(
            stored_filename=(
                "2099/01/not-existing.webp"
            ),
            mime_type="image/webp",
            file_size=123,
            width=100,
            height=100,
        ),
    )

    db_session.commit()

    assert db_session.get(
        ItemImage,
        image.id,
    ) is not None

    response = test_client.get(
        (
            f"/item-images/"
            f"{image.public_id}/content"
        )
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "A képfájl nem található."
    }


def test_list_item_images_api(
    test_client: TestClient,
    db_session: Session,
    tmp_path,
    monkeypatch,
) -> None:
    from io import BytesIO

    from PIL import Image

    from app.services import image_storage

    monkeypatch.setattr(
        image_storage,
        "ITEM_IMAGE_ROOT",
        tmp_path,
    )

    household = create_test_household(
        db_session
    )

    category = create_test_book_category(
        db_session
    )

    create_response = test_client.post(
        "/items",
        json={
            "household_id": household.id,
            "category_id": category.id,
            "title": "Képlista teszt",
        },
    )

    assert create_response.status_code == 201

    item_public_id = (
        create_response.json()["public_id"]
    )

    def make_jpeg(
        size: tuple[int, int],
    ) -> bytes:
        image = Image.new(
            "RGB",
            size,
            "white",
        )

        buffer = BytesIO()

        image.save(
            buffer,
            format="JPEG",
        )

        image.close()

        return buffer.getvalue()

    first_response = test_client.post(
        f"/items/{item_public_id}/images",
        files={
            "file": (
                "first.jpg",
                make_jpeg((100, 80)),
                "image/jpeg",
            ),
        },
        data={
            "caption": "Első kép",
            "sort_order": "20",
        },
    )

    second_response = test_client.post(
        f"/items/{item_public_id}/images",
        files={
            "file": (
                "second.jpg",
                make_jpeg((200, 160)),
                "image/jpeg",
            ),
        },
        data={
            "caption": "Második kép",
            "sort_order": "10",
            "is_primary": "true",
        },
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    response = test_client.get(
        f"/items/{item_public_id}/images"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2

    assert data[0]["caption"] == "Második kép"
    assert data[0]["is_primary"] is True
    assert data[0]["width"] == 200
    assert data[0]["height"] == 160

    assert data[1]["caption"] == "Első kép"
    assert data[1]["is_primary"] is False

    assert data[0]["content_url"].startswith(
        "/item-images/"
    )


def test_list_item_images_returns_empty_list(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_test_household(
        db_session
    )

    category = create_test_book_category(
        db_session
    )

    create_response = test_client.post(
        "/items",
        json={
            "household_id": household.id,
            "category_id": category.id,
            "title": "Kép nélküli tárgy",
        },
    )

    item_public_id = (
        create_response.json()["public_id"]
    )

    response = test_client.get(
        f"/items/{item_public_id}/images"
    )

    assert response.status_code == 200
    assert response.json() == []


def test_list_item_images_returns_404_for_unknown_item(
    test_client: TestClient,
) -> None:
    response = test_client.get(
        (
            "/items/"
            "01AAAAAAAAAAAAAAAAAAAAAAAA"
            "/images"
        )
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "A gyűjteményi elem nem található."
    }


def test_update_item_image_api(
    test_client: TestClient,
    db_session: Session,
    tmp_path,
    monkeypatch,
) -> None:
    from io import BytesIO

    from PIL import Image

    from app.services import image_storage

    monkeypatch.setattr(
        image_storage,
        "ITEM_IMAGE_ROOT",
        tmp_path,
    )

    household = create_test_household(
        db_session
    )

    category = create_test_book_category(
        db_session
    )

    create_response = test_client.post(
        "/items",
        json={
            "household_id": household.id,
            "category_id": category.id,
            "title": "Képmódosítás teszt",
        },
    )

    assert create_response.status_code == 201

    item_public_id = (
        create_response.json()["public_id"]
    )

    image = Image.new(
        "RGB",
        (240, 180),
        "white",
    )

    buffer = BytesIO()

    image.save(
        buffer,
        format="JPEG",
    )

    image.close()

    upload_response = test_client.post(
        f"/items/{item_public_id}/images",
        files={
            "file": (
                "borito.jpg",
                buffer.getvalue(),
                "image/jpeg",
            ),
        },
        data={
            "caption": "Régi képaláírás",
            "sort_order": "20",
        },
    )

    assert upload_response.status_code == 201

    image_public_id = (
        upload_response.json()["public_id"]
    )

    response = test_client.patch(
        f"/item-images/{image_public_id}",
        json={
            "caption": "Új képaláírás",
            "sort_order": 10,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["public_id"] == image_public_id
    assert data["caption"] == "Új képaláírás"
    assert data["sort_order"] == 10
    assert data["is_primary"] is True
    assert data["mime_type"] == "image/webp"


def test_update_item_image_sets_new_primary(
    test_client: TestClient,
    db_session: Session,
    tmp_path,
    monkeypatch,
) -> None:
    from io import BytesIO

    from PIL import Image

    from app.services import image_storage

    monkeypatch.setattr(
        image_storage,
        "ITEM_IMAGE_ROOT",
        tmp_path,
    )

    household = create_test_household(
        db_session
    )

    category = create_test_book_category(
        db_session
    )

    create_response = test_client.post(
        "/items",
        json={
            "household_id": household.id,
            "category_id": category.id,
            "title": "Elsődleges kép teszt",
        },
    )

    item_public_id = (
        create_response.json()["public_id"]
    )

    def make_jpeg() -> bytes:
        image = Image.new(
            "RGB",
            (120, 90),
            "white",
        )

        buffer = BytesIO()

        image.save(
            buffer,
            format="JPEG",
        )

        image.close()

        return buffer.getvalue()

    first_response = test_client.post(
        f"/items/{item_public_id}/images",
        files={
            "file": (
                "first.jpg",
                make_jpeg(),
                "image/jpeg",
            ),
        },
    )

    second_response = test_client.post(
        f"/items/{item_public_id}/images",
        files={
            "file": (
                "second.jpg",
                make_jpeg(),
                "image/jpeg",
            ),
        },
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    first_public_id = (
        first_response.json()["public_id"]
    )

    second_public_id = (
        second_response.json()["public_id"]
    )

    response = test_client.patch(
        f"/item-images/{second_public_id}",
        json={
            "is_primary": True,
        },
    )

    assert response.status_code == 200
    assert response.json()["is_primary"] is True

    images_response = test_client.get(
        f"/items/{item_public_id}/images"
    )

    assert images_response.status_code == 200

    images = images_response.json()

    assert images[0]["public_id"] == second_public_id
    assert images[0]["is_primary"] is True

    first = next(
        image
        for image in images
        if image["public_id"] == first_public_id
    )

    assert first["is_primary"] is False


def test_update_item_image_rejects_disabling_primary(
    test_client: TestClient,
    db_session: Session,
    tmp_path,
    monkeypatch,
) -> None:
    from io import BytesIO

    from PIL import Image

    from app.services import image_storage

    monkeypatch.setattr(
        image_storage,
        "ITEM_IMAGE_ROOT",
        tmp_path,
    )

    household = create_test_household(
        db_session
    )

    category = create_test_book_category(
        db_session
    )

    create_response = test_client.post(
        "/items",
        json={
            "household_id": household.id,
            "category_id": category.id,
            "title": "Elsődleges kikapcsolás teszt",
        },
    )

    item_public_id = (
        create_response.json()["public_id"]
    )

    image = Image.new(
        "RGB",
        (100, 100),
        "white",
    )

    buffer = BytesIO()

    image.save(
        buffer,
        format="JPEG",
    )

    image.close()

    upload_response = test_client.post(
        f"/items/{item_public_id}/images",
        files={
            "file": (
                "primary.jpg",
                buffer.getvalue(),
                "image/jpeg",
            ),
        },
    )

    image_public_id = (
        upload_response.json()["public_id"]
    )

    response = test_client.patch(
        f"/item-images/{image_public_id}",
        json={
            "is_primary": False,
        },
    )

    assert response.status_code == 400

    assert response.json() == {
        "detail": (
            "Az elsődleges kép státusza "
            "nem kapcsolható ki közvetlenül. "
            "Jelölj ki helyette másik "
            "elsődleges képet."
        )
    }


def test_update_item_image_returns_404_for_unknown_image(
    test_client: TestClient,
) -> None:
    response = test_client.patch(
        (
            "/item-images/"
            "01AAAAAAAAAAAAAAAAAAAAAAAA"
        ),
        json={
            "caption": "Nem létező kép",
        },
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "A kép nem található."
    }


def test_update_item_image_accepts_empty_caption_as_null(
    test_client: TestClient,
    db_session: Session,
    tmp_path,
    monkeypatch,
) -> None:
    from io import BytesIO

    from PIL import Image

    from app.services import image_storage

    monkeypatch.setattr(
        image_storage,
        "ITEM_IMAGE_ROOT",
        tmp_path,
    )

    household = create_test_household(
        db_session
    )

    category = create_test_book_category(
        db_session
    )

    create_response = test_client.post(
        "/items",
        json={
            "household_id": household.id,
            "category_id": category.id,
            "title": "Üres képaláírás teszt",
        },
    )

    item_public_id = (
        create_response.json()["public_id"]
    )

    image = Image.new(
        "RGB",
        (100, 80),
        "white",
    )

    buffer = BytesIO()

    image.save(
        buffer,
        format="JPEG",
    )

    image.close()

    upload_response = test_client.post(
        f"/items/{item_public_id}/images",
        files={
            "file": (
                "caption.jpg",
                buffer.getvalue(),
                "image/jpeg",
            ),
        },
        data={
            "caption": "Eredeti",
        },
    )

    image_public_id = (
        upload_response.json()["public_id"]
    )

    response = test_client.patch(
        f"/item-images/{image_public_id}",
        json={
            "caption": "   ",
        },
    )

    assert response.status_code == 200
    assert response.json()["caption"] is None


def test_delete_item_image_api(
    test_client: TestClient,
    db_session: Session,
    tmp_path,
    monkeypatch,
) -> None:
    from io import BytesIO

    from PIL import Image

    from app.models import ItemImage
    from app.services import image_storage

    monkeypatch.setattr(
        image_storage,
        "ITEM_IMAGE_ROOT",
        tmp_path,
    )

    household = create_test_household(
        db_session
    )

    category = create_test_book_category(
        db_session
    )

    create_response = test_client.post(
        "/items",
        json={
            "household_id": household.id,
            "category_id": category.id,
            "title": "Képtörlés teszt",
        },
    )

    item_public_id = (
        create_response.json()["public_id"]
    )

    image = Image.new(
        "RGB",
        (120, 90),
        "white",
    )

    buffer = BytesIO()

    image.save(
        buffer,
        format="JPEG",
    )

    image.close()

    upload_response = test_client.post(
        f"/items/{item_public_id}/images",
        files={
            "file": (
                "delete.jpg",
                buffer.getvalue(),
                "image/jpeg",
            ),
        },
    )

    assert upload_response.status_code == 201

    image_public_id = (
        upload_response.json()["public_id"]
    )

    image_record = db_session.query(
        ItemImage
    ).filter(
        ItemImage.public_id
        == image_public_id
    ).one()

    image_id = image_record.id

    stored_files = list(
        tmp_path.rglob("*.webp")
    )

    assert len(stored_files) == 2

    assert any(
        path.name.endswith(
            ".thumb.webp"
        )
        for path in stored_files
    )

    assert any(
        not path.name.endswith(
            ".thumb.webp"
        )
        for path in stored_files
    )

    assert stored_files[0].is_file()

    response = test_client.delete(
        f"/item-images/{image_public_id}"
    )

    assert response.status_code == 204
    assert response.content == b""

    assert db_session.get(
        ItemImage,
        image_id,
    ) is None

    assert list(
        tmp_path.rglob("*.webp")
    ) == []


def test_delete_primary_image_selects_replacement_api(
    test_client: TestClient,
    db_session: Session,
    tmp_path,
    monkeypatch,
) -> None:
    from io import BytesIO

    from PIL import Image

    from app.services import image_storage

    monkeypatch.setattr(
        image_storage,
        "ITEM_IMAGE_ROOT",
        tmp_path,
    )

    household = create_test_household(
        db_session
    )

    category = create_test_book_category(
        db_session
    )

    create_response = test_client.post(
        "/items",
        json={
            "household_id": household.id,
            "category_id": category.id,
            "title": "Elsődleges képtörlés teszt",
        },
    )

    item_public_id = (
        create_response.json()["public_id"]
    )

    def make_jpeg() -> bytes:
        image = Image.new(
            "RGB",
            (100, 80),
            "white",
        )

        buffer = BytesIO()

        image.save(
            buffer,
            format="JPEG",
        )

        image.close()

        return buffer.getvalue()

    first_response = test_client.post(
        f"/items/{item_public_id}/images",
        files={
            "file": (
                "first.jpg",
                make_jpeg(),
                "image/jpeg",
            ),
        },
        data={
            "sort_order": "20",
        },
    )

    second_response = test_client.post(
        f"/items/{item_public_id}/images",
        files={
            "file": (
                "second.jpg",
                make_jpeg(),
                "image/jpeg",
            ),
        },
        data={
            "sort_order": "10",
        },
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    first_public_id = (
        first_response.json()["public_id"]
    )

    second_public_id = (
        second_response.json()["public_id"]
    )

    response = test_client.delete(
        f"/item-images/{first_public_id}"
    )

    assert response.status_code == 204

    images_response = test_client.get(
        f"/items/{item_public_id}/images"
    )

    assert images_response.status_code == 200

    images = images_response.json()

    assert len(images) == 1
    assert images[0]["public_id"] == second_public_id
    assert images[0]["is_primary"] is True


def test_delete_item_image_returns_404_for_unknown_image(
    test_client: TestClient,
) -> None:
    response = test_client.delete(
        (
            "/item-images/"
            "01AAAAAAAAAAAAAAAAAAAAAAAA"
        )
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "A kép nem található."
    }


def test_delete_item_image_succeeds_when_file_is_missing(
    test_client: TestClient,
    db_session: Session,
) -> None:
    from app.models import ItemImage
    from app.services import (
        CollectionItemCreateInput,
        ItemImageCreateInput,
        create_collection_item,
        create_item_image,
    )

    household = create_test_household(
        db_session
    )

    category = create_test_book_category(
        db_session
    )

    item = create_collection_item(
        session=db_session,
        data=CollectionItemCreateInput(
            household_id=household.id,
            category_id=category.id,
            title="Hiányzó fájlos törlés teszt",
        ),
    )

    image = create_item_image(
        session=db_session,
        item=item,
        data=ItemImageCreateInput(
            stored_filename=(
                "2099/01/missing-delete.webp"
            ),
            mime_type="image/webp",
            file_size=100,
            width=100,
            height=100,
        ),
    )

    db_session.commit()

    image_id = image.id
    image_public_id = image.public_id

    response = test_client.delete(
        f"/item-images/{image_public_id}"
    )

    assert response.status_code == 204

    assert db_session.get(
        ItemImage,
        image_id,
    ) is None
