from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Category,
    CategoryField,
    CategoryFieldOption,
    CollectionItem,
    Household,
    ItemFieldValue,
    ItemIdentifier,
    User,
)
from app.services import (
    CollectionItemCreateInput,
    IdentifierInput,
    create_collection_item,
)


def create_test_household(
    session: Session,
    *,
    name: str = "Teszt háztartás",
    slug: str = "test-household",
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
    email: str = "item-test@example.com",
) -> User:
    user = User(
        email=email,
        password_hash="test-hash",
        display_name="Teszt felhasználó",
        is_active=True,
        is_platform_admin=False,
        email_verified=True,
    )

    session.add(user)
    session.flush()

    return user


def create_book_category(
    session: Session,
) -> Category:
    category = Category(
        household_id=None,
        name="Könyv",
        slug="book-test",
        description="Teszt könyvkategória",
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


def test_create_collection_item_with_identifier_and_fields(
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    user = create_test_user(db_session)
    category = create_book_category(db_session)

    item = create_collection_item(
        session=db_session,
        data=CollectionItemCreateInput(
            household_id=household.id,
            category_id=category.id,
            title="Az",
            created_by_user_id=user.id,
            identifiers=[
                IdentifierInput(
                    identifier_type="isbn13",
                    identifier_value="9789631234567",
                    is_primary=True,
                )
            ],
            field_values={
                "author": "Stephen King",
                "publish_year": 1986,
            },
        ),
    )

    assert item.id is not None
    assert item.public_id is not None
    assert item.title == "Az"
    assert item.household_id == household.id
    assert item.category_id == category.id
    assert item.created_by_user_id == user.id
    assert item.updated_by_user_id == user.id

    identifier = db_session.scalar(
        select(ItemIdentifier).where(
            ItemIdentifier.item_id == item.id
        )
    )

    assert identifier is not None
    assert identifier.identifier_type == "isbn13"
    assert identifier.identifier_value == "9789631234567"
    assert identifier.is_primary is True

    field_values = db_session.scalars(
        select(ItemFieldValue).where(
            ItemFieldValue.item_id == item.id
        )
    ).all()

    assert len(field_values) == 2

    values_by_key = {
        field_value.field.field_key: field_value
        for field_value in field_values
    }

    assert values_by_key["author"].value_text == "Stephen King"
    assert values_by_key["publish_year"].value_integer == 1986


def test_create_collection_item_rejects_unknown_field(
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_book_category(db_session)

    try:
        create_collection_item(
            session=db_session,
            data=CollectionItemCreateInput(
                household_id=household.id,
                category_id=category.id,
                title="Teszt könyv",
                field_values={
                    "unknown_field": "érték",
                },
            ),
        )
    except ValueError as error:
        assert "Ismeretlen kategóriamezők" in str(error)
    else:
        raise AssertionError("ValueError kivételre számítottunk.")


def test_create_collection_item_rejects_empty_title(
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_book_category(db_session)

    try:
        create_collection_item(
            session=db_session,
            data=CollectionItemCreateInput(
                household_id=household.id,
                category_id=category.id,
                title="   ",
            ),
        )
    except ValueError as error:
        assert str(error) == "A cím nem lehet üres."
    else:
        raise AssertionError("ValueError kivételre számítottunk.")


def test_create_collection_item_rejects_invalid_boolean_value(
    db_session: Session,
) -> None:
    household = create_test_household(db_session)

    category = Category(
        household_id=None,
        name="Teszt kategória",
        slug="boolean-test",
        is_system=True,
        is_active=True,
        supports_barcode=False,
        metadata_lookup_type="manual",
        sort_order=10,
    )

    db_session.add(category)
    db_session.flush()

    db_session.add(
        CategoryField(
            category_id=category.id,
            name="Aktív?",
            field_key="flag",
            field_type="boolean",
            is_required=False,
            is_searchable=False,
            is_filterable=True,
            is_visible_in_list=False,
            is_active=True,
            sort_order=10,
            validation_rules={},
            default_value={},
        )
    )

    db_session.flush()

    try:
        create_collection_item(
            session=db_session,
            data=CollectionItemCreateInput(
                household_id=household.id,
                category_id=category.id,
                title="Teszt tárgy",
                field_values={
                    "flag": "igen",
                },
            ),
        )
    except ValueError as error:
        assert "logikai értéket vár" in str(error)
    else:
        raise AssertionError("ValueError kivételre számítottunk.")


def test_create_collection_item_rejects_other_household_category(
    db_session: Session,
) -> None:
    first_household = create_test_household(
        db_session,
        name="Első háztartás",
        slug="first-household",
    )

    second_household = create_test_household(
        db_session,
        name="Második háztartás",
        slug="second-household",
    )

    category = Category(
        household_id=first_household.id,
        name="Saját kategória",
        slug="private-category",
        is_system=False,
        is_active=True,
        supports_barcode=False,
        metadata_lookup_type="manual",
        sort_order=10,
    )

    db_session.add(category)
    db_session.flush()

    try:
        create_collection_item(
            session=db_session,
            data=CollectionItemCreateInput(
                household_id=second_household.id,
                category_id=category.id,
                title="Tiltott tárgy",
            ),
        )
    except ValueError as error:
        assert "nem a megadott háztartáshoz tartozik" in str(error)
    else:
        raise AssertionError("ValueError kivételre számítottunk.")

def test_create_collection_item_rejects_year_below_minimum(
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_book_category(db_session)

    try:
        create_collection_item(
            session=db_session,
            data=CollectionItemCreateInput(
                household_id=household.id,
                category_id=category.id,
                title="Régi könyv",
                field_values={
                    "publish_year": 999,
                },
            ),
        )
    except ValueError as error:
        assert "nem lehet kisebb mint 1000" in str(error)
    else:
        raise AssertionError("ValueError kivételre számítottunk.")


def test_create_collection_item_accepts_valid_single_select(
    db_session: Session,
) -> None:
    household = create_test_household(db_session)

    category = Category(
        household_id=None,
        name="Állapottesztes kategória",
        slug="condition-test",
        is_system=True,
        is_active=True,
        supports_barcode=False,
        metadata_lookup_type="manual",
        sort_order=10,
    )

    db_session.add(category)
    db_session.flush()

    field = CategoryField(
        category_id=category.id,
        name="Állapot",
        field_key="condition",
        field_type="single_select",
        is_required=False,
        is_searchable=False,
        is_filterable=True,
        is_visible_in_list=True,
        is_active=True,
        sort_order=10,
        validation_rules={},
        default_value={},
    )

    db_session.add(field)
    db_session.flush()

    db_session.add_all(
        [
            CategoryFieldOption(
                field_id=field.id,
                value="new",
                label="Új",
                sort_order=10,
                is_active=True,
            ),
            CategoryFieldOption(
                field_id=field.id,
                value="used",
                label="Használt",
                sort_order=20,
                is_active=True,
            ),
        ]
    )

    db_session.flush()

    item = create_collection_item(
        session=db_session,
        data=CollectionItemCreateInput(
            household_id=household.id,
            category_id=category.id,
            title="Teszt tárgy",
            field_values={
                "condition": "used",
            },
        ),
    )

    value = db_session.scalar(
        select(ItemFieldValue).where(
            ItemFieldValue.item_id == item.id,
            ItemFieldValue.field_id == field.id,
        )
    )

    assert value is not None
    assert value.value_json == "used"


def test_create_collection_item_rejects_invalid_single_select(
    db_session: Session,
) -> None:
    household = create_test_household(db_session)

    category = Category(
        household_id=None,
        name="Tiltott választás teszt",
        slug="invalid-condition-test",
        is_system=True,
        is_active=True,
        supports_barcode=False,
        metadata_lookup_type="manual",
        sort_order=10,
    )

    db_session.add(category)
    db_session.flush()

    field = CategoryField(
        category_id=category.id,
        name="Állapot",
        field_key="condition",
        field_type="single_select",
        is_required=False,
        is_searchable=False,
        is_filterable=True,
        is_visible_in_list=True,
        is_active=True,
        sort_order=10,
        validation_rules={},
        default_value={},
    )

    db_session.add(field)
    db_session.flush()

    db_session.add(
        CategoryFieldOption(
            field_id=field.id,
            value="new",
            label="Új",
            sort_order=10,
            is_active=True,
        )
    )

    db_session.flush()

    try:
        create_collection_item(
            session=db_session,
            data=CollectionItemCreateInput(
                household_id=household.id,
                category_id=category.id,
                title="Teszt tárgy",
                field_values={
                    "condition": "broken",
                },
            ),
        )
    except ValueError as error:
        assert "Érvénytelen választási érték" in str(error)
    else:
        raise AssertionError("ValueError kivételre számítottunk.")
