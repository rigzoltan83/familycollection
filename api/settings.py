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

def build_database_url() -> str:
    """
    SQLAlchemy és Alembic számára használható PostgreSQL kapcsolat.

    A jelszó speciális karaktereit URL-kompatibilis formára alakítjuk.
    """
    from urllib.parse import quote_plus

    encoded_user = quote_plus(DB_USER)
    encoded_password = quote_plus(DB_PASS)

    return (
        f"postgresql+psycopg2://"
        f"{encoded_user}:{encoded_password}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )


DATABASE_URL = build_database_url()

APP_ENV = os.getenv(
    "APP_ENV",
    "development",
).strip().lower()


SESSION_SECRET_KEY = get_required_setting(
    "SESSION_SECRET_KEY"
)

SESSION_COOKIE_SECURE = get_bool_setting(
    "SESSION_COOKIE_SECURE",
    default=True,
)

SESSION_MAX_AGE_SECONDS = int(
    os.getenv(
        "SESSION_MAX_AGE_SECONDS",
        "2592000",
    )
)

if SESSION_MAX_AGE_SECONDS <= 0:
    raise RuntimeError(
        "A SESSION_MAX_AGE_SECONDS értékének "
        "pozitív egész számnak kell lennie."
    )


TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "",
).strip()

ITEM_IMAGE_ROOT = Path(
    os.getenv(
        "ITEM_IMAGE_ROOT",
        str(
            BASE_DIR.parent
            / "data"
            / "images"
            / "items"
        ),
    )
).expanduser().resolve()


ITEM_IMAGE_MAX_UPLOAD_BYTES = int(
    os.getenv(
        "ITEM_IMAGE_MAX_UPLOAD_BYTES",
        str(20 * 1024 * 1024),
    )
)


ITEM_IMAGE_MAX_DIMENSION = int(
    os.getenv(
        "ITEM_IMAGE_MAX_DIMENSION",
        "1920",
    )
)


ITEM_IMAGE_WEBP_QUALITY = int(
    os.getenv(
        "ITEM_IMAGE_WEBP_QUALITY",
        "82",
    )
)
