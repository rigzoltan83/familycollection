"""seed book category fields

Revision ID: c414f2afdc64
Revises: 070a2816179e
Create Date: 2026-08-05

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import json

from app.core.ids import generate_public_id


revision: str = "c414f2afdc64"
down_revision: Union[str, Sequence[str], None] = "070a2816179e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


CATEGORY_SLUG = "book"


BOOK_FIELDS = [
    {
        "field_key": "author",
        "name": "Szerző",
        "field_type": "text",
        "description": "A könyv szerzője vagy szerzői.",
        "placeholder": "Például: Stephen King",
        "is_required": False,
        "is_searchable": True,
        "is_filterable": False,
        "is_visible_in_list": True,
        "sort_order": 10,
        "validation_rules": {},
        "default_value": {},
    },
    {
        "field_key": "publisher",
        "name": "Kiadó",
        "field_type": "text",
        "description": "A könyvet megjelentető kiadó.",
        "placeholder": "Például: Európa Könyvkiadó",
        "is_required": False,
        "is_searchable": True,
        "is_filterable": True,
        "is_visible_in_list": False,
        "sort_order": 20,
        "validation_rules": {},
        "default_value": {},
    },
    {
        "field_key": "publish_year",
        "name": "Megjelenési év",
        "field_type": "year",
        "description": "A kiadás megjelenési éve.",
        "placeholder": "Például: 2024",
        "is_required": False,
        "is_searchable": False,
        "is_filterable": True,
        "is_visible_in_list": True,
        "sort_order": 30,
        "validation_rules": {
            "minimum": 1000,
            "maximum": 9999,
        },
        "default_value": {},
    },
    {
        "field_key": "isbn",
        "name": "ISBN",
        "field_type": "barcode",
        "description": "A könyv ISBN-10 vagy ISBN-13 azonosítója.",
        "placeholder": "Például: 9789631234567",
        "is_required": False,
        "is_searchable": True,
        "is_filterable": False,
        "is_visible_in_list": True,
        "sort_order": 40,
        "validation_rules": {
            "accepted_identifier_types": [
                "isbn10",
                "isbn13",
            ],
        },
        "default_value": {},
    },
    {
        "field_key": "page_count",
        "name": "Oldalszám",
        "field_type": "integer",
        "description": "A könyv oldalszáma.",
        "placeholder": "Például: 384",
        "is_required": False,
        "is_searchable": False,
        "is_filterable": True,
        "is_visible_in_list": False,
        "sort_order": 50,
        "validation_rules": {
            "minimum": 1,
        },
        "default_value": {},
    },
]


def upgrade() -> None:
    """
    Létrehozza a Könyv rendszerkategória alapmezőit.
    """
    connection = op.get_bind()

    for field_definition in BOOK_FIELDS:
        connection.execute(
            sa.text(
                """
                INSERT INTO category_fields
                (
                    public_id,
                    category_id,
                    name,
                    field_key,
                    field_type,
                    description,
                    placeholder,
                    is_required,
                    is_searchable,
                    is_filterable,
                    is_visible_in_list,
                    is_active,
                    sort_order,
                    validation_rules,
                    default_value
                )
                SELECT
                    :public_id,
                    category.id,
                    :name,
                    :field_key,
                    :field_type,
                    :description,
                    :placeholder,
                    :is_required,
                    :is_searchable,
                    :is_filterable,
                    :is_visible_in_list,
                    true,
                    :sort_order,
                    CAST(:validation_rules AS JSON),
                    CAST(:default_value AS JSON)
                FROM categories AS category
                WHERE category.slug = :category_slug
                  AND category.is_system = true
                ON CONFLICT (category_id, field_key) DO NOTHING
                """
            ),
            {
                "public_id": generate_public_id(),
                "category_slug": CATEGORY_SLUG,
                "name": field_definition["name"],
                "field_key": field_definition["field_key"],
                "field_type": field_definition["field_type"],
                "description": field_definition["description"],
                "placeholder": field_definition["placeholder"],
                "is_required": field_definition["is_required"],
                "is_searchable": field_definition["is_searchable"],
                "is_filterable": field_definition["is_filterable"],
                "is_visible_in_list": field_definition[
                    "is_visible_in_list"
                ],
                "sort_order": field_definition["sort_order"],
                "validation_rules": json.dumps(
                    field_definition["validation_rules"]
                ),
                "default_value": json.dumps(
                    field_definition["default_value"]
                ),
            },
        )


def downgrade() -> None:
    """
    Kizárólag a Könyv rendszerkategória seedelt alapmezőit törli.
    """
    connection = op.get_bind()

    connection.execute(
        sa.text(
            """
            DELETE FROM category_fields
            WHERE category_id IN
            (
                SELECT id
                FROM categories
                WHERE slug = :category_slug
                  AND is_system = true
            )
              AND field_key IN
            (
                'author',
                'publisher',
                'publish_year',
                'isbn',
                'page_count'
            )
            """
        ),
        {
            "category_slug": CATEGORY_SLUG,
        },
    )
