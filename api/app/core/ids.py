"""
Közös azonosító-segédfüggvények.
"""

from ulid import ULID


def generate_public_id() -> str:
    """
    Új publikus ULID generálása.

    Minden külső azonosító ezt a függvényt használja.
    """
    return str(ULID())
