from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.models import (
    Household,
    HouseholdMember,
    User,
)
from app.services import (
    create_household_user,
    list_household_users,
    update_household_user,
)


TEST_PASSWORD = "Admin-user-teszt-123"


def create_test_household(
    session: Session,
    *,
    name: str = "Admin user teszt",
    slug: str = "admin-user-test",
) -> Household:
    household = Household(
        name=name,
        slug=slug,
        is_active=True,
    )

    session.add(household)
    session.flush()

    return household


def test_create_household_user_creates_user_and_membership(
    db_session: Session,
) -> None:
    household = create_test_household(
        db_session
    )

    record = create_household_user(
        db_session,
        household_id=household.id,
        email="  UJ.USER@EXAMPLE.COM  ",
        display_name="  Új felhasználó  ",
        password=TEST_PASSWORD,
        role="editor",
    )

    assert record.email == "uj.user@example.com"
    assert record.display_name == "Új felhasználó"
    assert record.role == "editor"
    assert record.user_is_active is True
    assert record.membership_is_active is True

    user = db_session.get(
        User,
        record.user_id,
    )

    assert user is not None
    assert user.email == "uj.user@example.com"
    assert user.display_name == "Új felhasználó"
    assert user.is_platform_admin is False
    assert user.email_verified is False
    assert user.password_hash != TEST_PASSWORD

    assert verify_password(
        plain_password=TEST_PASSWORD,
        hashed_password=user.password_hash,
    ) is True

    membership = db_session.get(
        HouseholdMember,
        record.membership_id,
    )

    assert membership is not None
    assert membership.household_id == household.id
    assert membership.user_id == user.id
    assert membership.role == "editor"
    assert membership.is_active is True


def test_create_household_user_rejects_duplicate_email(
    db_session: Session,
) -> None:
    household = create_test_household(
        db_session
    )

    create_household_user(
        db_session,
        household_id=household.id,
        email="duplicate@example.com",
        display_name="Első user",
        password=TEST_PASSWORD,
        role="viewer",
    )

    try:
        create_household_user(
            db_session,
            household_id=household.id,
            email="DUPLICATE@example.com",
            display_name="Második user",
            password=TEST_PASSWORD,
            role="viewer",
        )

    except ValueError as error:
        assert str(error) == (
            "Ezzel az e-mail címmel már "
            "létezik felhasználó."
        )

    else:
        raise AssertionError(
            "Duplikált e-mail esetén ValueError várt."
        )


def test_create_household_user_rejects_owner_role(
    db_session: Session,
) -> None:
    household = create_test_household(
        db_session
    )

    try:
        create_household_user(
            db_session,
            household_id=household.id,
            email="owner@example.com",
            display_name="Owner próba",
            password=TEST_PASSWORD,
            role="owner",
        )

    except ValueError as error:
        assert str(error) == (
            "Csak viewer, editor vagy admin "
            "szerepkör adható."
        )

    else:
        raise AssertionError(
            "Owner szerepkörnél ValueError várt."
        )


def test_create_household_user_rejects_short_password(
    db_session: Session,
) -> None:
    household = create_test_household(
        db_session
    )

    try:
        create_household_user(
            db_session,
            household_id=household.id,
            email="short@example.com",
            display_name="Rövid jelszó",
            password="12345678901",
            role="viewer",
        )

    except ValueError as error:
        assert str(error) == (
            "A jelszó legalább 12 karakter "
            "hosszú legyen."
        )

    else:
        raise AssertionError(
            "Rövid jelszónál ValueError várt."
        )


def test_list_household_users_returns_all_memberships(
    db_session: Session,
) -> None:
    household = create_test_household(
        db_session
    )

    first = create_household_user(
        db_session,
        household_id=household.id,
        email="first@example.com",
        display_name="Első",
        password=TEST_PASSWORD,
        role="viewer",
    )

    second = create_household_user(
        db_session,
        household_id=household.id,
        email="second@example.com",
        display_name="Második",
        password=TEST_PASSWORD,
        role="admin",
    )

    records = list_household_users(
        db_session,
        household_id=household.id,
    )

    assert [
        record.user_id
        for record in records
    ] == [
        first.user_id,
        second.user_id,
    ]

    assert records[0].role == "viewer"
    assert records[1].role == "admin"


def test_list_household_users_does_not_include_other_household(
    db_session: Session,
) -> None:
    first_household = create_test_household(
        db_session,
        name="Első háztartás",
        slug="first-admin-household",
    )

    second_household = create_test_household(
        db_session,
        name="Második háztartás",
        slug="second-admin-household",
    )

    first_user = create_household_user(
        db_session,
        household_id=first_household.id,
        email="first-household@example.com",
        display_name="Első household user",
        password=TEST_PASSWORD,
        role="viewer",
    )

    create_household_user(
        db_session,
        household_id=second_household.id,
        email="second-household@example.com",
        display_name="Második household user",
        password=TEST_PASSWORD,
        role="admin",
    )

    records = list_household_users(
        db_session,
        household_id=first_household.id,
    )

    assert len(records) == 1
    assert records[0].user_id == first_user.user_id


def test_update_household_user_changes_fields(
    db_session: Session,
) -> None:
    household = create_test_household(
        db_session
    )

    acting_admin = create_household_user(
        db_session,
        household_id=household.id,
        email="acting-admin@example.com",
        display_name="Aktív admin",
        password=TEST_PASSWORD,
        role="admin",
    )

    target = create_household_user(
        db_session,
        household_id=household.id,
        email="target@example.com",
        display_name="Régi név",
        password=TEST_PASSWORD,
        role="viewer",
    )

    updated = update_household_user(
        db_session,
        household_id=household.id,
        user_id=target.user_id,
        acting_user_id=acting_admin.user_id,
        display_name="  Új név  ",
        role="editor",
        membership_is_active=False,
        fields_set={
            "display_name",
            "role",
            "membership_is_active",
        },
    )

    assert updated.display_name == "Új név"
    assert updated.role == "editor"
    assert (
        updated.membership_is_active
        is False
    )

    user = db_session.get(
        User,
        target.user_id,
    )

    membership = db_session.get(
        HouseholdMember,
        target.membership_id,
    )

    assert user is not None
    assert user.display_name == "Új név"

    assert membership is not None
    assert membership.role == "editor"
    assert membership.is_active is False


def test_update_household_user_rejects_owner(
    db_session: Session,
) -> None:
    household = create_test_household(
        db_session
    )

    acting_admin = create_household_user(
        db_session,
        household_id=household.id,
        email="admin-owner-test@example.com",
        display_name="Admin",
        password=TEST_PASSWORD,
        role="admin",
    )

    owner_user = User(
        email="owner-test@example.com",
        password_hash="unused",
        display_name="Owner",
        is_active=True,
        is_platform_admin=False,
        email_verified=True,
    )

    db_session.add(owner_user)
    db_session.flush()

    owner_membership = HouseholdMember(
        household_id=household.id,
        user_id=owner_user.id,
        role="owner",
        is_active=True,
    )

    db_session.add(owner_membership)
    db_session.flush()

    try:
        update_household_user(
            db_session,
            household_id=household.id,
            user_id=owner_user.id,
            acting_user_id=acting_admin.user_id,
            role="viewer",
            fields_set={"role"},
        )

    except ValueError as error:
        assert str(error) == (
            "Az owner tagság ezen a felületen "
            "nem módosítható."
        )

    else:
        raise AssertionError(
            "Owner módosításánál ValueError várt."
        )


def test_update_household_user_rejects_own_role_change(
    db_session: Session,
) -> None:
    household = create_test_household(
        db_session
    )

    acting_admin = create_household_user(
        db_session,
        household_id=household.id,
        email="self-role@example.com",
        display_name="Saját admin",
        password=TEST_PASSWORD,
        role="admin",
    )

    try:
        update_household_user(
            db_session,
            household_id=household.id,
            user_id=acting_admin.user_id,
            acting_user_id=acting_admin.user_id,
            role="viewer",
            fields_set={"role"},
        )

    except ValueError as error:
        assert str(error) == (
            "A saját szerepkör nem "
            "módosítható."
        )

    else:
        raise AssertionError(
            "Saját role módosításánál "
            "ValueError várt."
        )


def test_update_household_user_rejects_own_deactivation(
    db_session: Session,
) -> None:
    household = create_test_household(
        db_session
    )

    acting_admin = create_household_user(
        db_session,
        household_id=household.id,
        email="self-disable@example.com",
        display_name="Saját admin",
        password=TEST_PASSWORD,
        role="admin",
    )

    try:
        update_household_user(
            db_session,
            household_id=household.id,
            user_id=acting_admin.user_id,
            acting_user_id=acting_admin.user_id,
            membership_is_active=False,
            fields_set={
                "membership_is_active"
            },
        )

    except ValueError as error:
        assert str(error) == (
            "A saját háztartási tagság "
            "nem tiltható le."
        )

    else:
        raise AssertionError(
            "Saját tagság letiltásánál "
            "ValueError várt."
        )


def test_update_household_user_allows_own_display_name(
    db_session: Session,
) -> None:
    household = create_test_household(
        db_session
    )

    acting_admin = create_household_user(
        db_session,
        household_id=household.id,
        email="self-name@example.com",
        display_name="Régi admin név",
        password=TEST_PASSWORD,
        role="admin",
    )

    updated = update_household_user(
        db_session,
        household_id=household.id,
        user_id=acting_admin.user_id,
        acting_user_id=acting_admin.user_id,
        display_name="Új admin név",
        fields_set={"display_name"},
    )

    assert (
        updated.display_name
        == "Új admin név"
    )

    assert updated.role == "admin"
    assert (
        updated.membership_is_active
        is True
    )
