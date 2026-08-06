from datetime import datetime
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image

import app.services.image_storage as image_storage


def make_image_bytes(
    *,
    size: tuple[int, int] = (800, 600),
    image_format: str = "JPEG",
    mode: str = "RGB",
) -> bytes:
    image = Image.new(
        mode,
        size,
        128,
    )

    buffer = BytesIO()

    image.save(
        buffer,
        format=image_format,
    )

    image.close()

    return buffer.getvalue()


def test_store_item_image_creates_webp(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        image_storage,
        "ITEM_IMAGE_ROOT",
        tmp_path,
    )

    stored = image_storage.store_item_image(
        make_image_bytes(),
        now=datetime(2026, 8, 6, 12, 30, 0),
    )

    assert stored.stored_filename.startswith(
        "2026/08/"
    )

    assert stored.stored_filename.endswith(
        ".webp"
    )

    assert stored.absolute_path.is_file()
    assert stored.mime_type == "image/webp"
    assert stored.file_size > 0
    assert stored.width == 800
    assert stored.height == 600

    with Image.open(
        stored.absolute_path
    ) as image:
        assert image.format == "WEBP"
        assert image.size == (800, 600)


def test_store_item_image_resizes_large_image(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        image_storage,
        "ITEM_IMAGE_ROOT",
        tmp_path,
    )

    monkeypatch.setattr(
        image_storage,
        "ITEM_IMAGE_MAX_DIMENSION",
        1000,
    )

    stored = image_storage.store_item_image(
        make_image_bytes(
            size=(3000, 1500),
        ),
        now=datetime(2026, 8, 6, 12, 30, 0),
    )

    assert stored.width == 1000
    assert stored.height == 500


def test_store_item_image_keeps_transparency(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        image_storage,
        "ITEM_IMAGE_ROOT",
        tmp_path,
    )

    stored = image_storage.store_item_image(
        make_image_bytes(
            size=(120, 80),
            image_format="PNG",
            mode="RGBA",
        ),
    )

    with Image.open(
        stored.absolute_path
    ) as image:
        assert image.mode == "RGBA"


def test_store_item_image_rejects_empty_content(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        image_storage,
        "ITEM_IMAGE_ROOT",
        tmp_path,
    )

    with pytest.raises(
        image_storage.ImageStorageError,
        match="üres",
    ):
        image_storage.store_item_image(
            b""
        )


def test_store_item_image_rejects_invalid_content(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        image_storage,
        "ITEM_IMAGE_ROOT",
        tmp_path,
    )

    with pytest.raises(
        image_storage.ImageStorageError,
        match="nem érvényes kép",
    ):
        image_storage.store_item_image(
            b"this is not an image"
        )


def test_store_item_image_rejects_oversized_upload(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        image_storage,
        "ITEM_IMAGE_ROOT",
        tmp_path,
    )

    monkeypatch.setattr(
        image_storage,
        "ITEM_IMAGE_MAX_UPLOAD_BYTES",
        5,
    )

    with pytest.raises(
        image_storage.ImageStorageError,
        match="túl nagy",
    ):
        image_storage.store_item_image(
            b"123456"
        )


def test_resolve_item_image_path_rejects_traversal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        image_storage,
        "ITEM_IMAGE_ROOT",
        tmp_path,
    )

    with pytest.raises(
        image_storage.ImageStorageError,
        match="Érvénytelen",
    ):
        image_storage.resolve_item_image_path(
            "../../etc/passwd"
        )


def test_delete_item_image_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        image_storage,
        "ITEM_IMAGE_ROOT",
        tmp_path,
    )

    stored = image_storage.store_item_image(
        make_image_bytes(),
    )

    assert image_storage.delete_item_image_file(
        stored.stored_filename
    )

    assert not stored.absolute_path.exists()

    assert not image_storage.delete_item_image_file(
        stored.stored_filename
    )
