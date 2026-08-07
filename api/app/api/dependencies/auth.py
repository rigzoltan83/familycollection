"""
Autentikációs és háztartási jogosultsági dependency-k.
"""

from fastapi import (
    Depends,
    HTTPException,
    Request,
    status,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.models import HouseholdMember, User


ROLE_LEVELS = {
    "viewer": 10,
    "editor": 20,
    "admin": 30,
    "owner": 40,
}


def get_current_user(
    request: Request,
    session: Session = Depends(get_db_session),
) -> User:
    """
    Visszaadja az aktuálisan bejelentkezett,
    aktív felhasználót.

    Ha nincs érvényes session vagy a felhasználó
    már nem aktív, HTTP 401 választ ad.
    """
    user_id = request.session.get(
        "user_id"
    )

    if not isinstance(user_id, int):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nincs bejelentkezve.",
        )

    user = session.get(
        User,
        user_id,
    )

    if user is None or not user.is_active:
        request.session.clear()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nincs bejelentkezve.",
        )

    return user


def get_active_household_member(
    household_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    session: Session = Depends(get_db_session),
) -> HouseholdMember:
    """
    Visszaadja az aktuális user aktív tagságát
    a megadott háztartásban.

    Ha nincs aktív tagság, HTTP 403 választ ad.
    """
    membership = session.scalar(
        select(HouseholdMember).where(
            HouseholdMember.household_id
            == household_id,
            HouseholdMember.user_id
            == current_user.id,
            HouseholdMember.is_active.is_(True),
        )
    )

    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Nincs jogosultsága ehhez "
                "a háztartáshoz."
            ),
        )

    return membership


def _require_minimum_household_role(
    membership: HouseholdMember,
    *,
    minimum_role: str,
) -> HouseholdMember:
    """
    Ellenőrzi a háztartási szerepkör szintjét.
    """
    current_level = ROLE_LEVELS.get(
        membership.role,
        0,
    )

    required_level = ROLE_LEVELS[
        minimum_role
    ]

    if current_level < required_level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Nincs megfelelő jogosultsága "
                "ehhez a művelethez."
            ),
        )

    return membership


def require_household_viewer(
    membership: HouseholdMember = Depends(
        get_active_household_member
    ),
) -> HouseholdMember:
    """
    Legalább viewer jogosultság szükséges.
    """
    return _require_minimum_household_role(
        membership,
        minimum_role="viewer",
    )


def require_household_editor(
    membership: HouseholdMember = Depends(
        get_active_household_member
    ),
) -> HouseholdMember:
    """
    Legalább editor jogosultság szükséges.
    """
    return _require_minimum_household_role(
        membership,
        minimum_role="editor",
    )


def require_household_admin(
    membership: HouseholdMember = Depends(
        get_active_household_member
    ),
) -> HouseholdMember:
    """
    Legalább admin jogosultság szükséges.

    Az owner természetesen ezt is teljesíti.
    """
    return _require_minimum_household_role(
        membership,
        minimum_role="admin",
    )
