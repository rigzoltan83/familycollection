from datetime import datetime

import pytest

from app.services import (
    LegacyBookSource,
    normalize_legacy_identifier,
    normalize_publish_year,
    prepare_legacy_book,
)


def test_normalize_isbn13() -> None:
    identifier = normalize_legacy_identifier(
        "978-963-369-450-3"
    )

    assert identifier is not None
    assert identifier.identifier_type == "isbn13"
    assert identifier.identifier_value == "9789633694503"


def test_normalize_isbn10() -> None:
    identifier = normalize_legacy_identifier(
        "963 11 5174 3"
    )

    assert identifier is not None
    assert identifier.identifier_type == "isbn10"
    assert identifier.identifier_value == "9631151743"


def test_normalize_issn() -> None:
    identifier = normalize_legacy_identifier(
        "ISSN 3103-4152"
    )

    assert identifier is not None
    assert identifier.identifier_type == "issn"
    assert identifier.identifier_value == "3103-4152"


def test_normalize_msz_as_custom() -> None:
    identifier = normalize_legacy_identifier(
        "MSZ 5601-59"
    )

    assert identifier is not None
    assert identifier.identifier_type == "custom"
    assert identifier.identifier_value == "MSZ 5601-59"


def test_placeholder_x_does_not_create_identifier() -> None:
    assert normalize_legacy_identifier("X") is None
    assert normalize_legacy_identifier(" x ") is None


def test_normalize_valid_publish_year() -> None:
    year, warning = normalize_publish_year(" 2007 ")

    assert year == 2007
    assert warning is None


def test_prepare_legacy_book() -> None:
    created = datetime(2026, 7, 14, 8, 53, 42)
    updated = datetime(2026, 7, 14, 8, 54, 22)

    prepared = prepare_legacy_book(
        LegacyBookSource(
            legacy_book_id=6,
            isbn="9789633694503",
            title=" A három testőr Afrikában ",
            author=" Jenő Rejtő ",
            publisher=" Alexandra K. ",
            publish_year="2007",
            location_id=5,
            borrowed_to="",
            created=created,
            updated=updated,
        )
    )

    assert prepared.legacy_book_id == 6
    assert prepared.title == "A három testőr Afrikában"
    assert prepared.author == "Jenő Rejtő"
    assert prepared.publisher == "Alexandra K."
    assert prepared.publish_year == 2007
    assert prepared.legacy_location_id == 5
    assert prepared.legacy_borrowed_to is None
    assert prepared.created_at == created
    assert prepared.updated_at == updated
    assert prepared.warnings == []

    assert prepared.identifier is not None
    assert prepared.identifier.identifier_type == "isbn13"
    assert prepared.identifier.identifier_value == "9789633694503"


def test_prepare_placeholder_x_adds_warning() -> None:
    prepared = prepare_legacy_book(
        LegacyBookSource(
            legacy_book_id=265,
            isbn="X",
            title="Grimm mesék",
            author=None,
            publisher=None,
            publish_year=None,
            location_id=1,
            borrowed_to=None,
            created=None,
            updated=None,
        )
    )

    assert prepared.identifier is None
    assert len(prepared.warnings) == 1
    assert "helykitöltő ISBN" in prepared.warnings[0]


def test_prepare_rejects_empty_title() -> None:
    with pytest.raises(
        ValueError,
        match="A régi könyv címe üres",
    ):
        prepare_legacy_book(
            LegacyBookSource(
                legacy_book_id=999,
                isbn="9789630000000",
                title="   ",
                author=None,
                publisher=None,
                publish_year=None,
                location_id=None,
                borrowed_to=None,
                created=None,
                updated=None,
            )
        )
