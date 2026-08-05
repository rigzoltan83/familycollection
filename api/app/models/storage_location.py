"""
StorageLocation SQLAlchemy modell.

Háztartásonként hierarchikus tárolóhelyeket kezel.

Példák:

- Nappali
- Nappali / Újpolc
- Nappali / Újpolc / 1. rekesz
- Hálószoba / Szekrény jobb / 4. rekesz

A hierarchia tetszőleges mélységű lehet.
"""

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.mixins import PublicEntityMixin


class StorageLocation(
    PublicEntityMixin,
    Base,
):
    __tablename__ = "storage_locations"

    __table_args__ = (
        CheckConstraint(
            """
            location_type IN (
                'room',
                'shelf',
                'cabinet',
                'drawer',
                'box',
                'slot',
                'area',
                'other'
            )
            """,
            name="ck_storage_locations_type",
        ),
        CheckConstraint(
            "sort_order >= 0",
            name="ck_storage_locations_sort_order",
        ),
        Index(
            "ix_storage_locations_household_id",
            "household_id",
        ),
        Index(
            "ix_storage_locations_parent_id",
            "parent_id",
        ),
        Index(
            "ix_storage_locations_household_parent",
            "household_id",
            "parent_id",
        ),
        Index(
            "uq_storage_locations_root_slug",
            "household_id",
            "slug",
            unique=True,
            postgresql_where=text("parent_id IS NULL"),
        ),
        Index(
            "uq_storage_locations_child_slug",
            "household_id",
            "parent_id",
            "slug",
            unique=True,
            postgresql_where=text("parent_id IS NOT NULL"),
        ),
    )

    household_id: Mapped[int] = mapped_column(
        ForeignKey(
            "households.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "storage_locations.id",
            ondelete="CASCADE",
        ),
        nullable=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    slug: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    location_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="other",
        server_default=text("'other'"),
    )

    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )

    household: Mapped["Household"] = relationship()

    parent: Mapped["StorageLocation | None"] = relationship(
        remote_side="StorageLocation.id",
        back_populates="children",
    )

    children: Mapped[list["StorageLocation"]] = relationship(
        back_populates="parent",
        cascade="all, delete-orphan",
        single_parent=True,
    )

    def __repr__(self) -> str:
        return (
            f"StorageLocation(id={self.id!r}, "
            f"household_id={self.household_id!r}, "
            f"parent_id={self.parent_id!r}, "
            f"name={self.name!r}, "
            f"location_type={self.location_type!r})"
        )
