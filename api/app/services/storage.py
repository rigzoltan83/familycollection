"""
Hierarchikus tárhelykezelési szolgáltatások.

A modul a StorageLocation modellekből felépíthető
fa lekérdezését és később a tárhely-admin műveleteket kezeli.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Household, StorageLocation


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


@dataclass(slots=True)
class StorageLocationCreateInput:
    household_id: int
    name: str
    location_type: str
    parent_public_id: str | None = None
    slug: str | None = None
    description: str | None = None
    sort_order: int = 0
    is_active: bool = True


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


def _normalize_storage_slug(
    value: str,
) -> str:
    """
    Egyszerű, URL-barát slugot készít.

    A magyar ékezeteket alap latin karakterekre alakítja,
    a szóközöket és egyéb elválasztókat kötőjelre cseréli.
    """
    replacements = str.maketrans({
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ö": "o",
        "ő": "o",
        "ú": "u",
        "ü": "u",
        "ű": "u",
        "Á": "a",
        "É": "e",
        "Í": "i",
        "Ó": "o",
        "Ö": "o",
        "Ő": "o",
        "Ú": "u",
        "Ü": "u",
        "Ű": "u",
    })

    normalized = value.translate(replacements).strip().lower()

    characters: list[str] = []
    previous_was_separator = False

    for character in normalized:
        if character.isalnum():
            characters.append(character)
            previous_was_separator = False
            continue

        if not previous_was_separator:
            characters.append("-")
            previous_was_separator = True

    return "".join(characters).strip("-")


def create_storage_location(
    session: Session,
    *,
    data: StorageLocationCreateInput,
) -> StorageLocation:
    """
    Új hierarchikus tárhelyet hoz létre.

    Ellenőrzi:

    - a háztartást;
    - a típust;
    - a nevet és slugot;
    - a sorrendet;
    - az opcionális szülőelemet;
    - a testvérek közötti slug-egyediséget.

    A hívó kezeli a commitot vagy rollbacket.
    """
    if data.household_id <= 0:
        raise ValueError(
            "A household_id csak pozitív egész szám lehet."
        )

    household = session.get(
        Household,
        data.household_id,
    )

    if household is None or not household.is_active:
        raise ValueError(
            "A megadott aktív háztartás nem található."
        )

    cleaned_name = data.name.strip()

    if not cleaned_name:
        raise ValueError(
            "A tárhely neve nem lehet üres."
        )

    allowed_location_types = {
        "room",
        "shelf",
        "cabinet",
        "drawer",
        "box",
        "slot",
        "area",
        "other",
    }

    cleaned_location_type = (
        data.location_type.strip().lower()
    )

    if cleaned_location_type not in allowed_location_types:
        raise ValueError(
            "Nem támogatott tárhelytípus."
        )

    if data.sort_order < 0:
        raise ValueError(
            "A sort_order nem lehet negatív."
        )

    parent: StorageLocation | None = None

    if data.parent_public_id is not None:
        cleaned_parent_public_id = (
            data.parent_public_id.strip()
        )

        if not cleaned_parent_public_id:
            raise ValueError(
                "A parent_public_id nem lehet üres."
            )

        parent = session.scalar(
            select(StorageLocation).where(
                StorageLocation.public_id
                == cleaned_parent_public_id
            )
        )

        if parent is None:
            raise ValueError(
                "A megadott szülő tárhely nem található."
            )

        if parent.household_id != data.household_id:
            raise ValueError(
                "A szülő tárhely nem ehhez a háztartáshoz tartozik."
            )

    cleaned_slug = (
        _normalize_storage_slug(data.slug)
        if data.slug is not None
        else _normalize_storage_slug(cleaned_name)
    )

    if not cleaned_slug:
        raise ValueError(
            "A tárhely slugja nem lehet üres."
        )

    duplicate_count = session.scalar(
        select(
            func.count(StorageLocation.id)
        ).where(
            StorageLocation.household_id
            == data.household_id,
            StorageLocation.parent_id
            == (
                parent.id
                if parent is not None
                else None
            ),
            StorageLocation.slug
            == cleaned_slug,
        )
    )

    if duplicate_count:
        raise ValueError(
            "Ugyanilyen sluggal már létezik tárhely ezen a szinten."
        )

    cleaned_description = (
        data.description.strip()
        if (
            data.description is not None
            and data.description.strip()
        )
        else None
    )

    location = StorageLocation(
        household_id=data.household_id,
        parent_id=(
            parent.id
            if parent is not None
            else None
        ),
        name=cleaned_name,
        slug=cleaned_slug,
        location_type=cleaned_location_type,
        description=cleaned_description,
        sort_order=data.sort_order,
        is_active=data.is_active,
    )

    session.add(location)
    session.flush()

    return location
