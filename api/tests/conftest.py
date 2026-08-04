"""
Közös pytest konfiguráció.

A tesztek kizárólag a külön familycollection_test adatbázist
használhatják. A normál adatbázis használatát biztonsági ellenőrzés
akadályozza meg.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base
from app import models  # noqa: F401
from settings import TEST_DATABASE_URL


def validate_test_database_url() -> str:
    """
    Ellenőrzi, hogy valóban külön tesztadatbázist használunk.
    """
    if not TEST_DATABASE_URL:
        raise RuntimeError(
            "A TEST_DATABASE_URL nincs beállítva."
        )

    database_name = TEST_DATABASE_URL.rsplit("/", 1)[-1]

    if database_name != "familycollection_test":
        raise RuntimeError(
            "A tesztek csak a familycollection_test adatbázison "
            "futhatnak."
        )

    return TEST_DATABASE_URL


TEST_ENGINE = create_engine(
    validate_test_database_url(),
    pool_pre_ping=True,
)

TestingSessionLocal = sessionmaker(
    bind=TEST_ENGINE,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=Session,
)


@pytest.fixture(scope="session", autouse=True)
def prepare_test_database():
    """
    A tesztfutás elején létrehozza, a végén eltávolítja
    az SQLAlchemy által kezelt teszttáblákat.
    """
    Base.metadata.drop_all(bind=TEST_ENGINE)
    Base.metadata.create_all(bind=TEST_ENGINE)

    yield

    Base.metadata.drop_all(bind=TEST_ENGINE)


@pytest.fixture
def db_session():
    """
    Minden teszthez külön tranzakciót biztosít.

    A teszt végén rollback történik, így a tesztek nem hagynak
    tartós adatot maguk után.
    """
    connection = TEST_ENGINE.connect()
    transaction = connection.begin()

    session = TestingSessionLocal(
        bind=connection,
    )

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
