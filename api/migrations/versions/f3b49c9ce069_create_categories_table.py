"""create categories table

Revision ID: f3b49c9ce069
Revises: 1217cb995788
Create Date: 2026-08-04 14:09:34.711990

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f3b49c9ce069"
down_revision: Union[str, Sequence[str], None] = "1217cb995788"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Létrehozza a rendszer- és háztartási kategóriákat tároló táblát.
    """
    op.create_table(
        "categories",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "household_id",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "name",
            sa.String(length=150),
            nullable=False,
        ),
        sa.Column(
            "slug",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "description",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "icon",
            sa.String(length=100),
            nullable=True,
        ),
        sa.Column(
            "is_system",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "supports_barcode",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "metadata_lookup_type",
            sa.String(length=50),
            server_default=sa.text("'manual'"),
            nullable=False,
        ),
        sa.Column(
            "sort_order",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            """
            (
                is_system = true
                AND household_id IS NULL
            )
            OR
            (
                is_system = false
                AND household_id IS NOT NULL
            )
            """,
            name="ck_categories_system_household",
        ),
        sa.ForeignKeyConstraint(
            ["household_id"],
            ["households.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_categories_household_id",
        "categories",
        ["household_id"],
        unique=False,
    )

    op.create_index(
        "uq_categories_household_slug",
        "categories",
        ["household_id", "slug"],
        unique=True,
        postgresql_where=sa.text(
            "household_id IS NOT NULL"
        ),
    )

    op.create_index(
        "uq_categories_system_slug",
        "categories",
        ["slug"],
        unique=True,
        postgresql_where=sa.text(
            "is_system = true"
        ),
    )


def downgrade() -> None:
    """
    Visszavonáskor csak a categories táblát távolítja el.
    """
    op.drop_index(
        "uq_categories_system_slug",
        table_name="categories",
    )

    op.drop_index(
        "uq_categories_household_slug",
        table_name="categories",
    )

    op.drop_index(
        "ix_categories_household_id",
        table_name="categories",
    )

    op.drop_table("categories")
