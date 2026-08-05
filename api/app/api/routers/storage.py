"""
StorageLocation HTTP-végpontok.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.schemas import (
    StorageTreeNodeResponse,
    StorageTreeResponse,
)
from app.services import (
    StorageTreeNode,
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
