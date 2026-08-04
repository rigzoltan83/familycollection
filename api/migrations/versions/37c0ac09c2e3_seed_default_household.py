"""seed default household

Revision ID: 37c0ac09c2e3
Revises: e417a417b9e4
Create Date: 2026-08-04

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "37c0ac09c2e3"
down_revision: Union[str, Sequence[str], None] = "e417a417b9e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


DEFAULT_HOUSEHOLD_NAME = "Családi gyűjtemény"
DEFAULT_HOUSEHOLD_SLUG = "default-household"


def upgrade() -> None:
    """
    Létrehozza a jelenlegi adatállomány alapértelmezett háztartását.

    A beszúrás idempotens: ha a slug már létezik, nem hoz létre
    újabb rekordot.
    """
    connection = op.get_bind()

    connection.execute(
        sa.text(
            """
            INSERT INTO households
            (
                name,
                slug,
                is_active
            )
            VALUES
            (
                :name,
                :slug,
                true
            )
            ON CONFLICT (slug) DO NOTHING
            """
        ),
        {
            "name": DEFAULT_HOUSEHOLD_NAME,
            "slug": DEFAULT_HOUSEHOLD_SLUG,
        },
    )


def downgrade() -> None:
    """
    Kizárólag a baseline során létrehozott alapértelmezett
    háztartást törli.

    Más háztartásokhoz nem nyúl.
    """
    connection = op.get_bind()

    connection.execute(
        sa.text(
            """
            DELETE FROM households
            WHERE slug = :slug
              AND name = :name
            """
        ),
        {
            "slug": DEFAULT_HOUSEHOLD_SLUG,
            "name": DEFAULT_HOUSEHOLD_NAME,
        },
    )
