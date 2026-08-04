"""
CategoryMetadataProvider SQLAlchemy modell.

Összekapcsolja a kategóriákat a metadata providerekkel,
és meghatározza a keresési sorrendet és működést.
"""

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    JSON,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.mixins import PublicEntityMixin


class CategoryMetadataProvider(
    PublicEntityMixin,
    Base,
):
    __tablename__ = "category_metadata_providers"

    __table_args__ = (
        UniqueConstraint(
            "category_id",
            "provider_id",
            name="uq_category_metadata_providers_category_provider",
        ),
        CheckConstraint(
            "priority >= 0",
            name="ck_category_metadata_providers_priority",
        ),
        Index(
            "ix_category_metadata_providers_category_priority",
            "category_id",
            "priority",
        ),
        Index(
            "ix_category_metadata_providers_provider_id",
            "provider_id",
        ),
    )

    category_id: Mapped[int] = mapped_column(
        ForeignKey(
            "categories.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    provider_id: Mapped[int] = mapped_column(
        ForeignKey(
            "metadata_providers.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    priority: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=100,
        server_default=text("100"),
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )

    stop_on_match: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )

    configuration: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default=text("'{}'::json"),
    )

    category: Mapped["Category"] = relationship()

    provider: Mapped["MetadataProvider"] = relationship()

    def __repr__(self) -> str:
        return (
            f"CategoryMetadataProvider(id={self.id!r}, "
            f"category_id={self.category_id!r}, "
            f"provider_id={self.provider_id!r}, "
            f"priority={self.priority!r})"
        )
