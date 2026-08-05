"""
ItemStorageAssignment SQLAlchemy modell.

A gyűjteményi elemek fizikai tárolási helyét és a
helyváltoztatási előzményeket kezeli.

Egy CollectionItem időben több tárolási rekorddal rendelkezhet,
de egyszerre legfeljebb egy aktív hozzárendelése lehet.
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Index,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.mixins import PublicEntityMixin


class ItemStorageAssignment(
    PublicEntityMixin,
    Base,
):
    __tablename__ = "item_storage_assignments"

    __table_args__ = (
        Index(
            "ix_item_storage_assignments_item_id",
            "item_id",
        ),
        Index(
            "ix_item_storage_assignments_storage_location_id",
            "storage_location_id",
        ),
        Index(
            "ix_item_storage_assignments_moved_by_user_id",
            "moved_by_user_id",
        ),
        Index(
            "ix_item_storage_assignments_item_history",
            "item_id",
            "assigned_at",
        ),
        Index(
            "ix_item_storage_assignments_location_active",
            "storage_location_id",
            "is_active",
        ),
        Index(
            "uq_item_storage_assignments_active_item",
            "item_id",
            unique=True,
            postgresql_where=text("is_active = true"),
        ),
    )

    item_id: Mapped[int] = mapped_column(
        ForeignKey(
            "collection_items.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    storage_location_id: Mapped[int] = mapped_column(
        ForeignKey(
            "storage_locations.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )

    assigned_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
    )

    removed_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
    )

    moved_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    movement_reason: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    item: Mapped["CollectionItem"] = relationship(
        back_populates="storage_assignments",
    )

    storage_location: Mapped["StorageLocation"] = relationship()

    moved_by_user: Mapped["User | None"] = relationship()

    def __repr__(self) -> str:
        return (
            f"ItemStorageAssignment(id={self.id!r}, "
            f"item_id={self.item_id!r}, "
            f"storage_location_id={self.storage_location_id!r}, "
            f"is_active={self.is_active!r})"
        )
