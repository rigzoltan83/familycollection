"""
Közös pytest konfiguráció.

A tesztek kizárólag a külön familycollection_test adatbázist
használhatják. A normál adatbázis használatát biztonsági ellenőrzés
akadályozza meg.
"""

import os

# Tests exercise FastAPI directly at root-level API paths.
# Keep session cookies independent from deployment subpaths.
os.environ["APP_BASE_PATH"] = ""
os.environ["SESSION_COOKIE_PATH"] = "/"

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base
from app import models  # noqa: F401
from settings import TEST_DATABASE_URL

from fastapi.testclient import TestClient

from app.core.database import get_db_session
from main import app

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
    Minden teszt külön külső tranzakcióban fut.

    A tesztelt alkalmazás session.commit() hívásai csak egy belső
    SAVEPOINT-ot zárnak le. A teszt végén a külső tranzakció
    visszagörgetése minden módosítást eltávolít.
    """
    connection = TEST_ENGINE.connect()
    outer_transaction = connection.begin()

    session = TestingSessionLocal(
        bind=connection,
        join_transaction_mode="create_savepoint",
    )

    session.begin_nested()

    @event.listens_for(
        session,
        "after_transaction_end",
    )
    def restart_savepoint(
        session: Session,
        transaction,
    ) -> None:
        if (
            transaction.nested
            and transaction._parent is not None
            and not transaction._parent.nested
        ):
            session.begin_nested()

    try:
        yield session
    finally:
        event.remove(
            session,
            "after_transaction_end",
            restart_savepoint,
        )

        session.close()

        if outer_transaction.is_active:
            outer_transaction.rollback()

        connection.close()


@pytest.fixture
def test_client(db_session: Session):
    """
    FastAPI tesztkliens.

    Az alkalmazás normál adatbázis-session dependency-jét
    a külön tesztadatbázis sessionjére cseréli.
    """
    def override_get_db_session():
        yield db_session

    app.dependency_overrides[get_db_session] = (
        override_get_db_session
    )

    try:
        with TestClient(
            app,
            base_url="https://testserver",
        ) as client:
            yield client
    finally:
        app.dependency_overrides.clear()
