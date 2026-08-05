from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import (
    Category,
    CategoryField,
    Household,
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
