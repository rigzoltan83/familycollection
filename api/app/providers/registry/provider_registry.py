"""
Metadata provider registry.

A registry összekapcsolja a provider kódját
a tényleges Python implementációval.
"""

from app.providers.base import MetadataProvider


class ProviderRegistry:
    """
    Metadata provider implementációk központi nyilvántartása.
    """

    def __init__(self) -> None:
        self._providers: dict[str, MetadataProvider] = {}

    def register(
        self,
        provider: MetadataProvider,
    ) -> None:
        """
        Provider regisztrálása.

        Ugyanazzal a kóddal két provider nem regisztrálható.
        """
        code = provider.code.strip().lower()

        if not code:
            raise ValueError(
                "A provider code nem lehet üres."
            )

        if code in self._providers:
            raise ValueError(
                f"Már létezik provider ezzel a kóddal: {code}"
            )

        self._providers[code] = provider

    def get(
        self,
        code: str,
    ) -> MetadataProvider:
        """
        Provider lekérése kód alapján.
        """
        normalized_code = code.strip().lower()

        try:
            return self._providers[normalized_code]
        except KeyError as error:
            raise KeyError(
                f"Ismeretlen provider: {normalized_code}"
            ) from error

    def get_optional(
        self,
        code: str,
    ) -> MetadataProvider | None:
        """
        Provider lekérése hiba nélkül.

        Ismeretlen kód esetén None értéket ad vissza.
        """
        normalized_code = code.strip().lower()

        return self._providers.get(normalized_code)

    def list_all(self) -> list[MetadataProvider]:
        """
        Az összes regisztrált provider listázása
        provider kód szerint rendezve.
        """
        return [
            self._providers[code]
            for code in sorted(self._providers)
        ]

    def contains(
        self,
        code: str,
    ) -> bool:
        """
        Ellenőrzi, hogy egy provider regisztrálva van-e.
        """
        normalized_code = code.strip().lower()

        return normalized_code in self._providers

    def clear(self) -> None:
        """
        A registry ürítése.

        Elsősorban automatikus tesztekhez használható.
        """
        self._providers.clear()


provider_registry = ProviderRegistry()
