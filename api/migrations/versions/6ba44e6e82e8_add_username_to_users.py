"""add username to users

Revision ID: 6ba44e6e82e8
Revises: 21f779d6e45f
Create Date: 2026-08-07 16:56:24.176947
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.

revision: str = "6ba44e6e82e8"
down_revision: Union[str, Sequence[str], None] = (
    "21f779d6e45f"
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Username mező hozzáadása.

    A már létező felhasználók username értékét
    az e-mail cím @ előtti részéből képezzük.

    Ha ugyanaz az alap username több usernél is
    előfordulna, a további rekordok user ID suffixet
    kapnak.
    """
    op.add_column(
        "users",
        sa.Column(
            "username",
            sa.String(length=100),
            nullable=True,
        ),
    )

    op.execute(
        """
        WITH username_candidates AS (
            SELECT
                id,
                lower(
                    regexp_replace(
                        split_part(email, '@', 1),
                        '[^a-zA-Z0-9._-]+',
                        '-',
                        'g'
                    )
                ) AS base_username,
                row_number() OVER (
                    PARTITION BY lower(
                        regexp_replace(
                            split_part(email, '@', 1),
                            '[^a-zA-Z0-9._-]+',
                            '-',
                            'g'
                        )
                    )
                    ORDER BY id
                ) AS duplicate_number
            FROM users
        )
        UPDATE users
        SET username =
            CASE
                WHEN username_candidates.base_username = ''
                THEN 'user-' || users.id::text

                WHEN username_candidates.duplicate_number = 1
                THEN left(
                    username_candidates.base_username,
                    100
                )

                ELSE left(
                    username_candidates.base_username,
                    100
                    - length(users.id::text)
                    - 1
                )
                || '-'
                || users.id::text
            END
        FROM username_candidates
        WHERE users.id = username_candidates.id
        """
    )

    op.alter_column(
        "users",
        "username",
        existing_type=sa.String(length=100),
        nullable=False,
    )

    op.create_index(
        "ix_users_username",
        "users",
        [sa.literal_column("lower(username)")],
        unique=True,
    )


def downgrade() -> None:
    """
    Username támogatás visszavonása.
    """
    op.drop_index(
        "ix_users_username",
        table_name="users",
    )

    op.drop_column(
        "users",
        "username",
    )
