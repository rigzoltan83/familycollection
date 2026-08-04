"""
Egységes azonosítómodell.
"""

from dataclasses import dataclass


@dataclass(slots=True)
class MetadataIdentifier:
    """
    Egy külső vagy belső azonosító.
    """

    identifier_type: str
    value: str
