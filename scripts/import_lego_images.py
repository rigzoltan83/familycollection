#!/usr/bin/env python3

import argparse
import os
import secrets
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image, ImageOps


DB_CONTAINER = "family-db"
DB_USER = "familyuser"
DB_NAME = "familycollection"

CATEGORY_ID = 3
NUMBER_FIELD_ID = 13

SOURCE_DIR = Path(
    "/opt/familycollection/lego_box_images"
)

IMAGE_ROOT = Path(
    "/opt/familycollection/data/images/items"
)

WEBP_QUALITY = 88
THUMB_MAX_SIZE = 500

CROCKFORD32 = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def die(message):
    print(f"HIBA: {message}", file=sys.stderr)
    sys.exit(1)


def generate_ulid():
    timestamp_ms = int(time.time() * 1000)
    random_bits = secrets.randbits(80)

    value = (timestamp_ms << 80) | random_bits

    chars = []

    for _ in range(26):
        chars.append(
            CROCKFORD32[value & 31]
        )
        value >>= 5

    return "".join(reversed(chars))


def sql_quote(value):
    if value is None:
        return "NULL"

    value = str(value)

    return "'" + value.replace(
        "'",
        "''"
    ) + "'"


def psql(sql, tuples_only=False):
    cmd = [
        "docker",
        "exec",
        "-i",
        DB_CONTAINER,
        "psql",
        "-v",
        "ON_ERROR_STOP=1",
        "-U",
        DB_USER,
        "-d",
        DB_NAME,
    ]

    if tuples_only:
        cmd.extend([
            "-A",
            "-t",
            "-F",
            "|",
        ])

    result = subprocess.run(
        cmd,
        input=sql,
        text=True,
        capture_output=True,
    )

    if result.returncode != 0:
        print(
            result.stdout,
            file=sys.stderr,
        )
        print(
            result.stderr,
            file=sys.stderr,
        )
        raise RuntimeError(
            "PostgreSQL hiba."
        )

    return result.stdout


def get_lego_items():
    sql = f"""
SELECT
    ci.id,
    ci.public_id,
    ci.title,
    ifv.value_text
FROM collection_items ci
JOIN item_field_values ifv
    ON ifv.item_id = ci.id
WHERE ci.category_id = {CATEGORY_ID}
  AND ci.is_active = true
  AND ifv.field_id = {NUMBER_FIELD_ID}
  AND ifv.value_text IS NOT NULL
ORDER BY ci.id;
"""

    result = psql(
        sql,
        tuples_only=True,
    )

    items = {}

    for line in result.splitlines():
        line = line.strip()

        if not line:
            continue

        parts = line.split("|", 3)

        if len(parts) != 4:
            continue

        item_id = int(parts[0])
        public_id = parts[1]
        title = parts[2]
        number = parts[3].strip()

        if number in items:
            die(
                "Duplikált LEGO Number "
                f"az adatbázisban: {number}"
            )

        items[number] = {
            "id": item_id,
            "public_id": public_id,
            "title": title,
        }

    return items


def get_existing_images():
    sql = f"""
SELECT
    ci.id,
    ii.id,
    ii.original_filename,
    ii.stored_filename,
    ii.is_primary
FROM collection_items ci
JOIN item_images ii
    ON ii.item_id = ci.id
WHERE ci.category_id = {CATEGORY_ID}
  AND ci.is_active = true
  AND ii.is_active = true;
"""

    result = psql(
        sql,
        tuples_only=True,
    )

    existing = {}

    for line in result.splitlines():
        line = line.strip()

        if not line:
            continue

        parts = line.split("|")

        if len(parts) < 5:
            continue

        item_id = int(parts[0])

        existing.setdefault(
            item_id,
            []
        ).append({
            "image_id": int(parts[1]),
            "original_filename": parts[2],
            "stored_filename": parts[3],
            "is_primary": (
                parts[4].lower() == "t"
            ),
        })

    return existing


def find_source_images():
    files = {}

    for path in sorted(
        SOURCE_DIR.glob("*.jpg")
    ):
        number = path.stem.strip()

        if number in files:
            die(
                f"Duplikált kép: {number}"
            )

        files[number] = path

    return files


def read_image_info(path):
    with Image.open(path) as img:
        img = ImageOps.exif_transpose(img)

        return (
            img.width,
            img.height,
        )


def convert_image(
    source,
    main_target,
    thumb_target,
):
    with Image.open(source) as img:
        img = ImageOps.exif_transpose(img)

        if img.mode not in (
            "RGB",
            "RGBA",
        ):
            img = img.convert("RGB")

        width = img.width
        height = img.height

        main_target.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        img.save(
            main_target,
            "WEBP",
            quality=WEBP_QUALITY,
            method=6,
        )

        thumb = img.copy()

        thumb.thumbnail(
            (
                THUMB_MAX_SIZE,
                THUMB_MAX_SIZE,
            ),
            Image.Resampling.LANCZOS,
        )

        thumb.save(
            thumb_target,
            "WEBP",
            quality=WEBP_QUALITY,
            method=6,
        )

        return (
            width,
            height,
        )


def build_db_insert(
    item_id,
    original_filename,
    stored_filename,
    image_public_id,
    file_size,
    width,
    height,
):
    return f"""
INSERT INTO item_images (
    item_id,
    original_filename,
    stored_filename,
    mime_type,
    file_size,
    width,
    height,
    sort_order,
    is_primary,
    is_active,
    public_id,
    caption
)
VALUES (
    {item_id},
    {sql_quote(original_filename)},
    {sql_quote(stored_filename)},
    'image/webp',
    {file_size},
    {width},
    {height},
    0,
    true,
    true,
    {sql_quote(image_public_id)},
    NULL
);
"""


def main():
    parser = argparse.ArgumentParser(
        description=(
            "LEGO JPG képek importálása "
            "FamilyCollection-be"
        )
    )

    parser.add_argument(
        "--commit",
        action="store_true",
        help=(
            "Tényleges import. "
            "Enélkül csak dry-run."
        ),
    )

    args = parser.parse_args()

    if not SOURCE_DIR.is_dir():
        die(
            "Nem található: "
            f"{SOURCE_DIR}"
        )

    lego_items = get_lego_items()
    source_images = find_source_images()
    existing_images = get_existing_images()

    print()
    print(
        f"LEGO rekordok:     "
        f"{len(lego_items)}"
    )
    print(
        f"JPG képek:         "
        f"{len(source_images)}"
    )
    print()

    missing_items = sorted(
        set(source_images)
        - set(lego_items)
    )

    missing_images = sorted(
        set(lego_items)
        - set(source_images)
    )

    if missing_items:
        print(
            "KÉP VAN, LEGO REKORD NINCS:"
        )

        for number in missing_items:
            print(
                f"  {number}.jpg"
            )

        print()

    if missing_images:
        print(
            "LEGO REKORD VAN, KÉP NINCS:"
        )

        for number in missing_images:
            print(
                f"  {number} | "
                f"{lego_items[number]['title']}"
            )

        print()

    import_rows = []
    skipped = []

    for number, source in sorted(
        source_images.items(),
        key=lambda x: x[0],
    ):
        item = lego_items.get(number)

        if item is None:
            continue

        if item["id"] in existing_images:
            skipped.append({
                "number": number,
                "title": item["title"],
                "reason": (
                    "már van aktív képe"
                ),
            })
            continue

        try:
            width, height = read_image_info(
                source
            )
        except Exception as exc:
            die(
                f"Hibás kép: {source}: {exc}"
            )

        import_rows.append({
            "number": number,
            "source": source,
            "item_id": item["id"],
            "title": item["title"],
            "width": width,
            "height": height,
        })

    print(
        "==================================="
    )
    print("KÉPIMPORT ÖSSZESÍTÉS")
    print(
        "==================================="
    )
    print(
        f"Importálható:       "
        f"{len(import_rows)}"
    )
    print(
        f"Kihagyott:          "
        f"{len(skipped)}"
    )
    print()

    for index, row in enumerate(
        import_rows,
        start=1,
    ):
        print(
            f"{index:3}. "
            f"{row['number']:8} | "
            f"{row['width']:4}x"
            f"{row['height']:<4} | "
            f"{row['title']}"
        )

    if skipped:
        print()
        print("KIHAGYOTT:")

        for row in skipped:
            print(
                f"  {row['number']:8} | "
                f"{row['title']} | "
                f"{row['reason']}"
            )

    if not args.commit:
        print()
        print(
            "==================================="
        )
        print("DRY-RUN KÉSZ")
        print(
            "Sem fájl, sem adatbázis "
            "nem változott."
        )
        print(
            "==================================="
        )
        return

    if missing_items:
        die(
            "Van olyan JPG, amelyhez "
            "nincs LEGO rekord. "
            "Import megszakítva."
        )

    if missing_images:
        die(
            "Van olyan LEGO rekord, "
            "amelyhez nincs JPG. "
            "Import megszakítva."
        )

    if not import_rows:
        print(
            "Nincs új importálandó kép."
        )
        return

    now = time.localtime()

    year_dir = f"{now.tm_year:04d}"
    month_dir = f"{now.tm_mon:02d}"

    relative_dir = Path(
        year_dir
    ) / month_dir

    target_dir = (
        IMAGE_ROOT
        / relative_dir
    )

    target_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    created_files = []
    sql_parts = [
        "BEGIN;",
    ]

    try:
        for index, row in enumerate(
            import_rows,
            start=1,
        ):
            stored_ulid = generate_ulid()
            image_public_id = generate_ulid()

            stored_filename = (
                relative_dir
                / f"{stored_ulid}.webp"
            )

            thumb_filename = (
                relative_dir
                / f"{stored_ulid}.thumb.webp"
            )

            main_target = (
                IMAGE_ROOT
                / stored_filename
            )

            thumb_target = (
                IMAGE_ROOT
                / thumb_filename
            )

            print(
                f"[{index}/{len(import_rows)}] "
                f"{row['number']} "
                f"{row['title']}"
            )

            width, height = convert_image(
                row["source"],
                main_target,
                thumb_target,
            )

            created_files.append(
                main_target
            )
            created_files.append(
                thumb_target
            )

            file_size = (
                main_target.stat().st_size
            )

            sql_parts.append(
                build_db_insert(
                    item_id=row["item_id"],
                    original_filename=(
                        row["source"].name
                    ),
                    stored_filename=(
                        stored_filename.as_posix()
                    ),
                    image_public_id=(
                        image_public_id
                    ),
                    file_size=file_size,
                    width=width,
                    height=height,
                )
            )

        sql_parts.append("COMMIT;")

        psql(
            "\n".join(sql_parts)
        )

    except Exception as exc:
        print()
        print(
            "HIBA történt, "
            "a létrehozott fájlok törlése..."
        )

        for path in created_files:
            try:
                path.unlink(
                    missing_ok=True
                )
            except Exception:
                pass

        die(str(exc))

    print()
    print(
        "==================================="
    )
    print("KÉPIMPORT SIKERES")
    print(
        f"Importált képek: "
        f"{len(import_rows)}"
    )
    print(
        "==================================="
    )


if __name__ == "__main__":
    main()
