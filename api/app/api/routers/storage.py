"""
StorageLocation HTTP-végpontok.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.schemas import (
    StorageLocationCreateRequest,
    StorageLocationResponse,
    StorageTreeNodeResponse,
    StorageTreeResponse,
)
from app.services import (
    StorageLocationCreateInput,
    StorageTreeNode,
    create_storage_location,
    list_storage_tree,
)


router = APIRouter(
    prefix="/storage",
    tags=["storage"],
)


def _build_tree_node_response(
    node: StorageTreeNode,
    *,
    public_ids_by_id: dict[int, str],
) -> StorageTreeNodeResponse:
    parent_public_id = (
        public_ids_by_id.get(node.parent_id)
        if node.parent_id is not None
        else None
    )

    return StorageTreeNodeResponse(
        public_id=node.public_id,
        household_id=node.household_id,
        parent_public_id=parent_public_id,
        name=node.name,
        slug=node.slug,
        location_type=node.location_type,
        description=node.description,
        sort_order=node.sort_order,
        is_active=node.is_active,
        children=[
            _build_tree_node_response(
                child,
                public_ids_by_id=public_ids_by_id,
            )
            for child in node.children
        ],
    )


def _collect_public_ids(
    nodes: list[StorageTreeNode],
) -> dict[int, str]:
    public_ids_by_id: dict[int, str] = {}

    def walk(node: StorageTreeNode) -> None:
        public_ids_by_id[node.id] = node.public_id

        for child in node.children:
            walk(child)

    for node in nodes:
        walk(node)

    return public_ids_by_id


def _build_location_response(
    location,
    *,
    parent_public_id: str | None,
) -> StorageLocationResponse:
    return StorageLocationResponse(
        public_id=location.public_id,
        household_id=location.household_id,
        parent_public_id=parent_public_id,
        name=location.name,
        slug=location.slug,
        location_type=location.location_type,
        description=location.description,
        sort_order=location.sort_order,
        is_active=location.is_active,
    )


@router.get(
    "/tree",
    response_model=StorageTreeResponse,
)
def get_storage_tree(
    household_id: int,
    include_inactive: bool = False,
    session: Session = Depends(get_db_session),
) -> StorageTreeResponse:
    try:
        nodes = list_storage_tree(
            session=session,
            household_id=household_id,
            include_inactive=include_inactive,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    public_ids_by_id = _collect_public_ids(nodes)

    return StorageTreeResponse(
        household_id=household_id,
        include_inactive=include_inactive,
        locations=[
            _build_tree_node_response(
                node,
                public_ids_by_id=public_ids_by_id,
            )
            for node in nodes
        ],
    )


@router.post(
    "",
    response_model=StorageLocationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_storage(
    request: StorageLocationCreateRequest,
    session: Session = Depends(get_db_session),
) -> StorageLocationResponse:
    try:
        location = create_storage_location(
            session=session,
            data=StorageLocationCreateInput(
                household_id=request.household_id,
                parent_public_id=request.parent_public_id,
                name=request.name,
                slug=request.slug,
                location_type=request.location_type,
                description=request.description,
                sort_order=request.sort_order,
                is_active=request.is_active,
            ),
        )

        parent_public_id = None

        if location.parent is not None:
            parent_public_id = location.parent.public_id

        session.commit()

        return _build_location_response(
            location,
            parent_public_id=parent_public_id,
        )

    except ValueError as error:
        session.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    except Exception:
        session.rollback()
        raise
