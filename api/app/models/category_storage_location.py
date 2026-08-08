"""
CategoryStorageLocation SQLAlchemy modell.

Háztartásonként összekapcsolja a kategóriákat
az adott kategóriában használható tárolóhelyekkel.

A kapcsolat rendszerkategóriák esetén is
háztartás-specifikus.

Ha include_descendants igaz, akkor a megadott
tárolóhely teljes leszármazotti ága is engedélyezett.
"""

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Index,
    Integer,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.core.database import Base


class CategoryStorageLocation(Base):
    __tablename__ = "category_storage_locations"

    __table_args__ = (
        UniqueConstraint(
            "household_id",
            "category_id",
            "storage_location_id",
            name=(
                "uq_category_storage_locations_"
                "household_category_location"
            ),
        ),
        Index(
            "ix_category_storage_locations_household_id",
            "household_id",
        ),
        Index(
            "ix_category_storage_locations_category_id",
            "category_id",
        ),
        Index(
            "ix_category_storage_locations_storage_location_id",
            "storage_location_id",
        ),
        Index(
            "ix_category_storage_locations_household_category",
            "household_id",
            "category_id",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    household_id: Mapped[int] = mapped_column(
        ForeignKey(
            "households.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    category_id: Mapped[int] = mapped_column(
        ForeignKey(
            "categories.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    storage_location_id: Mapped[int] = mapped_column(
        ForeignKey(
            "storage_locations.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    include_descendants: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )

    household: Mapped["Household"] = relationship()

    category: Mapped["Category"] = relationship(
        back_populates="storage_location_rules",
    )

    storage_location: Mapped["StorageLocation"] = relationship(
        back_populates="category_rules",
    )

    def __repr__(self) -> str:
        return (
            "CategoryStorageLocation("
            f"id={self.id!r}, "
            f"household_id={self.household_id!r}, "
            f"category_id={self.category_id!r}, "
            f"storage_location_id={self.storage_location_id!r}, "
            f"include_descendants={self.include_descendants!r})"
        )
