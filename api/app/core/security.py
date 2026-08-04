"""
FamilyCollection biztonsági segédfüggvények.

A jelszavakat Argon2id algoritmussal hash-eljük.
Nyers jelszó soha nem kerülhet adatbázisba vagy naplóba.
"""

from pwdlib import PasswordHash


password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """
    Nyers jelszó biztonságos hash-elése.
    """
    if not password:
        raise ValueError("A jelszó nem lehet üres.")

    return password_hash.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """
    Nyers jelszó ellenőrzése a tárolt hash alapján.

    Hibás vagy sérült hash esetén False értéket ad vissza.
    """
    if not plain_password or not hashed_password:
        return False

    try:
        return password_hash.verify(
            plain_password,
            hashed_password,
        )
    except Exception:
        return False
