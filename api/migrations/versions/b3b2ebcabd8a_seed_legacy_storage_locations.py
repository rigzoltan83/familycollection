"""seed legacy storage locations

Revision ID: b3b2ebcabd8a
Revises: 63f891d85ff1
Create Date: 2026-08-05

"""

from __future__ import annotations

import re
import unicodedata
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.core.ids import generate_public_id


revision: str = "b3b2ebcabd8a"
down_revision: Union[str, Sequence[str], None] = "63f891d85ff1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SEED_MARKER = "[legacy-locations-seed:b3b2ebcabd8a]"

SPECIAL_AREA_NAMES = {
    "Polcról levéve",
    "Kölcsönadva",
}


def _slugify(value: str) -> str:
    """
    Ékezetmentes, URL-barát slug készítése.
    """
    normalized = unicodedata.normalize(
        "NFKD",
        value.strip(),
    )

    ascii_value = "".join(
        character
        for character in normalized
        if not unicodedata.combining(character)
    )

    slug = re.sub(
        r"[^a-zA-Z0-9]+",
        "-",
        ascii_value,
    ).strip("-").lower()

    return slug or "location"


def _get_default_household_id(
    connection: sa.Connection,
) -> int:
    household_id = connection.scalar(
        sa.text(
            """
            SELECT id
            FROM households
            WHERE is_active = true
            ORDER BY id
            LIMIT 1
            """
        )
    )

    if household_id is None:
        raise RuntimeError(
            "Nem található aktív háztartás a régi "
            "tárolóhelyek migrálásához."
        )

    return int(household_id)


def _find_location_id(
    connection: sa.Connection,
    *,
    household_id: int,
    parent_id: int | None,
    slug: str,
) -> int | None:
    location_id = connection.scalar(
        sa.text(
            """
            SELECT id
            FROM storage_locations
            WHERE household_id = :household_id
              AND (
                    (
                        parent_id IS NULL
                        AND :parent_id IS NULL
                    )
                    OR parent_id = :parent_id
                  )
              AND slug = :slug
            ORDER BY id
            LIMIT 1
            """
        ),
        {
            "household_id": household_id,
            "parent_id": parent_id,
            "slug": slug,
        },
    )

    if location_id is None:
        return None

    return int(location_id)


def _ensure_location(
    connection: sa.Connection,
    *,
    household_id: int,
    parent_id: int | None,
    name: str,
    slug: str,
    location_type: str,
    sort_order: int,
    legacy_description: str,
) -> int:
    existing_id = _find_location_id(
        connection,
        household_id=household_id,
        parent_id=parent_id,
        slug=slug,
    )

    if existing_id is not None:
        return existing_id

    location_id = connection.scalar(
        sa.text(
            """
            INSERT INTO storage_locations
            (
                public_id,
                household_id,
                parent_id,
                name,
                slug,
                location_type,
                description,
                sort_order,
                is_active
            )
            VALUES
            (
                :public_id,
                :household_id,
                :parent_id,
                :name,
                :slug,
                :location_type,
                :description,
                :sort_order,
                true
            )
            RETURNING id
            """
        ),
        {
            "public_id": generate_public_id(),
            "household_id": household_id,
            "parent_id": parent_id,
            "name": name,
            "slug": slug,
            "location_type": location_type,
            "description": (
                f"{SEED_MARKER} {legacy_description}"
            ),
            "sort_order": sort_order,
        },
    )

    if location_id is None:
        raise RuntimeError(
            f"A tárolóhely nem hozható létre: {name}"
        )

    return int(location_id)


def upgrade() -> None:
    """
    A régi locations tábla adataiból létrehozza a hierarchikus
    tárolóhelyeket:

    helyiség -> polc/szekrény -> hely
    """
    connection = op.get_bind()

    household_id = _get_default_household_id(
        connection
    )

    legacy_locations = connection.execute(
        sa.text(
            """
            SELECT
                id,
                room,
                shelf,
                slot
            FROM locations
            ORDER BY
                room,
                shelf,
                slot,
                id
            """
        )
    ).mappings().all()

    for legacy_location in legacy_locations:
        legacy_id = int(legacy_location["id"])
        room_name = str(legacy_location["room"]).strip()
        shelf_name = str(legacy_location["shelf"]).strip()
        slot_number = int(legacy_location["slot"])

        room_slug = _slugify(room_name)

        room_type = (
            "area"
            if room_name in SPECIAL_AREA_NAMES
            else "room"
        )

        room_id = _ensure_location(
            connection,
            household_id=household_id,
            parent_id=None,
            name=room_name,
            slug=room_slug,
            location_type=room_type,
            sort_order=legacy_id * 10,
            legacy_description=(
                f"Régi helyiség: {room_name}"
            ),
        )

        shelf_slug = _slugify(shelf_name)

        shelf_id = _ensure_location(
            connection,
            household_id=household_id,
            parent_id=room_id,
            name=shelf_name,
            slug=shelf_slug,
            location_type="shelf",
            sort_order=legacy_id * 10,
            legacy_description=(
                f"Régi polc/szekrény: "
                f"{room_name} / {shelf_name}"
            ),
        )

        slot_name = f"{slot_number}. hely"
        slot_slug = f"slot-{slot_number}"

        _ensure_location(
            connection,
            household_id=household_id,
            parent_id=shelf_id,
            name=slot_name,
            slug=slot_slug,
            location_type="slot",
            sort_order=slot_number * 10,
            legacy_description=(
                f"Régi location_id={legacy_id}; "
                f"útvonal={room_name} / "
                f"{shelf_name} / {slot_number}"
            ),
        )


def downgrade() -> None:
    """
    Kizárólag a migráció által létrehozott legacy tárolóhelyeket
    törli.

    A törlés alulról felfelé történik.
    """
    connection = op.get_bind()

    connection.execute(
        sa.text(
            """
            WITH RECURSIVE seeded_locations AS
            (
                SELECT
                    id,
                    parent_id,
                    1 AS depth
                FROM storage_locations
                WHERE description LIKE :marker_pattern

                UNION ALL

                SELECT
                    child.id,
                    child.parent_id,
                    seeded.depth + 1
                FROM storage_locations AS child
                JOIN seeded_locations AS seeded
                    ON child.parent_id = seeded.id
            )
            DELETE FROM storage_locations
            WHERE id IN
            (
                SELECT id
                FROM seeded_locations
            )
            """
        ),
        {
            "marker_pattern": f"{SEED_MARKER}%",
        },
    )
