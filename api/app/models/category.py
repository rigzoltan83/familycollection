"""
Category SQLAlchemy modell.

Támogatja:

- a platform által biztosított rendszerkategóriákat;
- a háztartások által létrehozott saját kategóriákat.
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Category(Base):
    __tablename__ = "categories"

    __table_args__ = (
        CheckConstraint(
            """
            (
                is_system = true
                AND household_id IS NULL
            )
            OR
            (
                is_system = false
                AND household_id IS NOT NULL
            )
            """,
            name="ck_categories_system_household",
        ),
        Index(
            "uq_categories_system_slug",
            "slug",
            unique=True,
            postgresql_where=text("is_system = true"),
        ),
        Index(
            "uq_categories_household_slug",
            "household_id",
            "slug",
            unique=True,
            postgresql_where=text("household_id IS NOT NULL"),
        ),
        Index(
            "ix_categories_household_id",
            "household_id",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    household_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "households.id",
            ondelete="CASCADE",
        ),
        nullable=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    slug: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    icon: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    is_system: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )

    supports_barcode: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )

    metadata_lookup_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="manual",
        server_default=text("'manual'"),
    )

    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    household: Mapped["Household | None"] = relationship()

    def __repr__(self) -> str:
        return (
            f"Category(id={self.id!r}, "
            f"name={self.name!r}, "
            f"slug={self.slug!r}, "
            f"is_system={self.is_system!r})"
        )
