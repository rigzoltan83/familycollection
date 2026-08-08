from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import (
    Category,
    CategoryField,
    CategoryFieldOption,
    Household,
    HouseholdMember,
    User,
)


TEST_PASSWORD = "Category-fields-test-123"


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


def create_user(
    session: Session,
    *,
    household: Household,
    email: str,
    role: str,
) -> User:
    user = User(
        email=email,
        username=(
            email
            .split("@", 1)[0]
            .lower()
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


def create_category(
    session: Session,
    *,
    household_id: int | None,
    name: str,
    slug: str,
    is_system: bool,
) -> Category:
    category = Category(
        household_id=household_id,
        name=name,
        slug=slug,
        description=None,
        icon=None,
        is_system=is_system,
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
    name: str,
    field_key: str,
    field_type: str,
    sort_order: int,
    is_active: bool = True,
) -> CategoryField:
    field = CategoryField(
        category_id=category.id,
        name=name,
        field_key=field_key,
        field_type=field_type,
        description=None,
        placeholder=None,
        is_required=False,
        is_searchable=False,
        is_filterable=False,
        is_visible_in_list=True,
        is_active=is_active,
        sort_order=sort_order,
        validation_rules={},
        default_value={},
    )

    session.add(field)
    session.flush()

    return field


def test_viewer_can_list_system_category_fields(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_household(
        db_session,
        name="System field household",
        slug="system-field-household",
    )

    viewer = create_user(
        db_session,
        household=household,
        email="system-field-viewer@example.com",
        role="viewer",
    )

    category = create_category(
        db_session,
        household_id=None,
        name="Könyv",
        slug="book-system-fields",
        is_system=True,
    )

    create_field(
        db_session,
        category=category,
        name="Kiadó",
        field_key="publisher",
        field_type="text",
        sort_order=20,
    )

    create_field(
        db_session,
        category=category,
        name="Szerző",
        field_key="author",
        field_type="text",
        sort_order=10,
    )

    login(
        test_client,
        user=viewer,
    )

    response = test_client.get(
        (
            f"/households/{household.id}"
            f"/categories/{category.id}"
            "/fields"
        )
    )

    assert response.status_code == 200

    data = response.json()

    assert [
        field["field_key"]
        for field in data
    ] == [
        "author",
        "publisher",
    ]


def test_household_category_fields_are_available(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_household(
        db_session,
        name="Own category household",
        slug="own-category-fields",
    )

    viewer = create_user(
        db_session,
        household=household,
        email="own-category-viewer@example.com",
        role="viewer",
    )

    category = create_category(
        db_session,
        household_id=household.id,
        name="Társasjáték",
        slug="boardgame-fields",
        is_system=False,
    )

    create_field(
        db_session,
        category=category,
        name="Játékidő",
        field_key="play_time",
        field_type="integer",
        sort_order=10,
    )

    login(
        test_client,
        user=viewer,
    )

    response = test_client.get(
        (
            f"/households/{household.id}"
            f"/categories/{category.id}"
            "/fields"
        )
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["field_key"] == "play_time"
    assert data[0]["field_type"] == "integer"


def test_other_household_category_is_rejected(
    test_client: TestClient,
    db_session: Session,
) -> None:
    first_household = create_household(
        db_session,
        name="First household",
        slug="first-category-fields",
    )

    second_household = create_household(
        db_session,
        name="Second household",
        slug="second-category-fields",
    )

    viewer = create_user(
        db_session,
        household=first_household,
        email="cross-field-viewer@example.com",
        role="viewer",
    )

    category = create_category(
        db_session,
        household_id=second_household.id,
        name="Másik gyűjtemény",
        slug="other-category-fields",
        is_system=False,
    )

    login(
        test_client,
        user=viewer,
    )

    response = test_client.get(
        (
            f"/households/{first_household.id}"
            f"/categories/{category.id}"
            "/fields"
        )
    )

    assert response.status_code == 400


def test_inactive_fields_are_hidden(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_household(
        db_session,
        name="Inactive field household",
        slug="inactive-field-household",
    )

    viewer = create_user(
        db_session,
        household=household,
        email="inactive-field-viewer@example.com",
        role="viewer",
    )

    category = create_category(
        db_session,
        household_id=household.id,
        name="Teszt gyűjtemény",
        slug="inactive-field-category",
        is_system=False,
    )

    create_field(
        db_session,
        category=category,
        name="Aktív mező",
        field_key="active_field",
        field_type="text",
        sort_order=10,
        is_active=True,
    )

    create_field(
        db_session,
        category=category,
        name="Inaktív mező",
        field_key="inactive_field",
        field_type="text",
        sort_order=20,
        is_active=False,
    )

    login(
        test_client,
        user=viewer,
    )

    response = test_client.get(
        (
            f"/households/{household.id}"
            f"/categories/{category.id}"
            "/fields"
        )
    )

    assert response.status_code == 200

    data = response.json()

    assert [
        field["field_key"]
        for field in data
    ] == [
        "active_field",
    ]


def test_select_field_returns_only_active_options(
    test_client: TestClient,
    db_session: Session,
) -> None:
    household = create_household(
        db_session,
        name="Option household",
        slug="option-field-household",
    )

    viewer = create_user(
        db_session,
        household=household,
        email="option-viewer@example.com",
        role="viewer",
    )

    category = create_category(
        db_session,
        household_id=household.id,
        name="Játék",
        slug="option-field-category",
        is_system=False,
    )

    field = create_field(
        db_session,
        category=category,
        name="Állapot",
        field_key="condition",
        field_type="single_select",
        sort_order=10,
    )

    db_session.add_all(
        [
            CategoryFieldOption(
                field_id=field.id,
                value="new",
                label="Új",
                sort_order=20,
                is_active=True,
            ),
            CategoryFieldOption(
                field_id=field.id,
                value="used",
                label="Használt",
                sort_order=10,
                is_active=True,
            ),
            CategoryFieldOption(
                field_id=field.id,
                value="hidden",
                label="Rejtett",
                sort_order=30,
                is_active=False,
            ),
        ]
    )

    db_session.flush()

    login(
        test_client,
        user=viewer,
    )

    response = test_client.get(
        (
            f"/households/{household.id}"
            f"/categories/{category.id}"
            "/fields"
        )
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1

    options = data[0]["options"]

    assert [
        option["value"]
        for option in options
    ] == [
        "used",
        "new",
    ]

    assert [
        option["label"]
        for option in options
    ] == [
        "Használt",
        "Új",
    ]
