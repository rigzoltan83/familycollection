"""seed manual metadata provider

Revision ID: b4e3aa89e86e
Revises: b197a428a2c4
Create Date: 2026-08-04

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.core.ids import generate_public_id


revision: str = "b4e3aa89e86e"
down_revision: Union[str, Sequence[str], None] = "b197a428a2c4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


PROVIDER_CODE = "manual"
PLUGIN_KEY = "manual"


def upgrade() -> None:
    """
    Létrehozza a kézi adatbevitelhez használt rendszerprovidert.

    A beszúrás idempotens: meglévő code esetén nem hoz létre
    újabb rekordot.
    """
    connection = op.get_bind()

    connection.execute(
        sa.text(
            """
            INSERT INTO metadata_providers
            (
                public_id,
                code,
                name,
                description,
                provider_type,
                plugin_key,
                is_system,
                is_active,
                requires_api_key,
                supports_barcode,
                supports_text_search,
                supports_images,
                configuration_schema
            )
            VALUES
            (
                :public_id,
                :code,
                :name,
                :description,
                :provider_type,
                :plugin_key,
                true,
                true,
                false,
                false,
                false,
                false,
                CAST(:configuration_schema AS JSON)
            )
            ON CONFLICT (code) DO NOTHING
            """
        ),
        {
            "public_id": generate_public_id(),
            "code": PROVIDER_CODE,
            "name": "Manual",
            "description": (
                "Kézi adatbevitel és külső találat nélküli fallback."
            ),
            "provider_type": "manual",
            "plugin_key": PLUGIN_KEY,
            "configuration_schema": "{}",
        },
    )


def downgrade() -> None:
    """
    Kizárólag a seed során létrehozott manual providert törli.
    """
    connection = op.get_bind()

    connection.execute(
        sa.text(
            """
            DELETE FROM metadata_providers
            WHERE code = :code
              AND plugin_key = :plugin_key
              AND is_system = true
            """
        ),
        {
            "code": PROVIDER_CODE,
            "plugin_key": PLUGIN_KEY,
        },
    )
