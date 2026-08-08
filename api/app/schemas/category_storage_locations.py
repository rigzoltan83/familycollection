"""
Kategóriákhoz rendelhető tárhelyszabályok sémái.
"""

from pydantic import BaseModel


class CategoryStorageLocationRuleRequest(
    BaseModel
):
    """
    Egy kategóriához engedélyezett tárhely.
    """

    storage_location_public_id: str
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

    storage_location_public_id: str
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


class CategoryAllowedStorageResponse(
    BaseModel
):
    """
    Egy kategóriában ténylegesen használható
    tárhelyek feloldott listája.
    """

    category_id: int
    restricted: bool
    storage_public_ids: list[str]
