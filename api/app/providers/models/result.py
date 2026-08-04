"""
Egységes provider találati modell.
"""

from dataclasses import dataclass, field

from app.providers.models.identifier import MetadataIdentifier


@dataclass(slots=True)
class MetadataResult:
    """
    Minden provider ilyen objektumot ad vissza.
    """

    provider_code: str

    external_id: str | None = None

    title: str | None = None

    subtitle: str | None = None

    description: str | None = None

    identifiers: list[MetadataIdentifier] = field(
        default_factory=list
    )

    common_fields: dict[str, object] = field(
        default_factory=dict
    )

    category_fields: dict[str, object] = field(
        default_factory=dict
    )

    image_urls: list[str] = field(
        default_factory=list
    )

    source_url: str | None = None

    confidence: float = 1.0

    raw_data: dict[str, object] = field(
        default_factory=dict
    )
