"""
Kategóriamező-definíciók publikus API-sémái.

Ezek alapján a frontend dinamikusan fel tudja
építeni egy gyűjtemény adatbeviteli felületét.
"""

from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
)


class CategoryFieldOptionResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    public_id: str

    value: str
    label: str

    sort_order: int


class CategoryFieldResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    public_id: str

    category_id: int

    name: str
    field_key: str
    field_type: str

    description: str | None
    placeholder: str | None

    is_required: bool
    is_searchable: bool
    is_filterable: bool
    is_visible_in_list: bool

    sort_order: int

    validation_rules: dict[str, Any]
    default_value: dict[str, Any]

    options: list[CategoryFieldOptionResponse]
