"""
Első FamilyCollection platformadmin létrehozása.

A script:

- interaktívan bekéri az admin adatait;
- Argon2id algoritmussal hash-eli a jelszót;
- létrehozza a platformadmin felhasználót;
- owner szerepkörrel hozzákapcsolja az alapértelmezett háztartáshoz.

Futtatás az api könyvtárból:

    python scripts/bootstrap_admin.py
"""

from getpass import getpass
from pathlib import Path
import sys

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError


API_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(API_DIR))


from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import Household, HouseholdMember, User


DEFAULT_HOUSEHOLD_SLUG = "default-household"


def read_required_value(label: str) -> str:
    """
    Kötelező szöveges érték bekérése.
    """
    value = input(label).strip()

    if not value:
        raise ValueError(f"A mező nem lehet üres: {label}")

    return value


def read_password() -> str:
    """
    Jelszó kétszeri bekérése és alapellenőrzése.
    """
    password = getpass("Jelszó: ")
    password_confirmation = getpass("Jelszó ismét: ")

    if password != password_confirmation:
        raise ValueError("A két jelszó nem egyezik.")

    if len(password) < 12:
        raise ValueError(
            "A jelszó legalább 12 karakter hosszú legyen."
        )

    return password


def bootstrap_admin() -> None:
    """
    Első platformadmin és household owner tagság létrehozása.
    """
    print("FamilyCollection platformadmin létrehozása")
    print("-" * 44)

    email = read_required_value(
        "E-mail cím: "
    ).lower()

    username = read_required_value(
        "Felhasználónév: "
    ).lower()

    display_name = read_required_value(
        "Megjelenített név: "
    )

    password = read_password()
    password_hash = hash_password(password)

    with SessionLocal() as session:
        try:
            existing_user = session.scalar(
                select(User).where(
                    func.lower(User.email) == email
                )
            )

            if existing_user is not None:
                raise ValueError(
                    "Ezzel az e-mail címmel már létezik felhasználó."
                )

            if len(username) < 3:
                raise ValueError(
                    "A felhasználónév legalább "
                    "3 karakter hosszú legyen."
                )

            if len(username) > 100:
                raise ValueError(
                    "A felhasználónév legfeljebb "
                    "100 karakter hosszú lehet."
                )

            if not all(
                character.isalnum()
                or character in "._-"
                for character in username
            ):
                raise ValueError(
                    "A felhasználónév csak betűt, számot, "
                    "pontot, kötőjelet és aláhúzást "
                    "tartalmazhat."
                )

            existing_username = session.scalar(
                select(User).where(
                    func.lower(User.username)
                    == username
                )
            )

            if existing_username is not None:
                raise ValueError(
                    "Ezzel a felhasználónévvel már "
                    "létezik felhasználó."
                )

            household = session.scalar(
                select(Household).where(
                    Household.slug == DEFAULT_HOUSEHOLD_SLUG
                )
            )

            if household is None:
                raise RuntimeError(
                    "Az alapértelmezett háztartás nem található."
                )

            user = User(
                email=email,
                username=username,
                password_hash=password_hash,
                display_name=display_name,
                is_active=True,
                is_platform_admin=True,
                email_verified=True,
            )

            session.add(user)
            session.flush()

            membership = HouseholdMember(
                household_id=household.id,
                user_id=user.id,
                role="owner",
                is_active=True,
            )

            session.add(membership)
            session.commit()

        except Exception:
            session.rollback()
            raise

    print()
    print("A platformadmin sikeresen létrejött.")
    print(
        f"Felhasználónév: {username}"
    )
    print(
        f"E-mail: {email}"
    )
    print(f"Háztartás: {household.name}")
    print("Szerepkör: owner")


def main() -> None:
    try:
        bootstrap_admin()

    except (ValueError, RuntimeError) as error:
        print()
        print(f"Hiba: {error}")
        raise SystemExit(1) from error

    except IntegrityError as error:
        print()
        print(
            "Adatbázis-integritási hiba történt. "
            "Nem jött létre részleges felhasználó."
        )
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
