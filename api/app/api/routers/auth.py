"""
Autentikációs HTTP-végpontok.
"""

from datetime import datetime

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
)
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db_session
from app.models import User
from app.schemas import (
    AuthContextResponse,
    AuthHouseholdResponse,
    AuthenticatedUserResponse,
    LoginRequest,
    LoginResponse,
)
from app.services import authenticate_user


router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)


@router.post(
    "/login",
    response_model=LoginResponse,
)
def login(
    payload: LoginRequest,
    request: Request,
    session: Session = Depends(get_db_session),
) -> LoginResponse:
    """
    Felhasználó bejelentkeztetése.

    Sikeres hitelesítéskor a sessionbe kizárólag
    a felhasználó belső azonosítója kerül.
    """
    user = authenticate_user(
        session=session,
        email=str(payload.email),
        password=payload.password,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Hibás e-mail cím vagy jelszó.",
        )

    request.session.clear()

    request.session["user_id"] = user.id

    user.last_login_at = datetime.now()

    session.commit()
    session.refresh(user)

    return LoginResponse(
        status="authenticated",
        user=user,
    )


@router.get(
    "/me",
    response_model=AuthenticatedUserResponse,
)
def get_me(
    current_user: User = Depends(
        get_current_user
    ),
) -> AuthenticatedUserResponse:
    """
    Az aktuálisan bejelentkezett felhasználó.
    """
    return (
        AuthenticatedUserResponse.model_validate(
            current_user
        )
    )


@router.get(
    "/context",
    response_model=AuthContextResponse,
)
def get_auth_context(
    current_user: User = Depends(
        get_current_user
    ),
) -> AuthContextResponse:
    """
    A frontend indulásához szükséges
    felhasználói és háztartási kontextus.
    """
    households = []

    for membership in (
        current_user.household_memberships
    ):
        if not membership.is_active:
            continue

        household = membership.household

        if (
            household is None
            or not household.is_active
        ):
            continue

        households.append(
            AuthHouseholdResponse(
                id=household.id,
                name=household.name,
                slug=household.slug,
                role=membership.role,
            )
        )

    households.sort(
        key=lambda item: (
            item.name.lower(),
            item.id,
        )
    )

    return AuthContextResponse(
        user=(
            AuthenticatedUserResponse
            .model_validate(current_user)
        ),
        households=households,
    )


@router.post(
    "/logout",
)
def logout(
    request: Request,
) -> dict[str, str]:
    """
    Az aktuális session megszüntetése.
    """
    request.session.clear()

    return {
        "status": "logged_out",
    }
