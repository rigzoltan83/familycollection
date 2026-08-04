"""
Metadata provider alapinterfész.

Minden metadata provider ezt az interfészt valósítja meg.
"""

from abc import ABC, abstractmethod


class MetadataProvider(ABC):
    """
    Minden provider közös absztrakt alaposztálya.
    """

    code: str
    name: str

    @abstractmethod
    def supports(
        self,
        identifier_type: str,
    ) -> bool:
        """
        Megmondja, hogy támogatja-e az adott
        azonosítótípust.
        """
        raise NotImplementedError

    @abstractmethod
    def lookup_by_identifier(
        self,
        identifier: str,
    ):
        """
        Keresés egyedi azonosító alapján.
        """
        raise NotImplementedError

    @abstractmethod
    def search(
        self,
        query: str,
    ):
        """
        Szöveges keresés.
        """
        raise NotImplementedError
