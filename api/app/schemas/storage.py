"""
Storage API Pydantic sémák.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


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
