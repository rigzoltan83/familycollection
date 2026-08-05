"""
ItemIdentifier SQLAlchemy modell.

Egy CollectionItem több külső vagy belső azonosítóval is
rendelkezhet, például ISBN-10, ISBN-13, EAN, UPC,
provider-azonosító vagy saját cikkszám.
"""

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.mixins import PublicEntityMixin


class ItemIdentifier(
    PublicEntityMixin,
    Base,
):
    __tablename__ = "item_identifiers"

    __table_args__ = (
        UniqueConstraint(
            "item_id",
            "identifier_type",
            "identifier_value",
            name="uq_item_identifiers_item_type_value",
        ),
        CheckConstraint(
            """
            identifier_type IN (
                'isbn10',
                'isbn13',
                'ean8',
                'ean13',
                'upc',
                'issn',
                'catalog_number',
                'provider_external_id',
                'custom',
                'qr',
                'rfid',
                'nfc'
            )
            """,
            name="ck_item_identifiers_type",
        ),
        Index(
            "ix_item_identifiers_item_id",
            "item_id",
        ),
        Index(
            "ix_item_identifiers_type_value",
            "identifier_type",
            "identifier_value",
        ),
        Index(
            "ix_item_identifiers_provider_code",
            "provider_code",
        ),
    )

    item_id: Mapped[int] = mapped_column(
        ForeignKey(
            "collection_items.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    identifier_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    identifier_value: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    provider_code: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
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

    item: Mapped["CollectionItem"] = relationship()

    def __repr__(self) -> str:
        return (
            f"ItemIdentifier(id={self.id!r}, "
            f"item_id={self.item_id!r}, "
            f"identifier_type={self.identifier_type!r}, "
            f"identifier_value={self.identifier_value!r})"
        )
