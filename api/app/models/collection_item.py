"""
CollectionItem SQLAlchemy modell.

Minden nyilvántartott tárgy közös adatait tárolja,
függetlenül attól, hogy könyv, bélyeg, bankjegy,
kőzet vagy bármilyen más kategóriába tartozik.
"""

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.mixins import PublicEntityMixin


class CollectionItem(
    PublicEntityMixin,
    Base,
):
    __tablename__ = "collection_items"

    __table_args__ = (
        CheckConstraint(
            """
            status IN (
                'active',
                'loaned',
                'archived',
                'missing',
                'disposed'
            )
            """,
            name="ck_collection_items_status",
        ),
        Index(
            "ix_collection_items_household_category",
            "household_id",
            "category_id",
        ),
        Index(
            "ix_collection_items_household_status",
            "household_id",
            "status",
        ),
        Index(
            "ix_collection_items_category_id",
            "category_id",
        ),
        Index(
            "ix_collection_items_created_by_user_id",
            "created_by_user_id",
        ),
        Index(
            "ix_collection_items_updated_by_user_id",
            "updated_by_user_id",
        ),
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
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
    )

    subtitle: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="active",
        server_default=text("'active'"),
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )

    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    updated_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    household: Mapped["Household"] = relationship()

    category: Mapped["Category"] = relationship()

    created_by_user: Mapped["User | None"] = relationship(
        foreign_keys=[created_by_user_id],
    )

    updated_by_user: Mapped["User | None"] = relationship(
        foreign_keys=[updated_by_user_id],
    )

    def __repr__(self) -> str:
        return (
            f"CollectionItem(id={self.id!r}, "
            f"public_id={self.public_id!r}, "
            f"title={self.title!r}, "
            f"category_id={self.category_id!r})"
        )
