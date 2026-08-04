"""
FamilyCollection felhasználói jelszó visszaállítása.

Futtatás az api könyvtárból:

    python -m scripts.reset_user_password
"""

from getpass import getpass

from sqlalchemy import func, select

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import User


def read_password() -> str:
    password = getpass("Új jelszó: ")
    confirmation = getpass("Új jelszó ismét: ")

    if password != confirmation:
        raise ValueError("A két jelszó nem egyezik.")

    if len(password) < 12:
        raise ValueError(
            "A jelszó legalább 12 karakter hosszú legyen."
        )

    return password


def main() -> None:
    email = input("Felhasználó e-mail címe: ").strip().lower()

    if not email:
        print("Hiba: az e-mail cím nem lehet üres.")
        raise SystemExit(1)

    try:
        new_password = read_password()
    except ValueError as error:
        print(f"Hiba: {error}")
        raise SystemExit(1) from error

    with SessionLocal() as session:
        user = session.scalar(
            select(User).where(
                func.lower(User.email) == email
            )
        )

        if user is None:
            print("Hiba: a felhasználó nem található.")
            raise SystemExit(1)

        user.password_hash = hash_password(new_password)
        session.commit()

    print()
    print("A jelszó sikeresen módosult.")
    print(f"Felhasználó: {email}")


if __name__ == "__main__":
    main()
