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


def get_user_by_email(
    session: Session,
    email: str,
) -> User | None:
    """
    Felhasználó keresése kis- és nagybetűtől függetlenül.
    """
    normalized_email = normalize_email(email)

    if not normalized_email:
        return None

    return session.scalar(
        select(User).where(
            func.lower(User.email) == normalized_email
        )
    )


def authenticate_user(
    session: Session,
    email: str,
    password: str,
) -> User | None:
    """
    Aktív felhasználó hitelesítése.

    Sikertelen hitelesítés esetén nem különbözteti meg,
    hogy az e-mail vagy a jelszó volt hibás.
    """
    user = get_user_by_email(
        session=session,
        email=email,
    )

    if user is None or not user.is_active:
        return None

    if not verify_password(
        plain_password=password,
        hashed_password=user.password_hash,
    ):
        return None

    return user
