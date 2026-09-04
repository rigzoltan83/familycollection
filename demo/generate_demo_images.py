#!/opt/familycollection/api/venv/bin/python

from __future__ import annotations

import os
import sys
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from sqlalchemy import select, text

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "api"

if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.core.database import SessionLocal
from app.models import CollectionItem, ItemImage
from app.services.collection_items import (
    ItemImageCreateInput,
    create_item_image,
)
from app.services.image_storage import store_item_image


EXPECTED_DATABASE = "familycollection_demo"

COVERS = {
    "The Clockmaker's Map": (
        "BOOK",
        "Elena Hart",
        (35, 45, 70),
        (196, 156, 74),
    ),
    "Gardens Beyond the Moon": (
        "BOOK",
        "Mira Vale",
        (37, 73, 58),
        (174, 205, 146),
    ),
    "Practical Astronomy at Home": (
        "BOOK",
        "Daniel Mercer",
        (24, 45, 78),
        (116, 173, 220),
    ),
    "Rails & Rivers": (
        "BOARD GAME",
        "Build the network",
        (91, 52, 36),
        (224, 163, 86),
    ),
    "Kingdom of Glass": (
        "BOARD GAME",
        "Strategy & alliances",
        (54, 43, 78),
        (184, 161, 218),
    ),
    "Signal Station": (
        "BOARD GAME",
        "Deep-space cooperation",
        (30, 66, 74),
        (100, 203, 193),
    ),
    "Orbital Colony": (
        "VIDEO GAME",
        "Beyond Earth",
        (31, 43, 68),
        (105, 153, 215),
    ),
    "Deep Signal": (
        "VIDEO GAME",
        "Unknown transmission",
        (24, 57, 67),
        (81, 199, 210),
    ),
    "Northern Circuit": (
        "VIDEO GAME",
        "Frozen racing",
        (47, 61, 78),
        (157, 197, 227),
    ),
}


def guard_database(session) -> None:
    configured = os.environ.get("DB_NAME", "").strip()

    if configured != EXPECTED_DATABASE:
        raise RuntimeError(
            "REFUSING TO RUN: DB_NAME must be "
            f"{EXPECTED_DATABASE!r}, got {configured!r}."
        )

    actual = session.scalar(
        text("SELECT current_database()")
    )

    if actual != EXPECTED_DATABASE:
        raise RuntimeError(
            "REFUSING TO RUN: connected database is "
            f"{actual!r}, expected {EXPECTED_DATABASE!r}."
        )

    print(f"SAFE DATABASE: {actual}")


def font(size: int):
    candidates = (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    )

    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)

    return ImageFont.load_default()


def regular_font(size: int):
    candidates = (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    )

    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)

    return ImageFont.load_default()


def wrap_text(draw, value, selected_font, max_width):
    words = value.split()
    lines = []
    current = ""

    for word in words:
        candidate = (
            f"{current} {word}".strip()
        )

        box = draw.textbbox(
            (0, 0),
            candidate,
            font=selected_font,
        )

        if box[2] - box[0] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)

    return lines


def create_cover(
    title: str,
    kind: str,
    subtitle: str,
    background,
    accent,
) -> bytes:
    width = 900
    height = 1200

    image = Image.new(
        "RGB",
        (width, height),
        background,
    )

    draw = ImageDraw.Draw(image)

    draw.rectangle(
        (0, 0, width, 22),
        fill=accent,
    )

    draw.rectangle(
        (70, 120, 830, 1040),
        outline=accent,
        width=5,
    )

    draw.ellipse(
        (570, 180, 760, 370),
        outline=accent,
        width=8,
    )

    draw.line(
        (665, 210, 665, 275),
        fill=accent,
        width=7,
    )

    draw.line(
        (665, 275, 720, 310),
        fill=accent,
        width=7,
    )

    kind_font = font(34)
    title_font = font(72)
    subtitle_font = regular_font(34)
    small_font = regular_font(25)

    draw.text(
        (105, 155),
        kind,
        font=kind_font,
        fill=accent,
    )

    title_lines = wrap_text(
        draw,
        title,
        title_font,
        670,
    )

    y = 450

    for line in title_lines:
        draw.text(
            (105, y),
            line,
            font=title_font,
            fill=(245, 245, 242),
        )
        y += 90

    draw.line(
        (105, y + 25, 420, y + 25),
        fill=accent,
        width=5,
    )

    draw.text(
        (105, y + 70),
        subtitle,
        font=subtitle_font,
        fill=(220, 220, 215),
    )

    draw.text(
        (105, 970),
        "FAMILYCOLLECTION",
        font=small_font,
        fill=accent,
    )

    draw.text(
        (105, 1010),
        "SYNTHETIC DEMO ITEM",
        font=small_font,
        fill=(190, 190, 185),
    )

    output = BytesIO()

    image.save(
        output,
        format="PNG",
        optimize=True,
    )

    image.close()

    return output.getvalue()


def main() -> None:
    session = SessionLocal()

    try:
        guard_database(session)

        existing = session.scalar(
            select(ItemImage.id)
            .where(ItemImage.is_active.is_(True))
            .limit(1)
        )

        if existing is not None:
            raise RuntimeError(
                "Demo images already exist. "
                "Refusing to create duplicates."
            )

        items = session.scalars(
            select(CollectionItem)
            .where(
                CollectionItem.title.in_(
                    tuple(COVERS)
                )
            )
        ).all()

        by_title = {
            item.title: item
            for item in items
        }

        missing = (
            set(COVERS)
            - set(by_title)
        )

        if missing:
            raise RuntimeError(
                "Demo items missing: "
                + ", ".join(sorted(missing))
            )

        for title, config in COVERS.items():
            kind, subtitle, background, accent = config

            png = create_cover(
                title,
                kind,
                subtitle,
                background,
                accent,
            )

            stored = store_item_image(
                png
            )

            create_item_image(
                session,
                by_title[title],
                ItemImageCreateInput(
                    stored_filename=stored.stored_filename,
                    mime_type=stored.mime_type,
                    file_size=stored.file_size,
                    width=stored.width,
                    height=stored.height,
                    original_filename=(
                        title.lower()
                        .replace(" ", "-")
                        .replace("'", "")
                        + ".png"
                    ),
                    caption=(
                        "Synthetic demo artwork for "
                        + title
                    ),
                    sort_order=0,
                    is_primary=True,
                ),
            )

            print(
                f"CREATE: {title} -> "
                f"{stored.stored_filename}"
            )

        session.commit()

        print()
        print(
            f"Created {len(COVERS)} "
            "synthetic demo images."
        )

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()


if __name__ == "__main__":
    main()
