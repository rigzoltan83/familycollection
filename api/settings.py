"""
FamilyCollection központi konfiguráció.

A beállításokat az api/.env fájlból és a környezeti változókból
olvassa be.

A valódi .env fájl nem kerül Gitbe.
"""

import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)


def get_required_setting(name: str) -> str:
    """
    Kötelező konfigurációs érték lekérése.

    Üres vagy hiányzó érték esetén az alkalmazás egyértelmű hibával
    áll le, ahelyett hogy hibás konfigurációval indulna el.
    """
    value = os.getenv(name)

    if value is None or not value.strip():
        raise RuntimeError(
            f"Hiányzó kötelező konfigurációs érték: {name}"
        )

    return value.strip()


def get_bool_setting(name: str, default: bool = False) -> bool:
    """
    Logikai konfigurációs érték beolvasása.

    Elfogadott igaz értékek:
    true, 1, yes, on

    Elfogadott hamis értékek:
    false, 0, no, off
    """
    raw_value = os.getenv(name)

    if raw_value is None:
        return default

    normalized = raw_value.strip().lower()

    if normalized in {"true", "1", "yes", "on"}:
        return True

    if normalized in {"false", "0", "no", "off"}:
        return False

    raise RuntimeError(
        f"Érvénytelen logikai konfiguráció: "
        f"{name}={raw_value!r}"
    )


DB_HOST = get_required_setting("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = get_required_setting("DB_NAME")
DB_USER = get_required_setting("DB_USER")
DB_PASS = get_required_setting("DB_PASS")

ISBNDB_KEY = os.getenv("ISBNDB_KEY", "").strip()

USE_ISBNDB = get_bool_setting(
    "USE_ISBNDB",
    default=False,
)

USE_OPENLIBRARY = get_bool_setting(
    "USE_OPENLIBRARY",
    default=True,
)

USE_ISBNSEARCH = get_bool_setting(
    "USE_ISBNSEARCH",
    default=False,
)
