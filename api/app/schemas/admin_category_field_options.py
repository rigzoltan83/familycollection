"""
Kategóriamező-opciók adminisztrációs Pydantic-sémái.
"""

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class CategoryFieldOptionCreateRequest(BaseModel):
    value: str = Field(
        min_length=1,
        max_length=100,
    )

    label: str = Field(
        min_length=1,
        max_length=150,
    )

    sort_order: int = Field(
        default=0,
        ge=0,
    )


class CategoryFieldOptionUpdateRequest(BaseModel):
    value: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    label: str | None = Field(
        default=None,
        min_length=1,
        max_length=150,
    )

    sort_order: int | None = Field(
        default=None,
        ge=0,
    )

    is_active: bool | None = None


class CategoryFieldOptionAdminResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    public_id: str

    field_id: int

    value: str
    label: str

    sort_order: int
    is_active: bool
