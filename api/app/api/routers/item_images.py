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
)


router = APIRouter(
    prefix="/item-images",
    tags=["item-images"],
)


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
