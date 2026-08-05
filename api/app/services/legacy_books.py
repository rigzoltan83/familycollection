"""
Régi books rekordok migrációját előkészítő segédfüggvények.

Ez a modul egyelőre csak:

- a forrásadatokat normalizálja;
- azonosítótípust állapít meg;
- megjelenési évet értelmez;
- figyelmeztetéseket gyűjt.

Adatbázisba még nem ír.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class LegacyBookSource:
    legacy_book_id: int
    isbn: str | None
    title: str | None
    author: str | None
    publisher: str | None
    publish_year: str | None
    location_id: int | None
    borrowed_to: str | None
    created: datetime | None
    updated: datetime | None


@dataclass(slots=True)
class NormalizedLegacyIdentifier:
    identifier_type: str
    identifier_value: str


@dataclass(slots=True)
class PreparedLegacyBook:
    legacy_book_id: int
    title: str
    author: str | None
    publisher: str | None
    publish_year: int | None
    identifier: NormalizedLegacyIdentifier | None
    legacy_isbn: str | None
    legacy_location_id: int | None
    legacy_borrowed_to: str | None
    created_at: datetime | None
    updated_at: datetime | None
    warnings: list[str] = field(default_factory=list)


def _clean_optional_text(
    value: str | None,
) -> str | None:
    if value is None:
        return None

    cleaned = value.strip()

    return cleaned or None


def normalize_legacy_identifier(
    value: str | None,
) -> NormalizedLegacyIdentifier | None:
    """
    A régi isbn mezőből ItemIdentifier-kompatibilis értéket készít.

    Szabályok:

    - X vagy üres: nincs azonosító;
    - ISSN kezdetű érték: issn;
    - MSZ kezdetű érték: custom;
    - 10 karakteres normalizált érték: isbn10;
    - 13 karakteres normalizált érték: isbn13;
    - minden más nem üres érték: custom.
    """
    cleaned = _clean_optional_text(value)

    if cleaned is None:
        return None

    if cleaned.upper() == "X":
        return None

    upper_value = cleaned.upper()

    if upper_value.startswith("ISSN"):
        issn_value = re.sub(
            r"^ISSN\s*",
            "",
            cleaned,
            flags=re.IGNORECASE,
        ).strip()

        return NormalizedLegacyIdentifier(
            identifier_type="issn",
            identifier_value=issn_value,
        )

    if upper_value.startswith("MSZ"):
        normalized_custom = re.sub(
            r"\s+",
            " ",
            cleaned,
        )

        return NormalizedLegacyIdentifier(
            identifier_type="custom",
            identifier_value=normalized_custom,
        )

    compact_value = re.sub(
        r"[^0-9Xx]",
        "",
        cleaned,
    ).upper()

    if len(compact_value) == 10:
        return NormalizedLegacyIdentifier(
            identifier_type="isbn10",
            identifier_value=compact_value,
        )

    if len(compact_value) == 13:
        return NormalizedLegacyIdentifier(
            identifier_type="isbn13",
            identifier_value=compact_value,
        )

    return NormalizedLegacyIdentifier(
        identifier_type="custom",
        identifier_value=cleaned,
    )


def normalize_publish_year(
    value: str | None,
) -> tuple[int | None, str | None]:
    """
    Megjelenési év normalizálása.

    Visszatérési érték:

    - normalizált év vagy None;
    - opcionális figyelmeztetés.
    """
    cleaned = _clean_optional_text(value)

    if cleaned is None:
        return None, None

    if not re.fullmatch(r"[0-9]{4}", cleaned):
        return (
            None,
            f"Érvénytelen megjelenési év: {cleaned}",
        )

    year = int(cleaned)

    if year < 1000 or year > 9999:
        return (
            None,
            f"Tartományon kívüli megjelenési év: {cleaned}",
        )

    return year, None


def prepare_legacy_book(
    source: LegacyBookSource,
) -> PreparedLegacyBook:
    """
    Egy régi books rekord normalizálása migrációhoz.
    """
    warnings: list[str] = []

    title = _clean_optional_text(source.title)

    if title is None:
        raise ValueError(
            f"A régi könyv címe üres: books.id={source.legacy_book_id}"
        )

    author = _clean_optional_text(source.author)
    publisher = _clean_optional_text(source.publisher)

    publish_year, year_warning = normalize_publish_year(
        source.publish_year
    )

    if year_warning is not None:
        warnings.append(year_warning)

    identifier = normalize_legacy_identifier(
        source.isbn
    )

    cleaned_legacy_isbn = _clean_optional_text(
        source.isbn
    )

    if (
        cleaned_legacy_isbn is not None
        and cleaned_legacy_isbn.upper() == "X"
    ):
        warnings.append(
            "Az X helykitöltő ISBN nem került azonosítóként migrálásra."
        )

    return PreparedLegacyBook(
        legacy_book_id=source.legacy_book_id,
        title=title,
        author=author,
        publisher=publisher,
        publish_year=publish_year,
        identifier=identifier,
        legacy_isbn=cleaned_legacy_isbn,
        legacy_location_id=source.location_id,
        legacy_borrowed_to=_clean_optional_text(
            source.borrowed_to
        ),
        created_at=source.created,
        updated_at=source.updated,
        warnings=warnings,
    )
