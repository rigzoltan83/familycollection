"""
CategoryField SQLAlchemy modell.

A kategóriákhoz tartozó dinamikus meződefiníciókat tárolja.
Például:

- Könyv: szerző, kiadó, megjelenési év
- Bélyeg: ország, névérték, kiadási év
- Kőzet: ásványtípus, tömeg, Mohs-keménység
"""

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.mixins import PublicEntityMixin


class CategoryField(
    PublicEntityMixin,
    Base,
):
    __tablename__ = "category_fields"

    __table_args__ = (
        UniqueConstraint(
            "category_id",
            "field_key",
            name="uq_category_fields_category_key",
        ),
        CheckConstraint(
            """
            field_type IN (
                'text',
                'long_text',
                'integer',
                'decimal',
                'boolean',
                'date',
                'year',
                'url',
                'email',
                'single_select',
                'multi_select',
                'barcode',
                'image',
                'file'
            )
            """,
            name="ck_category_fields_type",
        ),
        CheckConstraint(
            "sort_order >= 0",
            name="ck_category_fields_sort_order",
        ),
        Index(
            "ix_category_fields_category_sort_order",
            "category_id",
            "sort_order",
        ),
        Index(
            "ix_category_fields_category_id",
            "category_id",
        ),
    )

    category_id: Mapped[int] = mapped_column(
        ForeignKey(
            "categories.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    field_key: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    field_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    placeholder: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    is_required: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )

    is_searchable: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )

    is_filterable: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )

    is_visible_in_list: Mapped[bool] = mapped_column(
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

    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )

    validation_rules: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default=text("'{}'::json"),
    )

    default_value: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default=text("'{}'::json"),
    )

    category: Mapped["Category"] = relationship()

    def __repr__(self) -> str:
        return (
            f"CategoryField(id={self.id!r}, "
            f"category_id={self.category_id!r}, "
            f"field_key={self.field_key!r}, "
            f"field_type={self.field_type!r})"
        )
