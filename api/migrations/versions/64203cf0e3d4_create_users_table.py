"""create users table

Revision ID: 64203cf0e3d4
Revises: 37c0ac09c2e3
Create Date: 2026-08-04 12:56:50.615364

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "64203cf0e3d4"
down_revision: Union[str, Sequence[str], None] = "37c0ac09c2e3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Létrehozza a platformfelhasználókat tároló users táblát.
    """
    op.create_table(
        "users",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "email",
            sa.String(length=320),
            nullable=False,
        ),
        sa.Column(
            "password_hash",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "display_name",
            sa.String(length=150),
            nullable=False,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "is_platform_admin",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "email_verified",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "last_login_at",
            sa.DateTime(),
            nullable=True,
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
        "ix_users_email",
        "users",
        [sa.text("lower(email)")],
        unique=True,
    )


def downgrade() -> None:
    """
    Visszavonáskor csak a users táblát távolítja el.
    """
    op.drop_index(
        "ix_users_email",
        table_name="users",
    )

    op.drop_table("users")
