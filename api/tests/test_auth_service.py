from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import User
from app.services import authenticate_user, get_user_by_email


TEST_EMAIL = "teszt@example.com"
TEST_PASSWORD = "FamilyCollection-teszt-123"


def create_test_user(
    session: Session,
    *,
    email: str = TEST_EMAIL,
    password: str = TEST_PASSWORD,
    is_active: bool = True,
) -> User:
    user = User(
        email=email,
        password_hash=hash_password(password),
        display_name="Teszt felhasználó",
        is_active=is_active,
        is_platform_admin=False,
        email_verified=True,
    )

    session.add(user)
    session.flush()

    return user


def test_get_user_by_email_is_case_insensitive(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)

    found_user = get_user_by_email(
        db_session,
        "TESZT@EXAMPLE.COM",
    )

    assert found_user is not None
    assert found_user.id == user.id
    assert found_user.email == TEST_EMAIL


def test_authenticate_user_accepts_correct_password(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)

    authenticated_user = authenticate_user(
        session=db_session,
        email=TEST_EMAIL,
        password=TEST_PASSWORD,
    )

    assert authenticated_user is not None
    assert authenticated_user.id == user.id


def test_authenticate_user_rejects_wrong_password(
    db_session: Session,
) -> None:
    create_test_user(db_session)

    authenticated_user = authenticate_user(
        session=db_session,
        email=TEST_EMAIL,
        password="rossz-jelszo",
    )

    assert authenticated_user is None


def test_authenticate_user_rejects_unknown_email(
    db_session: Session,
) -> None:
    authenticated_user = authenticate_user(
        session=db_session,
        email="nincsilyen@example.com",
        password=TEST_PASSWORD,
    )

    assert authenticated_user is None


def test_authenticate_user_rejects_inactive_user(
    db_session: Session,
) -> None:
    create_test_user(
        db_session,
        is_active=False,
    )

    authenticated_user = authenticate_user(
        session=db_session,
        email=TEST_EMAIL,
        password=TEST_PASSWORD,
    )

    assert authenticated_user is None
