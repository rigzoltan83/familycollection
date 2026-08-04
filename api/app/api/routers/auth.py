"""
Autentikációs HTTP-végpontok.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.schemas import LoginRequest, LoginResponse
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
    request: LoginRequest,
    session: Session = Depends(get_db_session),
) -> LoginResponse:
    """
    Felhasználó hitelesítése e-mail címmel és jelszóval.

    Hibás e-mail vagy jelszó esetén egységes hibaüzenetet ad,
    így nem árulja el, hogy létezik-e az adott felhasználó.
    """
    user = authenticate_user(
        session=session,
        email=str(request.email),
        password=request.password,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Hibás e-mail cím vagy jelszó.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    return LoginResponse(
        status="authenticated",
        user=user,
    )
