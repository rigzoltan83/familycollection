"""
Manual metadata provider.

Nem végez külső keresést.
Mindig a kézi adatbevitel fallback providere.
"""

from app.providers.base import MetadataProvider
from app.providers.models import MetadataResult


class ManualProvider(MetadataProvider):
    code = "manual"
    name = "Manual"

    def supports(
        self,
        identifier_type: str,
    ) -> bool:
        return True

    def lookup_by_identifier(
        self,
        identifier: str,
    ) -> MetadataResult | None:
        return None

    def search(
        self,
        query: str,
    ) -> list[MetadataResult]:
        return []
