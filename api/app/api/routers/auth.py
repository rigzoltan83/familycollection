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

from app.core.database import get_db_session
from app.models import User
from app.schemas import (
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
def get_current_user(
    request: Request,
    session: Session = Depends(get_db_session),
) -> AuthenticatedUserResponse:
    """
    Az aktuálisan bejelentkezett felhasználó.
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

    return AuthenticatedUserResponse.model_validate(
        user
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
