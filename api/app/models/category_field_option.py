"""
CategoryFieldOption SQLAlchemy modell.

A single_select és multi_select típusú dinamikus mezők
választható értékeit tárolja.
"""

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.mixins import PublicEntityMixin


class CategoryFieldOption(
    PublicEntityMixin,
    Base,
):
    __tablename__ = "category_field_options"

    __table_args__ = (
        UniqueConstraint(
            "field_id",
            "value",
            name="uq_category_field_options_field_value",
        ),
        CheckConstraint(
            "sort_order >= 0",
            name="ck_category_field_options_sort_order",
        ),
        Index(
            "ix_category_field_options_field_sort_order",
            "field_id",
            "sort_order",
        ),
        Index(
            "ix_category_field_options_field_id",
            "field_id",
        ),
    )

    field_id: Mapped[int] = mapped_column(
        ForeignKey(
            "category_fields.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    value: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    label: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
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

    field: Mapped["CategoryField"] = relationship()

    def __repr__(self) -> str:
        return (
            f"CategoryFieldOption(id={self.id!r}, "
            f"field_id={self.field_id!r}, "
            f"value={self.value!r}, "
            f"label={self.label!r})"
        )
