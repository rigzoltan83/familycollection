"""
ItemImage SQLAlchemy modell.

A CollectionItem rekordokhoz tartozó képek metaadatait tárolja.
A tényleges képfájl nem az adatbázisban, hanem a fájlrendszerben van.
"""

from sqlalchemy import (
    BigInteger,
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


class ItemImage(
    PublicEntityMixin,
    Base,
):
    __tablename__ = "item_images"

    __table_args__ = (
        CheckConstraint(
            "file_size >= 0",
            name="ck_item_images_file_size_nonnegative",
        ),
        CheckConstraint(
            "width IS NULL OR width > 0",
            name="ck_item_images_width_positive",
        ),
        CheckConstraint(
            "height IS NULL OR height > 0",
            name="ck_item_images_height_positive",
        ),
        CheckConstraint(
            "sort_order >= 0",
            name="ck_item_images_sort_order_nonnegative",
        ),
        Index(
            "ix_item_images_item_id",
            "item_id",
        ),
        Index(
            "ix_item_images_item_active",
            "item_id",
            "is_active",
        ),
        Index(
            "ix_item_images_item_primary",
            "item_id",
            "is_primary",
        ),
        Index(
            "ix_item_images_stored_filename",
            "stored_filename",
            unique=True,
        ),
    )

    item_id: Mapped[int] = mapped_column(
        ForeignKey(
            "collection_items.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    original_filename: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    caption: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    stored_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    mime_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    file_size: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    width: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    height: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )

    is_primary: Mapped[bool] = mapped_column(
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

    item: Mapped["CollectionItem"] = relationship(
        back_populates="images",
    )

    def __repr__(self) -> str:
        return (
            f"ItemImage(id={self.id!r}, "
            f"public_id={self.public_id!r}, "
            f"item_id={self.item_id!r}, "
            f"stored_filename={self.stored_filename!r})"
        )
