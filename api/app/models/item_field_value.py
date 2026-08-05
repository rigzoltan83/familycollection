"""
ItemFieldValue SQLAlchemy modell.

A CollectionItem dinamikus kategóriamezőinek tényleges értékeit tárolja.
Egy rekordban mindig csak a mezőtípusnak megfelelő értékoszlop használható.
"""

from datetime import date
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.mixins import PublicEntityMixin


class ItemFieldValue(
    PublicEntityMixin,
    Base,
):
    __tablename__ = "item_field_values"

    __table_args__ = (
        UniqueConstraint(
            "item_id",
            "field_id",
            name="uq_item_field_values_item_field",
        ),
        CheckConstraint(
            """
            (
                CASE WHEN value_text IS NOT NULL THEN 1 ELSE 0 END
                +
                CASE WHEN value_integer IS NOT NULL THEN 1 ELSE 0 END
                +
                CASE WHEN value_decimal IS NOT NULL THEN 1 ELSE 0 END
                +
                CASE WHEN value_boolean IS NOT NULL THEN 1 ELSE 0 END
                +
                CASE WHEN value_date IS NOT NULL THEN 1 ELSE 0 END
                +
                CASE WHEN value_json IS NOT NULL THEN 1 ELSE 0 END
            ) <= 1
            """,
            name="ck_item_field_values_single_value",
        ),
        Index(
            "ix_item_field_values_item_id",
            "item_id",
        ),
        Index(
            "ix_item_field_values_field_id",
            "field_id",
        ),
        Index(
            "ix_item_field_values_field_text",
            "field_id",
            "value_text",
        ),
        Index(
            "ix_item_field_values_field_integer",
            "field_id",
            "value_integer",
        ),
        Index(
            "ix_item_field_values_field_decimal",
            "field_id",
            "value_decimal",
        ),
        Index(
            "ix_item_field_values_field_date",
            "field_id",
            "value_date",
        ),
    )

    item_id: Mapped[int] = mapped_column(
        ForeignKey(
            "collection_items.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    field_id: Mapped[int] = mapped_column(
        ForeignKey(
            "category_fields.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    value_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    value_integer: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    value_decimal: Mapped[Decimal | None] = mapped_column(
        Numeric(
            precision=20,
            scale=6,
        ),
        nullable=True,
    )

    value_boolean: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    value_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    value_json: Mapped[dict | list | None] = mapped_column(
        JSON,
        nullable=True,
    )

    item: Mapped["CollectionItem"] = relationship()

    field: Mapped["CategoryField"] = relationship()

    def __repr__(self) -> str:
        return (
            f"ItemFieldValue(id={self.id!r}, "
            f"item_id={self.item_id!r}, "
            f"field_id={self.field_id!r})"
        )
