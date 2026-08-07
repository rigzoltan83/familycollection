"""
Háztartási kategória-adminisztráció Pydantic-sémái.

A rendszerkategóriák globálisak.
A saját kategóriák egy konkrét háztartáshoz tartoznak.
"""

from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class HouseholdCategoryCreateRequest(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=150,
    )

    description: str | None = Field(
        default=None,
        max_length=2000,
    )

    icon: str | None = Field(
        default=None,
        max_length=100,
    )

    supports_barcode: bool = False

    sort_order: int = Field(
        default=0,
        ge=0,
    )


class HouseholdCategoryUpdateRequest(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=150,
    )

    description: str | None = Field(
        default=None,
        max_length=2000,
    )

    icon: str | None = Field(
        default=None,
        max_length=100,
    )

    supports_barcode: bool | None = None

    sort_order: int | None = Field(
        default=None,
        ge=0,
    )

    is_active: bool | None = None


class HouseholdCategoryResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    household_id: int | None

    name: str
    slug: str

    description: str | None
    icon: str | None

    is_system: bool
    is_active: bool

    supports_barcode: bool
    metadata_lookup_type: str

    sort_order: int

    created_at: datetime
    updated_at: datetime
