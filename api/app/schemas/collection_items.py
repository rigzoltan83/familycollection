"""
CollectionItem API-sémák.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ItemIdentifierCreate(BaseModel):
    identifier_type: str = Field(
        min_length=1,
        max_length=50,
    )
    identifier_value: str = Field(
        min_length=1,
        max_length=255,
    )
    provider_code: str | None = Field(
        default=None,
        max_length=100,
    )
    is_primary: bool = False


class CollectionItemCreateRequest(BaseModel):
    household_id: int = Field(gt=0)
    category_id: int = Field(gt=0)

    title: str = Field(
        min_length=1,
        max_length=300,
    )
    subtitle: str | None = Field(
        default=None,
        max_length=300,
    )
    notes: str | None = None
    status: str = "active"
    created_by_user_id: int | None = Field(
        default=None,
        gt=0,
    )

    identifiers: list[ItemIdentifierCreate] = Field(
        default_factory=list,
    )

    field_values: dict[
        str,
        str
        | int
        | float
        | Decimal
        | bool
        | date
        | list[Any]
        | dict[str, Any]
        | None,
    ] = Field(
        default_factory=dict,
    )


class ItemIdentifierResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    public_id: str
    identifier_type: str
    identifier_value: str
    provider_code: str | None
    is_primary: bool
    is_active: bool


class ItemFieldValueResponse(BaseModel):
    field_key: str
    field_type: str

    value_text: str | None = None
    value_integer: int | None = None
    value_decimal: Decimal | None = None
    value_boolean: bool | None = None
    value_date: date | None = None
    value_json: Any | None = None


class ItemImageUpdateRequest(BaseModel):
    caption: str | None = Field(
        default=None,
        max_length=200,
    )

    sort_order: int | None = Field(
        default=None,
        ge=0,
    )

    is_primary: bool | None = None


class ItemImageResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    public_id: str
    item_id: int

    original_filename: str | None
    caption: str | None

    mime_type: str
    file_size: int

    width: int | None
    height: int | None

    sort_order: int
    is_primary: bool
    is_active: bool

    created_at: datetime
    updated_at: datetime

    content_url: str


class CollectionItemResponse(BaseModel):
    public_id: str
    household_id: int
    category_id: int

    title: str
    subtitle: str | None
    notes: str | None
    status: str
    is_active: bool

    created_by_user_id: int | None
    updated_by_user_id: int | None

    created_at: datetime
    updated_at: datetime

    identifiers: list[ItemIdentifierResponse]
    field_values: list[ItemFieldValueResponse]


class CollectionItemListEntry(BaseModel):
    public_id: str
    household_id: int
    category_id: int
    title: str
    subtitle: str | None
    status: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    primary_image_thumbnail_url: str | None = None

    field_values: list[
        ItemFieldValueResponse
    ] = Field(
        default_factory=list
    )


class CollectionItemListResponse(BaseModel):
    items: list[CollectionItemListEntry]
    total: int
    limit: int
    offset: int

class CollectionItemUpdateRequest(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=300,
    )

    subtitle: str | None = Field(
        default=None,
        max_length=300,
    )

    notes: str | None = None

    status: str | None = None

    is_active: bool | None = None

    updated_by_user_id: int | None = Field(
        default=None,
        gt=0,
    )

    identifiers: list[ItemIdentifierCreate] | None = None

    field_values: dict[
        str,
        str
        | int
        | float
        | Decimal
        | bool
        | date
        | list[Any]
        | dict[str, Any]
        | None,
    ] | None = None
