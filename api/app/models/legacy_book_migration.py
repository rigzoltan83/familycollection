"""
LegacyBookMigration SQLAlchemy modell.

A régi books rekordokat kapcsolja össze az új CollectionItem
rekordokkal, és megőrzi a migrációhoz szükséges forrásadatokat.
"""

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.mixins import PublicEntityMixin


class LegacyBookMigration(
    PublicEntityMixin,
    Base,
):
    __tablename__ = "legacy_book_migrations"

    __table_args__ = (
        UniqueConstraint(
            "legacy_book_id",
            name="uq_legacy_book_migrations_legacy_book_id",
        ),
        UniqueConstraint(
            "collection_item_id",
            name="uq_legacy_book_migrations_collection_item_id",
        ),
        CheckConstraint(
            """
            migration_status IN (
                'pending',
                'migrated',
                'warning',
                'error'
            )
            """,
            name="ck_legacy_book_migrations_status",
        ),
        Index(
            "ix_legacy_book_migrations_status",
            "migration_status",
        ),
        Index(
            "ix_legacy_book_migrations_legacy_location_id",
            "legacy_location_id",
        ),
    )

    legacy_book_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    collection_item_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "collection_items.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    legacy_location_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    legacy_isbn: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    legacy_borrowed_to: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    legacy_room: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    legacy_shelf: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    legacy_slot: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    migration_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending",
    )

    migration_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    collection_item: Mapped["CollectionItem | None"] = relationship()

    def __repr__(self) -> str:
        return (
            f"LegacyBookMigration(id={self.id!r}, "
            f"legacy_book_id={self.legacy_book_id!r}, "
            f"collection_item_id={self.collection_item_id!r}, "
            f"migration_status={self.migration_status!r})"
        )
