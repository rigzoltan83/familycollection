"""seed book category and manual provider

Revision ID: 41d4cff9c0e2
Revises: 56260a831c30
Create Date: 2026-08-04

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.core.ids import generate_public_id


revision: str = "41d4cff9c0e2"
down_revision: Union[str, Sequence[str], None] = "56260a831c30"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


CATEGORY_SLUG = "book"
PROVIDER_CODE = "manual"


def upgrade() -> None:
    """
    Létrehozza a Könyv rendszerkategóriát, majd hozzárendeli
    a manual metadata providert 100-as prioritással.
    """
    connection = op.get_bind()

    connection.execute(
        sa.text(
            """
            INSERT INTO categories
            (
                household_id,
                name,
                slug,
                description,
                icon,
                is_system,
                is_active,
                supports_barcode,
                metadata_lookup_type,
                sort_order
            )
            VALUES
            (
                NULL,
                :name,
                :slug,
                :description,
                :icon,
                true,
                true,
                true,
                :metadata_lookup_type,
                :sort_order
            )
            ON CONFLICT DO NOTHING
            """
        ),
        {
            "name": "Könyv",
            "slug": CATEGORY_SLUG,
            "description": "Könyvek és kiadványok nyilvántartása.",
            "icon": "book",
            "metadata_lookup_type": "manual",
            "sort_order": 10,
        },
    )

    connection.execute(
        sa.text(
            """
            INSERT INTO category_metadata_providers
            (
                public_id,
                category_id,
                provider_id,
                priority,
                is_active,
                stop_on_match,
                configuration
            )
            SELECT
                :public_id,
                category.id,
                provider.id,
                100,
                true,
                true,
                CAST(:configuration AS JSON)
            FROM categories AS category
            CROSS JOIN metadata_providers AS provider
            WHERE category.slug = :category_slug
              AND category.is_system = true
              AND provider.code = :provider_code
              AND provider.is_system = true
            ON CONFLICT (category_id, provider_id) DO NOTHING
            """
        ),
        {
            "public_id": generate_public_id(),
            "category_slug": CATEGORY_SLUG,
            "provider_code": PROVIDER_CODE,
            "configuration": "{}",
        },
    )


def downgrade() -> None:
    """
    Először törli a Könyv–manual kapcsolatot, majd kizárólag
    a seed során létrehozott Könyv rendszerkategóriát.
    """
    connection = op.get_bind()

    connection.execute(
        sa.text(
            """
            DELETE FROM category_metadata_providers
            WHERE category_id IN
            (
                SELECT id
                FROM categories
                WHERE slug = :category_slug
                  AND is_system = true
            )
              AND provider_id IN
            (
                SELECT id
                FROM metadata_providers
                WHERE code = :provider_code
                  AND is_system = true
            )
            """
        ),
        {
            "category_slug": CATEGORY_SLUG,
            "provider_code": PROVIDER_CODE,
        },
    )

    connection.execute(
        sa.text(
            """
            DELETE FROM categories
            WHERE slug = :category_slug
              AND name = :category_name
              AND is_system = true
              AND household_id IS NULL
            """
        ),
        {
            "category_slug": CATEGORY_SLUG,
            "category_name": "Könyv",
        },
    )
