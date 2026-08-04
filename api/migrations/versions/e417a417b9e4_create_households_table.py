"""create households table

Revision ID: e417a417b9e4
Revises: 6037f217f1d4
Create Date: 2026-08-04 12:38:15.339476

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e417a417b9e4"
down_revision: Union[str, Sequence[str], None] = "6037f217f1d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Létrehozza a households táblát.

    A meglévő books és locations táblák örökölt táblák,
    ezért azokhoz ez a migráció nem nyúl.
    """
    op.create_table(
        "households",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
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
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
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
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_households_slug",
        "households",
        ["slug"],
        unique=True,
    )


def downgrade() -> None:
    """
    Csak a households táblát vonja vissza.

    A meglévő books és locations táblákhoz nem nyúl.
    """
    op.drop_index(
        "ix_households_slug",
        table_name="households",
    )

    op.drop_table("households")
