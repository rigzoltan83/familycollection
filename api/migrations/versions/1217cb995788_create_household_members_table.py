"""create household members table

Revision ID: 1217cb995788
Revises: 64203cf0e3d4
Create Date: 2026-08-04 13:06:21.192770

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "1217cb995788"
down_revision: Union[str, Sequence[str], None] = "64203cf0e3d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Létrehozza a felhasználók és háztartások közötti tagságot.
    """
    op.create_table(
        "household_members",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "household_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "role",
            sa.String(length=20),
            server_default=sa.text("'viewer'"),
            nullable=False,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "joined_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
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
            "role IN ('owner', 'admin', 'editor', 'viewer')",
            name="ck_household_members_role",
        ),
        sa.ForeignKeyConstraint(
            ["household_id"],
            ["households.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "household_id",
            "user_id",
            name="uq_household_members_household_user",
        ),
    )

    op.create_index(
        "ix_household_members_household_id",
        "household_members",
        ["household_id"],
        unique=False,
    )

    op.create_index(
        "ix_household_members_user_id",
        "household_members",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    """
    Visszavonáskor csak a household_members táblát távolítja el.
    """
    op.drop_index(
        "ix_household_members_user_id",
        table_name="household_members",
    )

    op.drop_index(
        "ix_household_members_household_id",
        table_name="household_members",
    )

    op.drop_table("household_members")
