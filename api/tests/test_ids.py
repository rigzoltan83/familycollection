from app.core.ids import generate_public_id


def test_generate_public_id_returns_ulid() -> None:
    public_id = generate_public_id()

    assert isinstance(public_id, str)
    assert len(public_id) == 26


def test_generate_public_ids_are_unique() -> None:
    first = generate_public_id()
    second = generate_public_id()

    assert first != second


def test_generate_public_ids_are_sortable() -> None:
    first = generate_public_id()
    second = generate_public_id()

    assert first < second
