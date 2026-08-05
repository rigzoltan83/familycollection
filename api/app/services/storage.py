"""
Hierarchikus tárhelykezelési szolgáltatások.

A modul a StorageLocation modellekből felépíthető
fa lekérdezését és később a tárhely-admin műveleteket kezeli.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import StorageLocation


@dataclass(slots=True)
class StorageTreeNode:
    id: int
    public_id: str
    household_id: int
    parent_id: int | None
    name: str
    slug: str
    location_type: str
    description: str | None
    sort_order: int
    is_active: bool
    children: list["StorageTreeNode"] = field(
        default_factory=list
    )


def list_storage_tree(
    session: Session,
    *,
    household_id: int,
    include_inactive: bool = False,
) -> list[StorageTreeNode]:
    """
    Visszaadja egy háztartás teljes tárhelyfáját.

    A gyökér- és gyermekelemek sorrendje:

    1. sort_order
    2. name
    3. id
    """
    if household_id <= 0:
        raise ValueError(
            "A household_id csak pozitív egész szám lehet."
        )

    filters = [
        StorageLocation.household_id == household_id,
    ]

    if not include_inactive:
        filters.append(
            StorageLocation.is_active.is_(True)
        )

    locations = session.scalars(
        select(StorageLocation)
        .where(*filters)
        .order_by(
            StorageLocation.sort_order.asc(),
            StorageLocation.name.asc(),
            StorageLocation.id.asc(),
        )
    ).all()

    nodes_by_id = {
        location.id: StorageTreeNode(
            id=location.id,
            public_id=location.public_id,
            household_id=location.household_id,
            parent_id=location.parent_id,
            name=location.name,
            slug=location.slug,
            location_type=location.location_type,
            description=location.description,
            sort_order=location.sort_order,
            is_active=location.is_active,
        )
        for location in locations
    }

    roots: list[StorageTreeNode] = []

    for location in locations:
        node = nodes_by_id[location.id]

        if location.parent_id is None:
            roots.append(node)
            continue

        parent_node = nodes_by_id.get(
            location.parent_id
        )

        if parent_node is None:
            roots.append(node)
            continue

        parent_node.children.append(node)

    return roots
