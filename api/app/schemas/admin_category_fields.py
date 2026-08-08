"""
Kategóriamezők adminisztrációs Pydantic-sémái.
"""

from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


CategoryFieldType = Literal[
    "text",
    "long_text",
    "integer",
    "decimal",
    "boolean",
    "date",
    "year",
    "url",
    "email",
    "single_select",
    "multi_select",
    "barcode",
    "image",
    "file",
]


class CategoryFieldCreateRequest(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=150,
    )

    field_key: str = Field(
        min_length=1,
        max_length=100,
    )

    field_type: CategoryFieldType

    description: str | None = None

    placeholder: str | None = Field(
        default=None,
        max_length=255,
    )

    is_required: bool = False
    is_searchable: bool = False
    is_filterable: bool = False
    is_visible_in_list: bool = False

    sort_order: int = Field(
        default=0,
        ge=0,
    )

    validation_rules: dict[str, Any] = Field(
        default_factory=dict,
    )

    default_value: dict[str, Any] = Field(
        default_factory=dict,
    )


class CategoryFieldUpdateRequest(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=150,
    )

    description: str | None = None

    placeholder: str | None = Field(
        default=None,
        max_length=255,
    )

    is_required: bool | None = None
    is_searchable: bool | None = None
    is_filterable: bool | None = None
    is_visible_in_list: bool | None = None

    sort_order: int | None = Field(
        default=None,
        ge=0,
    )

    validation_rules: dict[str, Any] | None = None
    default_value: dict[str, Any] | None = None

    is_active: bool | None = None


class CategoryFieldAdminResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
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
    is_active: bool

    sort_order: int

    validation_rules: dict[str, Any]
    default_value: dict[str, Any]
