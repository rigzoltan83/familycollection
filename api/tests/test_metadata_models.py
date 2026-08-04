from app.providers.models import (
    MetadataIdentifier,
    MetadataResult,
)


def test_metadata_identifier_stores_type_and_value() -> None:
    identifier = MetadataIdentifier(
        identifier_type="isbn13",
        value="9789631234567",
    )

    assert identifier.identifier_type == "isbn13"
    assert identifier.value == "9789631234567"


def test_metadata_result_has_safe_empty_collections() -> None:
    result = MetadataResult(
        provider_code="manual",
    )

    assert result.identifiers == []
    assert result.common_fields == {}
    assert result.category_fields == {}
    assert result.image_urls == []
    assert result.raw_data == {}


def test_metadata_result_default_confidence_is_one() -> None:
    result = MetadataResult(
        provider_code="manual",
    )

    assert result.confidence == 1.0


def test_metadata_result_instances_do_not_share_collections() -> None:
    first = MetadataResult(
        provider_code="first",
    )

    second = MetadataResult(
        provider_code="second",
    )

    first.image_urls.append(
        "https://example.com/image.jpg"
    )

    first.common_fields["title"] = "Első"

    assert second.image_urls == []
    assert second.common_fields == {}


def test_metadata_result_accepts_category_specific_fields() -> None:
    result = MetadataResult(
        provider_code="geology",
        title="Hegyikristály",
        category_fields={
            "mineral_type": "kvarc",
            "weight_grams": 245,
            "mohs_hardness": 7,
        },
    )

    assert result.title == "Hegyikristály"
    assert result.category_fields["mineral_type"] == "kvarc"
    assert result.category_fields["weight_grams"] == 245
    assert result.category_fields["mohs_hardness"] == 7


def test_metadata_result_accepts_multiple_identifiers() -> None:
    result = MetadataResult(
        provider_code="book_provider",
        identifiers=[
            MetadataIdentifier(
                identifier_type="isbn13",
                value="9789631234567",
            ),
            MetadataIdentifier(
                identifier_type="isbn10",
                value="9631234567",
            ),
        ],
    )

    assert len(result.identifiers) == 2
    assert result.identifiers[0].identifier_type == "isbn13"
    assert result.identifiers[1].identifier_type == "isbn10"
