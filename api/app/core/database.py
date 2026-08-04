"""
SQLAlchemy adatbázis-alapok.

A jelenlegi psycopg2-alapú db.py továbbra is működik.
Ezt a modult az új platformrészek használják majd.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from settings import DATABASE_URL


class Base(DeclarativeBase):
    """
    Minden új SQLAlchemy modell közös alaposztálya.
    """

    pass


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=Session,
)


def get_db_session() -> Generator[Session, None, None]:
    """
    FastAPI dependencyként használható adatbázis-session.

    A session minden kérés végén biztosan lezáródik.
    """
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()
