"""
MetadataProvider SQLAlchemy modell.

A tábla a rendszerben elérhető metadata provider plugineket írja le.
A tényleges Python implementációt a plugin_key kapcsolja össze
a ProviderRegistry bejegyzésével.
"""

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Index,
    JSON,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.mixins import PublicEntityMixin


class MetadataProvider(
    PublicEntityMixin,
    Base,
):
    __tablename__ = "metadata_providers"

    __table_args__ = (
        CheckConstraint(
            """
            provider_type IN (
                'remote_api',
                'web_lookup',
                'local_database',
                'manual',
                'import'
            )
            """,
            name="ck_metadata_providers_type",
        ),
        Index(
            "uq_metadata_providers_code",
            "code",
            unique=True,
        ),
        Index(
            "uq_metadata_providers_plugin_key",
            "plugin_key",
            unique=True,
        ),
    )

    code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    provider_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    plugin_key: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    is_system: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )

    requires_api_key: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )

    supports_barcode: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )

    supports_text_search: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )

    supports_images: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )

    configuration_schema: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default=text("'{}'::json"),
    )

    def __repr__(self) -> str:
        return (
            f"MetadataProvider(id={self.id!r}, "
            f"code={self.code!r}, "
            f"plugin_key={self.plugin_key!r})"
        )
