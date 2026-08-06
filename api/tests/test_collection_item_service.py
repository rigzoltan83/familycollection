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
    ItemImage,
    User,
)
from app.services import (
    CollectionItemCreateInput,
    CollectionItemUpdateInput,
    update_collection_item,
    IdentifierInput,
    create_collection_item,
    ItemImageCreateInput,
    create_item_image,
    delete_item_image,
    get_item_image_by_public_id,
    list_item_images,
    set_primary_item_image,
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


def create_test_collection_item(
    session: Session,
) -> CollectionItem:
    household = create_test_household(
        session,
    )

    category = create_book_category(
        session,
    )

    return create_collection_item(
        session=session,
        data=CollectionItemCreateInput(
            household_id=household.id,
            category_id=category.id,
            title="Képtesztes könyv",
        ),
    )


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

def test_update_collection_item_changes_basic_fields(
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
            title="Régi cím",
            subtitle="Régi alcím",
            notes="Régi megjegyzés",
            created_by_user_id=user.id,
        ),
    )

    updated_item = update_collection_item(
        session=db_session,
        item=item,
        data=CollectionItemUpdateInput(
            title="Új cím",
            subtitle="Új alcím",
            notes="Új megjegyzés",
            status="archived",
            updated_by_user_id=user.id,
        ),
    )

    assert updated_item.title == "Új cím"
    assert updated_item.subtitle == "Új alcím"
    assert updated_item.notes == "Új megjegyzés"
    assert updated_item.status == "archived"
    assert updated_item.updated_by_user_id == user.id


def test_update_collection_item_keeps_unspecified_fields(
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_book_category(db_session)

    item = create_collection_item(
        session=db_session,
        data=CollectionItemCreateInput(
            household_id=household.id,
            category_id=category.id,
            title="Eredeti cím",
            subtitle="Eredeti alcím",
            notes="Eredeti megjegyzés",
        ),
    )

    update_collection_item(
        session=db_session,
        item=item,
        data=CollectionItemUpdateInput(
            title="Módosított cím",
        ),
    )

    assert item.title == "Módosított cím"
    assert item.subtitle == "Eredeti alcím"
    assert item.notes == "Eredeti megjegyzés"
    assert item.status == "active"


def test_update_collection_item_replaces_identifiers(
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_book_category(db_session)

    item = create_collection_item(
        session=db_session,
        data=CollectionItemCreateInput(
            household_id=household.id,
            category_id=category.id,
            title="Teszt könyv",
            identifiers=[
                IdentifierInput(
                    identifier_type="isbn13",
                    identifier_value="9789631111111",
                    is_primary=True,
                )
            ],
        ),
    )

    update_collection_item(
        session=db_session,
        item=item,
        data=CollectionItemUpdateInput(
            identifiers=[
                IdentifierInput(
                    identifier_type="isbn10",
                    identifier_value="9632222222",
                    is_primary=True,
                )
            ],
        ),
    )

    db_session.refresh(item)

    identifiers = db_session.scalars(
        select(ItemIdentifier).where(
            ItemIdentifier.item_id == item.id
        )
    ).all()

    assert len(identifiers) == 1
    assert identifiers[0].identifier_type == "isbn10"
    assert identifiers[0].identifier_value == "9632222222"


def test_update_collection_item_replaces_dynamic_fields(
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_book_category(db_session)

    item = create_collection_item(
        session=db_session,
        data=CollectionItemCreateInput(
            household_id=household.id,
            category_id=category.id,
            title="Teszt könyv",
            field_values={
                "author": "Régi szerző",
                "publish_year": 1980,
            },
        ),
    )

    update_collection_item(
        session=db_session,
        item=item,
        data=CollectionItemUpdateInput(
            field_values={
                "author": "Új szerző",
                "publish_year": 2020,
            },
        ),
    )

    db_session.refresh(item)

    field_values = db_session.scalars(
        select(ItemFieldValue).where(
            ItemFieldValue.item_id == item.id
        )
    ).all()

    values_by_key = {
        field_value.field.field_key: field_value
        for field_value in field_values
    }

    assert len(field_values) == 2
    assert values_by_key["author"].value_text == "Új szerző"
    assert values_by_key["publish_year"].value_integer == 2020


def test_update_collection_item_rejects_unknown_field(
    db_session: Session,
) -> None:
    household = create_test_household(db_session)
    category = create_book_category(db_session)

    item = create_collection_item(
        session=db_session,
        data=CollectionItemCreateInput(
            household_id=household.id,
            category_id=category.id,
            title="Teszt könyv",
        ),
    )

    try:
        update_collection_item(
            session=db_session,
            item=item,
            data=CollectionItemUpdateInput(
                field_values={
                    "unknown": "érték",
                },
            ),
        )
    except ValueError as error:
        assert "Ismeretlen kategóriamezők" in str(error)
    else:
        raise AssertionError("ValueError kivételre számítottunk.")


def test_create_first_item_image_is_primary(
    db_session: Session,
) -> None:
    item = create_test_collection_item(
        db_session,
    )

    image = create_item_image(
        session=db_session,
        item=item,
        data=ItemImageCreateInput(
            stored_filename=(
                "2026/08/first.webp"
            ),
            original_filename="first.jpg",
            caption="Borító",
            mime_type="image/webp",
            file_size=12345,
            width=800,
            height=600,
            sort_order=10,
        ),
    )

    assert image.id is not None
    assert image.public_id is not None
    assert image.item_id == item.id
    assert image.is_active is True
    assert image.is_primary is True
    assert image.caption == "Borító"
    assert image.original_filename == "first.jpg"


def test_create_second_item_image_is_not_primary(
    db_session: Session,
) -> None:
    item = create_test_collection_item(
        db_session,
    )

    first = create_item_image(
        session=db_session,
        item=item,
        data=ItemImageCreateInput(
            stored_filename=(
                "2026/08/first.webp"
            ),
            mime_type="image/webp",
            file_size=100,
        ),
    )

    second = create_item_image(
        session=db_session,
        item=item,
        data=ItemImageCreateInput(
            stored_filename=(
                "2026/08/second.webp"
            ),
            mime_type="image/webp",
            file_size=200,
        ),
    )

    assert first.is_primary is True
    assert second.is_primary is False


def test_create_explicit_primary_replaces_existing_primary(
    db_session: Session,
) -> None:
    item = create_test_collection_item(
        db_session,
    )

    first = create_item_image(
        session=db_session,
        item=item,
        data=ItemImageCreateInput(
            stored_filename=(
                "2026/08/first.webp"
            ),
            mime_type="image/webp",
            file_size=100,
        ),
    )

    second = create_item_image(
        session=db_session,
        item=item,
        data=ItemImageCreateInput(
            stored_filename=(
                "2026/08/second.webp"
            ),
            mime_type="image/webp",
            file_size=200,
            is_primary=True,
        ),
    )

    db_session.refresh(first)
    db_session.refresh(second)

    assert first.is_primary is False
    assert second.is_primary is True


def test_create_first_image_can_explicitly_be_non_primary(
    db_session: Session,
) -> None:
    item = create_test_collection_item(
        db_session,
    )

    image = create_item_image(
        session=db_session,
        item=item,
        data=ItemImageCreateInput(
            stored_filename=(
                "2026/08/non-primary.webp"
            ),
            mime_type="image/webp",
            file_size=100,
            is_primary=False,
        ),
    )

    assert image.is_primary is False


def test_list_item_images_orders_primary_then_sort_order(
    db_session: Session,
) -> None:
    item = create_test_collection_item(
        db_session,
    )

    first = create_item_image(
        session=db_session,
        item=item,
        data=ItemImageCreateInput(
            stored_filename=(
                "2026/08/first.webp"
            ),
            mime_type="image/webp",
            file_size=100,
            sort_order=30,
        ),
    )

    second = create_item_image(
        session=db_session,
        item=item,
        data=ItemImageCreateInput(
            stored_filename=(
                "2026/08/second.webp"
            ),
            mime_type="image/webp",
            file_size=100,
            sort_order=10,
        ),
    )

    third = create_item_image(
        session=db_session,
        item=item,
        data=ItemImageCreateInput(
            stored_filename=(
                "2026/08/third.webp"
            ),
            mime_type="image/webp",
            file_size=100,
            sort_order=20,
            is_primary=True,
        ),
    )

    images = list_item_images(
        session=db_session,
        item=item,
    )

    assert images == [
        third,
        second,
        first,
    ]


def test_list_item_images_hides_inactive_by_default(
    db_session: Session,
) -> None:
    item = create_test_collection_item(
        db_session,
    )

    active = create_item_image(
        session=db_session,
        item=item,
        data=ItemImageCreateInput(
            stored_filename=(
                "2026/08/active.webp"
            ),
            mime_type="image/webp",
            file_size=100,
        ),
    )

    inactive = create_item_image(
        session=db_session,
        item=item,
        data=ItemImageCreateInput(
            stored_filename=(
                "2026/08/inactive.webp"
            ),
            mime_type="image/webp",
            file_size=100,
        ),
    )

    inactive.is_active = False
    db_session.flush()

    assert list_item_images(
        session=db_session,
        item=item,
    ) == [active]

    assert set(
        list_item_images(
            session=db_session,
            item=item,
            include_inactive=True,
        )
    ) == {
        active,
        inactive,
    }


def test_get_item_image_by_public_id(
    db_session: Session,
) -> None:
    item = create_test_collection_item(
        db_session,
    )

    image = create_item_image(
        session=db_session,
        item=item,
        data=ItemImageCreateInput(
            stored_filename=(
                "2026/08/find.webp"
            ),
            mime_type="image/webp",
            file_size=100,
        ),
    )

    found = get_item_image_by_public_id(
        session=db_session,
        public_id=image.public_id,
    )

    assert found is image

    assert get_item_image_by_public_id(
        session=db_session,
        public_id="",
    ) is None


def test_set_primary_item_image(
    db_session: Session,
) -> None:
    item = create_test_collection_item(
        db_session,
    )

    first = create_item_image(
        session=db_session,
        item=item,
        data=ItemImageCreateInput(
            stored_filename=(
                "2026/08/first.webp"
            ),
            mime_type="image/webp",
            file_size=100,
        ),
    )

    second = create_item_image(
        session=db_session,
        item=item,
        data=ItemImageCreateInput(
            stored_filename=(
                "2026/08/second.webp"
            ),
            mime_type="image/webp",
            file_size=100,
        ),
    )

    set_primary_item_image(
        session=db_session,
        image=second,
    )

    db_session.refresh(first)
    db_session.refresh(second)

    assert first.is_primary is False
    assert second.is_primary is True


def test_set_primary_rejects_inactive_image(
    db_session: Session,
) -> None:
    item = create_test_collection_item(
        db_session,
    )

    image = create_item_image(
        session=db_session,
        item=item,
        data=ItemImageCreateInput(
            stored_filename=(
                "2026/08/inactive.webp"
            ),
            mime_type="image/webp",
            file_size=100,
        ),
    )

    image.is_active = False
    db_session.flush()

    try:
        set_primary_item_image(
            session=db_session,
            image=image,
        )
    except ValueError as error:
        assert (
            str(error)
            == "Inaktív kép nem lehet elsődleges."
        )
    else:
        raise AssertionError(
            "ValueError kivételre számítottunk."
        )


def test_delete_primary_item_image_selects_replacement(
    db_session: Session,
) -> None:
    item = create_test_collection_item(
        db_session,
    )

    first = create_item_image(
        session=db_session,
        item=item,
        data=ItemImageCreateInput(
            stored_filename=(
                "2026/08/first.webp"
            ),
            mime_type="image/webp",
            file_size=100,
            sort_order=30,
        ),
    )

    second = create_item_image(
        session=db_session,
        item=item,
        data=ItemImageCreateInput(
            stored_filename=(
                "2026/08/second.webp"
            ),
            mime_type="image/webp",
            file_size=100,
            sort_order=10,
        ),
    )

    third = create_item_image(
        session=db_session,
        item=item,
        data=ItemImageCreateInput(
            stored_filename=(
                "2026/08/third.webp"
            ),
            mime_type="image/webp",
            file_size=100,
            sort_order=20,
        ),
    )

    assert first.is_primary is True

    first_id = first.id

    delete_item_image(
        session=db_session,
        image=first,
    )

    assert db_session.get(
        ItemImage,
        first_id,
    ) is None

    db_session.refresh(second)
    db_session.refresh(third)

    assert second.is_primary is True
    assert third.is_primary is False


def test_create_item_image_validates_caption_and_dimensions(
    db_session: Session,
) -> None:
    item = create_test_collection_item(
        db_session,
    )

    invalid_cases = [
        (
            ItemImageCreateInput(
                stored_filename="2026/08/a.webp",
                mime_type="image/webp",
                file_size=-1,
            ),
            "nem lehet negatív",
        ),
        (
            ItemImageCreateInput(
                stored_filename="2026/08/b.webp",
                mime_type="image/webp",
                file_size=1,
                width=0,
            ),
            "szélességének pozitívnak",
        ),
        (
            ItemImageCreateInput(
                stored_filename="2026/08/c.webp",
                mime_type="image/webp",
                file_size=1,
                height=0,
            ),
            "magasságának pozitívnak",
        ),
        (
            ItemImageCreateInput(
                stored_filename="2026/08/d.webp",
                mime_type="image/webp",
                file_size=1,
                caption="x" * 201,
            ),
            "legfeljebb 200 karakter",
        ),
    ]

    for data, expected_message in invalid_cases:
        try:
            create_item_image(
                session=db_session,
                item=item,
                data=data,
            )
        except ValueError as error:
            assert expected_message in str(error)
        else:
            raise AssertionError(
                "ValueError kivételre számítottunk."
            )
