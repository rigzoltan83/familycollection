"""
Kategóriákhoz rendelhető tárhelyszabályok sémái.
"""

from pydantic import BaseModel, ConfigDict


class CategoryStorageLocationRuleRequest(
    BaseModel
):
    """
    Egy kategóriához engedélyezett tárhely.
    """

    storage_location_id: int
    include_descendants: bool = True


class CategoryStorageLocationRulesUpdateRequest(
    BaseModel
):
    """
    Egy kategória teljes tárhelyszabály-listája.

    Üres lista azt jelenti, hogy nincs
    tárhelykorlátozás.
    """

    rules: list[
        CategoryStorageLocationRuleRequest
    ]


class CategoryStorageLocationRuleResponse(
    BaseModel
):
    """
    Egy mentett kategória-tárhely szabály.
    """

    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    household_id: int
    category_id: int
    storage_location_id: int
    include_descendants: bool


class CategoryStorageLocationRulesResponse(
    BaseModel
):
    """
    Egy kategória teljes tárhelykonfigurációja.
    """

    category_id: int
    restricted: bool
    rules: list[
        CategoryStorageLocationRuleResponse
    ]
