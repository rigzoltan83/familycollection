"""
Háztartási felhasználó-adminisztráció üzleti logikája.
"""

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import (
    Household,
    HouseholdMember,
    User,
)
from app.services.auth import (
    normalize_email,
    normalize_username,
)


ASSIGNABLE_ROLES = {
    "viewer",
    "editor",
    "admin",
}


@dataclass(frozen=True)
class HouseholdUserRecord:
    user_id: int
    email: str
    username: str
    display_name: str
    user_is_active: bool

    membership_id: int
    role: str
    membership_is_active: bool

    joined_at: object


def _validate_username(
    username: str,
) -> str:
    """
    Felhasználónév normalizálása és ellenőrzése.
    """
    normalized_username = normalize_username(
        username
    )

    if len(normalized_username) < 3:
        raise ValueError(
            "A felhasználónév legalább "
            "3 karakter hosszú legyen."
        )

    if len(normalized_username) > 100:
        raise ValueError(
            "A felhasználónév legfeljebb "
            "100 karakter hosszú lehet."
        )

    if not all(
        character.isalnum()
        or character in "._-"
        for character in normalized_username
    ):
        raise ValueError(
            "A felhasználónév csak betűt, számot, "
            "pontot, kötőjelet és aláhúzást "
            "tartalmazhat."
        )

    return normalized_username


def _validate_assignable_role(
    role: str,
) -> str:
    normalized_role = role.strip().lower()

    if normalized_role not in ASSIGNABLE_ROLES:
        raise ValueError(
            "Csak viewer, editor vagy admin "
            "szerepkör adható."
        )

    return normalized_role


def _get_active_household(
    session: Session,
    household_id: int,
) -> Household:
    household = session.scalar(
        select(Household).where(
            Household.id == household_id,
            Household.is_active.is_(True),
        )
    )

    if household is None:
        raise ValueError(
            "Az aktív háztartás nem található."
        )

    return household


def _build_household_user_record(
    membership: HouseholdMember,
) -> HouseholdUserRecord:
    user = membership.user


    return HouseholdUserRecord(
        user_id=user.id,
        email=user.email,
        username=user.username,
        display_name=user.display_name,
        user_is_active=user.is_active,
        membership_id=membership.id,
        role=membership.role,
        membership_is_active=membership.is_active,
        joined_at=membership.joined_at,
    )


def list_household_users(
    session: Session,
    household_id: int,
) -> list[HouseholdUserRecord]:
    """
    A háztartás összes tagságának listázása.
    """
    _get_active_household(
        session=session,
        household_id=household_id,
    )

    memberships = session.scalars(
        select(HouseholdMember)
        .where(
            HouseholdMember.household_id
            == household_id
        )
        .order_by(
            HouseholdMember.id
        )
    ).all()

    return [
        _build_household_user_record(
            membership
        )
        for membership in memberships
    ]


def create_household_user(
    session: Session,
    *,
    household_id: int,
    email: str,
    username: str,
    display_name: str,
    password: str,
    role: str,
) -> HouseholdUserRecord:
    """
    Új platformfelhasználó és hozzá tartozó
    household-tagság létrehozása.
    """
    _get_active_household(
        session=session,
        household_id=household_id,
    )

    normalized_email = normalize_email(
        email
    )

    normalized_username = _validate_username(
        username
    )

    normalized_display_name = (
        display_name.strip()
    )

    normalized_role = (
        _validate_assignable_role(role)
    )

    if not normalized_email:
        raise ValueError(
            "Az e-mail cím nem lehet üres."
        )

    if not normalized_display_name:
        raise ValueError(
            "A megjelenített név nem lehet üres."
        )

    if len(password) < 12:
        raise ValueError(
            "A jelszó legalább 12 karakter "
            "hosszú legyen."
        )

    existing_user = session.scalar(
        select(User).where(
            func.lower(User.email)
            == normalized_email
        )
    )

    if existing_user is not None:
        raise ValueError(
            "Ezzel az e-mail címmel már "
            "létezik felhasználó."
        )

    existing_username = session.scalar(
        select(User).where(
            func.lower(User.username)
            == normalized_username
        )
    )

    if existing_username is not None:
        raise ValueError(
            "Ezzel a felhasználónévvel már "
            "létezik felhasználó."
        )

    user = User(
        email=normalized_email,
        username=normalized_username,
        password_hash=hash_password(
            password
        ),
        display_name=normalized_display_name,
        is_active=True,
        is_platform_admin=False,
        email_verified=False,
    )

    session.add(user)
    session.flush()

    membership = HouseholdMember(
        household_id=household_id,
        user_id=user.id,
        role=normalized_role,
        is_active=True,
    )

    session.add(membership)
    session.flush()

    return _build_household_user_record(
        membership
    )


def update_household_user(
    session: Session,
    *,
    household_id: int,
    user_id: int,
    acting_user_id: int,
    display_name: str | None = None,
    role: str | None = None,
    membership_is_active: bool | None = None,
    fields_set: set[str] | None = None,
) -> HouseholdUserRecord:
    """
    Meglévő household-tagság és a hozzá tartozó
    felhasználó adminisztratív módosítása.

    Az owner tagság ezen az általános admin
    műveleten keresztül nem módosítható.

    A bejelentkezett admin a saját szerepkörét
    vagy tagsági aktív állapotát sem módosíthatja.
    """
    _get_active_household(
        session=session,
        household_id=household_id,
    )

    effective_fields = fields_set or set()

    if not effective_fields:
        raise ValueError(
            "Legalább egy módosítandó mezőt "
            "meg kell adni."
        )

    membership = session.scalar(
        select(HouseholdMember).where(
            HouseholdMember.household_id
            == household_id,
            HouseholdMember.user_id
            == user_id,
        )
    )

    if membership is None:
        raise ValueError(
            "A felhasználó nem tagja ennek "
            "a háztartásnak."
        )

    if membership.role == "owner":
        raise ValueError(
            "Az owner tagság ezen a felületen "
            "nem módosítható."
        )

    user = membership.user

    if "display_name" in effective_fields:
        normalized_display_name = (
            display_name.strip()
            if display_name is not None
            else ""
        )

        if not normalized_display_name:
            raise ValueError(
                "A megjelenített név nem lehet üres."
            )

        user.display_name = (
            normalized_display_name
        )

    if "role" in effective_fields:
        if user_id == acting_user_id:
            raise ValueError(
                "A saját szerepkör nem "
                "módosítható."
            )

        if role is None:
            raise ValueError(
                "A szerepkör nem lehet üres."
            )

        membership.role = (
            _validate_assignable_role(role)
        )

    if (
        "membership_is_active"
        in effective_fields
    ):
        if membership_is_active is None:
            raise ValueError(
                "Az aktív állapot nem lehet üres."
            )

        if (
            user_id == acting_user_id
            and not membership_is_active
        ):
            raise ValueError(
                "A saját háztartási tagság "
                "nem tiltható le."
            )

        membership.is_active = (
            membership_is_active
        )

    session.flush()

    return _build_household_user_record(
        membership
    )
