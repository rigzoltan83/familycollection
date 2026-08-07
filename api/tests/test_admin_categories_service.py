from sqlalchemy.orm import Session

from app.models import Category, Household
from app.services import (
    create_household_category,
    list_household_categories,
    slugify_category_name,
    update_household_category,
)


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


def test_slugify_category_name() -> None:
    assert (
        slugify_category_name(
            "Társasjáték gyűjtemény"
        )
        == "tarsasjatek-gyujtemeny"
    )


def test_create_household_category(
    db_session: Session,
) -> None:
    household = create_test_household(
        db_session,
        name="Első háztartás",
        slug="category-service-first",
    )

    category = create_household_category(
        session=db_session,
        household_id=household.id,
        name="  Saját   filmek  ",
        description="  Filmgyűjtemény  ",
        icon="  film  ",
        supports_barcode=True,
        sort_order=20,
    )

    assert category.household_id == household.id
    assert category.name == "Saját filmek"
    assert category.slug == "sajat-filmek"
    assert category.description == "Filmgyűjtemény"
    assert category.icon == "film"
    assert category.is_system is False
    assert category.is_active is True
    assert category.supports_barcode is True
    assert category.metadata_lookup_type == "manual"
    assert category.sort_order == 20


def test_duplicate_slug_gets_suffix(
    db_session: Session,
) -> None:
    household = create_test_household(
        db_session,
        name="Slug háztartás",
        slug="category-service-slug",
    )

    first = create_household_category(
        session=db_session,
        household_id=household.id,
        name="Filmek",
        description=None,
        icon=None,
        supports_barcode=False,
        sort_order=0,
    )

    second = create_household_category(
        session=db_session,
        household_id=household.id,
        name="Filmek",
        description=None,
        icon=None,
        supports_barcode=False,
        sort_order=0,
    )

    assert first.slug == "filmek"
    assert second.slug == "filmek-2"


def test_same_slug_allowed_in_other_household(
    db_session: Session,
) -> None:
    first_household = create_test_household(
        db_session,
        name="Első",
        slug="category-service-household-1",
    )

    second_household = create_test_household(
        db_session,
        name="Második",
        slug="category-service-household-2",
    )

    first = create_household_category(
        session=db_session,
        household_id=first_household.id,
        name="Filmek",
        description=None,
        icon=None,
        supports_barcode=False,
        sort_order=0,
    )

    second = create_household_category(
        session=db_session,
        household_id=second_household.id,
        name="Filmek",
        description=None,
        icon=None,
        supports_barcode=False,
        sort_order=0,
    )

    assert first.slug == "filmek"
    assert second.slug == "filmek"


def test_list_contains_system_and_own_categories_only(
    db_session: Session,
) -> None:
    first_household = create_test_household(
        db_session,
        name="Első",
        slug="category-service-list-1",
    )

    second_household = create_test_household(
        db_session,
        name="Második",
        slug="category-service-list-2",
    )

    system_category = create_system_category(
        db_session
    )

    own_category = create_household_category(
        session=db_session,
        household_id=first_household.id,
        name="Saját kategória",
        description=None,
        icon=None,
        supports_barcode=False,
        sort_order=20,
    )

    foreign_category = create_household_category(
        session=db_session,
        household_id=second_household.id,
        name="Másik kategória",
        description=None,
        icon=None,
        supports_barcode=False,
        sort_order=20,
    )

    categories = list_household_categories(
        session=db_session,
        household_id=first_household.id,
    )

    category_ids = {
        category.id
        for category in categories
    }

    assert system_category.id in category_ids
    assert own_category.id in category_ids
    assert foreign_category.id not in category_ids


def test_update_household_category(
    db_session: Session,
) -> None:
    household = create_test_household(
        db_session,
        name="Update háztartás",
        slug="category-service-update",
    )

    category = create_household_category(
        session=db_session,
        household_id=household.id,
        name="Régi név",
        description=None,
        icon=None,
        supports_barcode=False,
        sort_order=0,
    )

    updated = update_household_category(
        session=db_session,
        household_id=household.id,
        category_id=category.id,
        name="Új kategória",
        description=" Új leírás ",
        icon=" star ",
        supports_barcode=True,
        sort_order=30,
        is_active=False,
        fields_set={
            "name",
            "description",
            "icon",
            "supports_barcode",
            "sort_order",
            "is_active",
        },
    )

    assert updated.name == "Új kategória"
    assert updated.slug == "uj-kategoria"
    assert updated.description == "Új leírás"
    assert updated.icon == "star"
    assert updated.supports_barcode is True
    assert updated.sort_order == 30
    assert updated.is_active is False


def test_system_category_cannot_be_updated(
    db_session: Session,
) -> None:
    household = create_test_household(
        db_session,
        name="System protection",
        slug="category-service-system",
    )

    system_category = create_system_category(
        db_session
    )

    try:
        update_household_category(
            session=db_session,
            household_id=household.id,
            category_id=system_category.id,
            name="Átírva",
            description=None,
            icon=None,
            supports_barcode=None,
            sort_order=None,
            is_active=None,
            fields_set={"name"},
        )

    except ValueError as error:
        assert str(error) == (
            "Rendszerkategória nem módosítható."
        )

    else:
        raise AssertionError(
            "A rendszerkategória módosítása "
            "nem dobott ValueError hibát."
        )


def test_foreign_household_category_cannot_be_updated(
    db_session: Session,
) -> None:
    first_household = create_test_household(
        db_session,
        name="Első",
        slug="category-service-foreign-1",
    )

    second_household = create_test_household(
        db_session,
        name="Második",
        slug="category-service-foreign-2",
    )

    foreign_category = create_household_category(
        session=db_session,
        household_id=second_household.id,
        name="Másiké",
        description=None,
        icon=None,
        supports_barcode=False,
        sort_order=0,
    )

    try:
        update_household_category(
            session=db_session,
            household_id=first_household.id,
            category_id=foreign_category.id,
            name="Nem szabad",
            description=None,
            icon=None,
            supports_barcode=None,
            sort_order=None,
            is_active=None,
            fields_set={"name"},
        )

    except ValueError as error:
        assert str(error) == (
            "A kategória nem található."
        )

    else:
        raise AssertionError(
            "Másik household kategóriájának "
            "módosítása nem dobott ValueError hibát."
        )
