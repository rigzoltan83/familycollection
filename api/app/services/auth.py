"""
Autentikációs üzleti szolgáltatások.

Ez a modul független a HTTP-rétegtől:
felhasználót keres és jelszót ellenőriz.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.models import User


def normalize_email(email: str) -> str:
    """
    E-mail cím normalizálása kereséshez és tároláshoz.
    """
    return email.strip().lower()


def normalize_username(username: str) -> str:
    """
    Felhasználónév normalizálása kereséshez
    és összehasonlításhoz.
    """
    return username.strip().lower()


def get_user_by_email(
    session: Session,
    email: str,
) -> User | None:
    """
    Felhasználó keresése e-mail cím alapján,
    kis- és nagybetűtől függetlenül.
    """
    normalized_email = normalize_email(
        email
    )

    if not normalized_email:
        return None

    return session.scalar(
        select(User).where(
            func.lower(User.email)
            == normalized_email
        )
    )


def get_user_by_username(
    session: Session,
    username: str,
) -> User | None:
    """
    Felhasználó keresése felhasználónév alapján,
    kis- és nagybetűtől függetlenül.
    """
    normalized_username = normalize_username(
        username
    )

    if not normalized_username:
        return None

    return session.scalar(
        select(User).where(
            func.lower(User.username)
            == normalized_username
        )
    )


def authenticate_user(
    session: Session,
    identifier: str,
    password: str,
) -> User | None:
    """
    Aktív felhasználó hitelesítése
    e-mail címmel vagy felhasználónévvel.

    Sikertelen hitelesítés esetén nem különbözteti meg,
    hogy az azonosító vagy a jelszó volt hibás.
    """
    normalized_identifier = (
        identifier.strip()
    )

    if not normalized_identifier:
        return None

    if "@" in normalized_identifier:
        user = get_user_by_email(
            session=session,
            email=normalized_identifier,
        )
    else:
        user = get_user_by_username(
            session=session,
            username=normalized_identifier,
        )

    if user is None or not user.is_active:
        return None

    if not verify_password(
        plain_password=password,
        hashed_password=user.password_hash,
    ):
        return None

    return user
