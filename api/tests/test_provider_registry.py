import pytest

from app.providers.base import MetadataProvider
from app.providers.registry import ProviderRegistry


class DummyProvider(MetadataProvider):
    code = "dummy"
    name = "Dummy provider"

    def supports(
        self,
        identifier_type: str,
    ) -> bool:
        return identifier_type == "test"

    def lookup_by_identifier(
        self,
        identifier: str,
    ):
        return {
            "identifier": identifier,
        }

    def search(
        self,
        query: str,
    ):
        return [
            {
                "query": query,
            }
        ]


class SecondDummyProvider(MetadataProvider):
    code = "second"
    name = "Second dummy provider"

    def supports(
        self,
        identifier_type: str,
    ) -> bool:
        return True

    def lookup_by_identifier(
        self,
        identifier: str,
    ):
        return None

    def search(
        self,
        query: str,
    ):
        return []


def test_register_and_get_provider() -> None:
    registry = ProviderRegistry()
    provider = DummyProvider()

    registry.register(provider)

    assert registry.get("dummy") is provider
    assert registry.contains("dummy") is True


def test_provider_code_is_case_insensitive() -> None:
    registry = ProviderRegistry()
    provider = DummyProvider()

    registry.register(provider)

    assert registry.get("DUMMY") is provider
    assert registry.get_optional("DuMmY") is provider
    assert registry.contains("DUMMY") is True


def test_duplicate_provider_code_is_rejected() -> None:
    registry = ProviderRegistry()

    registry.register(DummyProvider())

    with pytest.raises(
        ValueError,
        match="Már létezik provider",
    ):
        registry.register(DummyProvider())


def test_unknown_provider_raises_key_error() -> None:
    registry = ProviderRegistry()

    with pytest.raises(
        KeyError,
        match="Ismeretlen provider",
    ):
        registry.get("missing")


def test_get_optional_returns_none_for_unknown_provider() -> None:
    registry = ProviderRegistry()

    assert registry.get_optional("missing") is None


def test_list_all_is_sorted_by_provider_code() -> None:
    registry = ProviderRegistry()

    registry.register(SecondDummyProvider())
    registry.register(DummyProvider())

    assert [
        provider.code
        for provider in registry.list_all()
    ] == [
        "dummy",
        "second",
    ]


def test_clear_removes_all_providers() -> None:
    registry = ProviderRegistry()

    registry.register(DummyProvider())
    registry.register(SecondDummyProvider())

    registry.clear()

    assert registry.list_all() == []
    assert registry.contains("dummy") is False
    assert registry.contains("second") is False
