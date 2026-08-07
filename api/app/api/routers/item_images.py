"""
ItemImage HTTP-végpontok.
"""

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.services import (
    ImageStorageError,
    get_item_image_by_public_id,
    resolve_item_image_path,
    resolve_item_image_thumbnail_path,
    ensure_item_image_thumbnail,
    ItemImageUpdateInput,
    update_item_image,
    delete_item_image,
    delete_item_image_file,
)
from app.schemas import (
    ItemImageResponse,
    ItemImageUpdateRequest,
)

router = APIRouter(
    prefix="/item-images",
    tags=["item-images"],
)


def _build_item_image_response(
    image,
) -> ItemImageResponse:
    return ItemImageResponse(
        public_id=image.public_id,
        item_id=image.item_id,
        original_filename=image.original_filename,
        caption=image.caption,
        mime_type=image.mime_type,
        file_size=image.file_size,
        width=image.width,
        height=image.height,
        sort_order=image.sort_order,
        is_primary=image.is_primary,
        is_active=image.is_active,
        created_at=image.created_at,
        updated_at=image.updated_at,
        content_url=(
            f"/item-images/"
            f"{image.public_id}/content"
        ),
    )


@router.patch(
    "/{image_public_id}",
    response_model=ItemImageResponse,
)
def update_item_image_endpoint(
    image_public_id: str,
    request: ItemImageUpdateRequest,
    session: Session = Depends(get_db_session),
) -> ItemImageResponse:
    image = get_item_image_by_public_id(
        session=session,
        public_id=image_public_id,
    )

    if image is None or not image.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A kép nem található.",
        )

    try:
        updated_image = update_item_image(
            session=session,
            image=image,
            data=ItemImageUpdateInput(
                caption=request.caption,
                sort_order=request.sort_order,
                is_primary=request.is_primary,
                fields_set=set(
                    request.model_fields_set
                ),
            ),
        )

        session.commit()
        session.refresh(updated_image)

    except ValueError as error:
        session.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    except Exception:
        session.rollback()
        raise

    return _build_item_image_response(
        updated_image
    )


@router.delete(
    "/{image_public_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_item_image_endpoint(
    image_public_id: str,
    session: Session = Depends(get_db_session),
) -> None:
    image = get_item_image_by_public_id(
        session=session,
        public_id=image_public_id,
    )

    if image is None or not image.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A kép nem található.",
        )

    stored_filename = image.stored_filename

    try:
        delete_item_image(
            session=session,
            image=image,
        )

        session.commit()

    except Exception:
        session.rollback()
        raise

    try:
        delete_item_image_file(
            stored_filename
        )

    except ImageStorageError:
        # A DB-rekord törlése már sikerült.
        # Hibás vagy hiányzó fájlútvonal miatt
        # nem állítjuk vissza a törlést.
        pass


@router.get(
    "/{image_public_id}/content",
    response_class=FileResponse,
)
def get_item_image_content(
    image_public_id: str,
    session: Session = Depends(get_db_session),
) -> FileResponse:
    image = get_item_image_by_public_id(
        session=session,
        public_id=image_public_id,
    )

    if image is None or not image.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A kép nem található.",
        )

    try:
        image_path = resolve_item_image_path(
            image.stored_filename
        )

    except ImageStorageError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A képfájl nem található.",
        ) from error

    if (
        not image_path.exists()
        or not image_path.is_file()
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A képfájl nem található.",
        )

    return FileResponse(
        path=image_path,
        media_type=image.mime_type,
        filename=None,
        headers={
            "Cache-Control":
                "public, max-age=86400",
        },
    )


@router.get(
    "/{image_public_id}/thumbnail",
    response_class=FileResponse,
)
def get_item_image_thumbnail(
    image_public_id: str,
    session: Session = Depends(get_db_session),
) -> FileResponse:
    image = get_item_image_by_public_id(
        session=session,
        public_id=image_public_id,
    )

    if image is None or not image.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A kép nem található.",
        )

    try:
        thumbnail_path = (
            ensure_item_image_thumbnail(
                image.stored_filename
            )
        )

    except ImageStorageError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "A kép bélyegképe nem található."
            ),
        ) from error

    if (
        not thumbnail_path.exists()
        or not thumbnail_path.is_file()
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "A kép bélyegképe nem található."
            ),
        )

    return FileResponse(
        path=thumbnail_path,
        media_type="image/webp",
        filename=None,
        headers={
            "Cache-Control":
                "public, max-age=86400",
        },
    )
