"""
Beépített metadata providerek regisztrálása.
"""

from app.providers.manual import ManualProvider
from app.providers.registry import provider_registry


def register_builtin_providers() -> None:
    """
    Regisztrálja a platform beépített provider implementációit.

    Többszöri meghívás esetén sem hoz létre duplikációt.
    """
    if not provider_registry.contains("manual"):
        provider_registry.register(
            ManualProvider()
        )
