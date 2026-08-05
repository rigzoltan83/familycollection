"""
Storage API Pydantic sémák.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class StorageLocationCreateRequest(BaseModel):
    """
    Új tárhely létrehozási kérelme.
    """

    household_id: int = Field(
        gt=0,
    )

    parent_public_id: str | None = None

    name: str = Field(
        min_length=1,
        max_length=150,
    )

    slug: str | None = Field(
        default=None,
        max_length=150,
    )

    location_type: str = Field(
        min_length=1,
        max_length=30,
    )

    description: str | None = Field(
        default=None,
        max_length=500,
    )

    sort_order: int = Field(
        default=0,
        ge=0,
    )

    is_active: bool = True


class StorageLocationResponse(BaseModel):
    """
    Egyetlen létrehozott vagy lekért tárhely válasza.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    public_id: str
    household_id: int
    parent_public_id: str | None

    name: str
    slug: str
    location_type: str
    description: str | None
    sort_order: int
    is_active: bool


class StorageTreeNodeResponse(BaseModel):
    """
    Egy hierarchikus tárhelyfa-elemet ír le.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    public_id: str
    household_id: int
    parent_public_id: str | None

    name: str
    slug: str
    location_type: str
    description: str | None
    sort_order: int
    is_active: bool

    children: list["StorageTreeNodeResponse"]


class StorageTreeResponse(BaseModel):
    """
    Egy háztartás teljes tárhelyfájának válasza.
    """

    household_id: int
    include_inactive: bool
    locations: list[StorageTreeNodeResponse]
