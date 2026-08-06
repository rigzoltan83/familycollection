"""
Általános CollectionItem-képtároló service.

A service:
- ellenőrzi a feltöltési méretet;
- valódi képként megnyitja a tartalmat;
- EXIF alapján helyes irányba forgatja;
- szükség esetén lekicsinyíti;
- WebP formátumban menti;
- egyedi, dátum szerint könyvtárazott fájlnevet készít.

Nem függ FastAPI-tól vagy SQLAlchemy-től.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import BinaryIO

from PIL import Image, ImageOps, UnidentifiedImageError
from ulid import ULID

from settings import (
    ITEM_IMAGE_MAX_DIMENSION,
    ITEM_IMAGE_MAX_UPLOAD_BYTES,
    ITEM_IMAGE_ROOT,
    ITEM_IMAGE_WEBP_QUALITY,
)


ALLOWED_INPUT_FORMATS = {
    "JPEG",
    "PNG",
    "WEBP",
}


@dataclass(frozen=True)
class StoredImage:
    """
    A sikeresen eltárolt kép metaadatai.
    """

    stored_filename: str
    absolute_path: Path
    mime_type: str
    file_size: int
    width: int
    height: int


class ImageStorageError(ValueError):
    """
    Felhasználói vagy képfeldolgozási hiba.
    """


def _read_upload_bytes(
    source: bytes | BinaryIO,
) -> bytes:
    if isinstance(source, bytes):
        content = source
    else:
        try:
            source.seek(0)
        except (AttributeError, OSError):
            pass

        content = source.read()

    if not isinstance(content, bytes):
        raise ImageStorageError(
            "A feltöltött tartalom nem bájtadat."
        )

    if not content:
        raise ImageStorageError(
            "A feltöltött képfájl üres."
        )

    if len(content) > ITEM_IMAGE_MAX_UPLOAD_BYTES:
        max_megabytes = (
            ITEM_IMAGE_MAX_UPLOAD_BYTES
            // 1024
            // 1024
        )

        raise ImageStorageError(
            "A feltöltött kép túl nagy. "
            f"A megengedett legnagyobb méret "
            f"{max_megabytes} MB."
        )

    return content


def _open_and_prepare_image(
    content: bytes,
) -> Image.Image:
    try:
        with Image.open(BytesIO(content)) as source_image:
            source_image.verify()

        with Image.open(BytesIO(content)) as source_image:
            input_format = (
                source_image.format or ""
            ).upper()

            if input_format not in ALLOWED_INPUT_FORMATS:
                raise ImageStorageError(
                    "Nem támogatott képformátum. "
                    "Engedélyezett: JPEG, PNG és WebP."
                )

            image = ImageOps.exif_transpose(
                source_image
            )

            image.load()

            if image.mode in {
                "RGBA",
                "LA",
            }:
                prepared = image.convert("RGBA")

            elif (
                image.mode == "P"
                and "transparency" in image.info
            ):
                prepared = image.convert("RGBA")

            else:
                prepared = image.convert("RGB")

    except ImageStorageError:
        raise

    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
    ) as error:
        raise ImageStorageError(
            "A feltöltött fájl nem érvényes kép."
        ) from error

    prepared.thumbnail(
        (
            ITEM_IMAGE_MAX_DIMENSION,
            ITEM_IMAGE_MAX_DIMENSION,
        ),
        Image.Resampling.LANCZOS,
    )

    if prepared.width <= 0 or prepared.height <= 0:
        raise ImageStorageError(
            "A kép mérete érvénytelen."
        )

    return prepared


def _build_relative_path(
    *,
    now: datetime,
) -> Path:
    image_id = str(ULID())

    return Path(
        f"{now.year:04d}",
        f"{now.month:02d}",
        f"{image_id}.webp",
    )


def store_item_image(
    source: bytes | BinaryIO,
    *,
    now: datetime | None = None,
) -> StoredImage:
    """
    Kép validálása, konvertálása és eltárolása.

    A visszaadott stored_filename az ITEM_IMAGE_ROOT
    könyvtárhoz viszonyított POSIX útvonal.
    """
    content = _read_upload_bytes(source)

    image = _open_and_prepare_image(
        content
    )

    current_time = now or datetime.now()

    relative_path = _build_relative_path(
        now=current_time,
    )

    absolute_path = (
        ITEM_IMAGE_ROOT / relative_path
    )

    absolute_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = absolute_path.with_suffix(
        ".tmp"
    )

    width = image.width
    height = image.height

    try:
        image.save(
            temporary_path,
            format="WEBP",
            quality=ITEM_IMAGE_WEBP_QUALITY,
            method=6,
        )

        temporary_path.replace(
            absolute_path
        )

    except OSError as error:
        temporary_path.unlink(
            missing_ok=True
        )

        raise ImageStorageError(
            "A kép nem menthető el."
        ) from error

    finally:
        image.close()

    file_size = absolute_path.stat().st_size

    return StoredImage(
        stored_filename=relative_path.as_posix(),
        absolute_path=absolute_path,
        mime_type="image/webp",
        file_size=file_size,
        width=width,
        height=height,
    )


def resolve_item_image_path(
    stored_filename: str,
) -> Path:
    """
    Biztonságosan feloldja a relatív tárolt fájlnevet.

    Megakadályozza a képkönyvtáron kívüli elérést.
    """
    clean_name = str(
        stored_filename or ""
    ).strip()

    if not clean_name:
        raise ImageStorageError(
            "A tárolt képfájlnév üres."
        )

    root = ITEM_IMAGE_ROOT.resolve()

    candidate = (
        root / clean_name
    ).resolve()

    try:
        candidate.relative_to(root)
    except ValueError as error:
        raise ImageStorageError(
            "Érvénytelen tárolt képfájlnév."
        ) from error

    return candidate


def delete_item_image_file(
    stored_filename: str,
) -> bool:
    """
    Törli a fájlt.

    True: a fájl létezett és törlődött.
    False: a fájl már nem létezett.
    """
    path = resolve_item_image_path(
        stored_filename
    )

    if not path.exists():
        return False

    if not path.is_file():
        raise ImageStorageError(
            "A képfájl útvonala nem fájl."
        )

    path.unlink()

    return True
