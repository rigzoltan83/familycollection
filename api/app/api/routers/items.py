"""
CollectionItem HTTP-végpontok.
"""

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from app.api.dependencies import (
    get_current_user,
    require_household_viewer_by_id,
    require_household_editor_by_id,
)
from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db_session
from app.models import (
    CategoryField,
    CollectionItem,
    ItemFieldValue,
    ItemIdentifier,
    ItemImage,
    User,
)
from app.schemas import (
    CollectionItemCreateRequest,
    CollectionItemResponse,
    CollectionItemListEntry,
    CollectionItemListResponse,
    CollectionItemUpdateRequest,
    ItemFieldValueResponse,
    ItemIdentifierResponse,
    ItemImageResponse,
)
from app.services import (
    CollectionItemCreateInput,
    CollectionItemUpdateInput,
    update_collection_item,
    IdentifierInput,
    create_collection_item,
    ImageStorageError,
    ItemImageCreateInput,
    create_item_image,
    delete_item_image_file,
    store_item_image,
    list_item_images,
)


router = APIRouter(
    prefix="/items",
    tags=["collection-items"],
)


def _load_item_for_response(
    session: Session,
    item_id: int,
) -> CollectionItem:
    item = session.scalar(
        select(CollectionItem)
        .options(
            selectinload(CollectionItem.identifiers),
            selectinload(CollectionItem.field_values).selectinload(
                ItemFieldValue.field
            ),
        )
        .where(CollectionItem.id == item_id)
    )

    if item is None:
        raise RuntimeError(
            "A létrehozott gyűjteményi elem nem tölthető vissza."
        )

    return item


def _build_item_response(
    item: CollectionItem,
) -> CollectionItemResponse:
    return CollectionItemResponse(
        public_id=item.public_id,
        household_id=item.household_id,
        category_id=item.category_id,
        title=item.title,
        subtitle=item.subtitle,
        notes=item.notes,
        status=item.status,
        is_active=item.is_active,
        created_by_user_id=item.created_by_user_id,
        updated_by_user_id=item.updated_by_user_id,
        created_at=item.created_at,
        updated_at=item.updated_at,
        identifiers=[
            ItemIdentifierResponse.model_validate(identifier)
            for identifier in item.identifiers
        ],
        field_values=[
            ItemFieldValueResponse(
                field_key=field_value.field.field_key,
                field_type=field_value.field.field_type,
                value_text=field_value.value_text,
                value_integer=field_value.value_integer,
                value_decimal=field_value.value_decimal,
                value_boolean=field_value.value_boolean,
                value_date=field_value.value_date,
                value_json=field_value.value_json,
            )
            for field_value in item.field_values
        ],
    )

def _build_item_image_response(
    image: ItemImage,
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
            f"/item-images/{image.public_id}/content"
        ),
    )


@router.get(
    "",
    response_model=CollectionItemListResponse,
)
def list_items(
    household_id: int,
    category_id: int | None = None,
    item_status: str | None = None,
    query: str | None = None,
    identifier: str | None = None,
    sort_by: str = "title",
    sort_direction: str = "asc",
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(
        get_current_user
    ),
    session: Session = Depends(get_db_session),
) -> CollectionItemListResponse:
    require_household_viewer_by_id(
        session=session,
        current_user=current_user,
        household_id=household_id,
    )

    if household_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A household_id csak pozitív egész szám lehet.",
        )

    if category_id is not None and category_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A category_id csak pozitív egész szám lehet.",
        )

    if limit < 1 or limit > 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A limit értéke 1 és 200 közötti lehet.",
        )

    if offset < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Az offset nem lehet negatív.",
        )

    normalized_query = (
        query.strip()
        if query is not None
        else None
    )

    normalized_identifier = (
        identifier.strip()
        if identifier is not None
        else None
    )

    allowed_sort_fields = {
        "title": CollectionItem.title,
        "created_at": CollectionItem.created_at,
        "updated_at": CollectionItem.updated_at,
    }

    if sort_by not in allowed_sort_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "A sort_by értéke csak title, created_at "
                "vagy updated_at lehet."
            ),
        )

    if sort_direction not in {
        "asc",
        "desc",
    }:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A sort_direction értéke csak asc vagy desc lehet.",
        )

    sort_column = allowed_sort_fields[sort_by]

    primary_order = (
        sort_column.asc()
        if sort_direction == "asc"
        else sort_column.desc()
    )

    allowed_statuses = {
        "active",
        "loaned",
        "archived",
        "missing",
        "disposed",
    }

    if (
        item_status is not None
        and item_status not in allowed_statuses
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "A status értéke csak active, loaned, archived, "
                "missing vagy disposed lehet."
            ),
        )

    if normalized_identifier == "":
        normalized_identifier = None

    if normalized_query == "":
        normalized_query = None

    filters = [
        CollectionItem.household_id == household_id,
        CollectionItem.is_active.is_(True),
    ]

    if normalized_identifier is not None:
        filters.append(
            exists(
                select(ItemIdentifier.id).where(
                    ItemIdentifier.item_id
                    == CollectionItem.id,
                    ItemIdentifier.is_active.is_(True),
                    ItemIdentifier.identifier_value
                    == normalized_identifier,
                )
            )
        )

    if normalized_query is not None:
        search_pattern = f"%{normalized_query}%"

        searchable_field_match = exists(
            select(ItemFieldValue.id)
            .join(
                CategoryField,
                CategoryField.id == ItemFieldValue.field_id,
            )
            .where(
                ItemFieldValue.item_id == CollectionItem.id,
                CategoryField.is_active.is_(True),
                CategoryField.is_searchable.is_(True),
                ItemFieldValue.value_text.ilike(search_pattern),
            )
        )

        filters.append(
            (
                CollectionItem.title.ilike(search_pattern)
                |
                CollectionItem.subtitle.ilike(search_pattern)
                |
                searchable_field_match
            )
        )

    if category_id is not None:
        filters.append(
            CollectionItem.category_id == category_id
        )

    if item_status is not None:
        filters.append(
            CollectionItem.status == item_status
        )

    total = session.scalar(
        select(func.count(CollectionItem.id)).where(*filters)
    )

    items = session.scalars(
        select(CollectionItem)
        .where(*filters)
        .order_by(
            primary_order,
            CollectionItem.id.asc(),
        )
        .limit(limit)
        .offset(offset)
    ).all()

    return CollectionItemListResponse(
        items=[
            CollectionItemListEntry(
                public_id=item.public_id,
                household_id=item.household_id,
                category_id=item.category_id,
                title=item.title,
                subtitle=item.subtitle,
                status=item.status,
                is_active=item.is_active,
                created_at=item.created_at,
                updated_at=item.updated_at,
            )
            for item in items
        ],
        total=total or 0,
        limit=limit,
        offset=offset,
    )


@router.post(
    "",
    response_model=CollectionItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_item(
    request: CollectionItemCreateRequest,
    current_user: User = Depends(
        get_current_user
    ),
    session: Session = Depends(get_db_session),
) -> CollectionItemResponse:
    require_household_editor_by_id(
        session=session,
        current_user=current_user,
        household_id=request.household_id,
    )
    try:
        item = create_collection_item(
            session=session,
            data=CollectionItemCreateInput(
                household_id=request.household_id,
                category_id=request.category_id,
                title=request.title,
                subtitle=request.subtitle,
                notes=request.notes,
                status=request.status,
                created_by_user_id=request.created_by_user_id,
                identifiers=[
                    IdentifierInput(
                        identifier_type=identifier.identifier_type,
                        identifier_value=identifier.identifier_value,
                        provider_code=identifier.provider_code,
                        is_primary=identifier.is_primary,
                    )
                    for identifier in request.identifiers
                ],
                field_values=request.field_values,
            ),
        )

        session.commit()

    except ValueError as error:
        session.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    except Exception:
        session.rollback()
        raise

    loaded_item = _load_item_for_response(
        session=session,
        item_id=item.id,
    )

    return _build_item_response(loaded_item)


@router.patch(
    "/{public_id}",
    response_model=CollectionItemResponse,
)
def update_item(
    public_id: str,
    request: CollectionItemUpdateRequest,
    current_user: User = Depends(
        get_current_user
    ),
    session: Session = Depends(get_db_session),
) -> CollectionItemResponse:
    item = session.scalar(
        select(CollectionItem)
        .options(
            selectinload(CollectionItem.identifiers),
            selectinload(CollectionItem.field_values).selectinload(
                ItemFieldValue.field
            ),
        )
        .where(CollectionItem.public_id == public_id)
    )

    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A gyűjteményi elem nem található.",
        )

    require_household_editor_by_id(
        session=session,
        current_user=current_user,
        household_id=item.household_id,
    )

    try:
        updated_item = update_collection_item(
            session=session,
            item=item,
            data=CollectionItemUpdateInput(
                title=request.title,
                subtitle=request.subtitle,
                notes=request.notes,
                status=request.status,
                is_active=request.is_active,
                updated_by_user_id=request.updated_by_user_id,
                identifiers=(
                    [
                        IdentifierInput(
                            identifier_type=identifier.identifier_type,
                            identifier_value=identifier.identifier_value,
                            provider_code=identifier.provider_code,
                            is_primary=identifier.is_primary,
                        )
                        for identifier in request.identifiers
                    ]
                    if request.identifiers is not None
                    else None
                ),
                field_values=request.field_values,
                fields_set=set(request.model_fields_set),
            ),
        )

        session.commit()

    except ValueError as error:
        session.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    except Exception:
        session.rollback()
        raise

    loaded_item = _load_item_for_response(
        session=session,
        item_id=updated_item.id,
    )

    return _build_item_response(loaded_item)


@router.post(
    "/{public_id}/images",
    response_model=ItemImageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_item_image(
    public_id: str,
    file: UploadFile = File(...),
    caption: str | None = Form(default=None),
    is_primary: bool | None = Form(default=None),
    sort_order: int = Form(default=0),
    current_user: User = Depends(
        get_current_user
    ),
    session: Session = Depends(get_db_session),
) -> ItemImageResponse:
    item = session.scalar(
        select(CollectionItem).where(
            CollectionItem.public_id == public_id,
            CollectionItem.is_active.is_(True),
        )
    )

    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A gyűjteményi elem nem található.",
        )

    require_household_editor_by_id(
        session=session,
        current_user=current_user,
        household_id=item.household_id,
    )

    if sort_order < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "A kép rendezési sorrendje "
                "nem lehet negatív."
            ),
        )

    stored_image = None

    try:
        content = await file.read()

        stored_image = store_item_image(
            content
        )

        image = create_item_image(
            session=session,
            item=item,
            data=ItemImageCreateInput(
                stored_filename=(
                    stored_image.stored_filename
                ),
                original_filename=(
                    file.filename
                    if file.filename
                    else None
                ),
                caption=caption,
                mime_type=stored_image.mime_type,
                file_size=stored_image.file_size,
                width=stored_image.width,
                height=stored_image.height,
                sort_order=sort_order,
                is_primary=is_primary,
            ),
        )

        session.commit()
        session.refresh(image)

    except (
        ImageStorageError,
        ValueError,
    ) as error:
        session.rollback()

        if stored_image is not None:
            delete_item_image_file(
                stored_image.stored_filename
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    except Exception:
        session.rollback()

        if stored_image is not None:
            delete_item_image_file(
                stored_image.stored_filename
            )

        raise

    finally:
        await file.close()

    return _build_item_image_response(
        image
    )


@router.get(
    "/{public_id}/images",
    response_model=list[ItemImageResponse],
)
def get_item_images(
    public_id: str,
    current_user: User = Depends(
        get_current_user
    ),
    session: Session = Depends(get_db_session),
) -> list[ItemImageResponse]:
    item = session.scalar(
        select(CollectionItem).where(
            CollectionItem.public_id == public_id,
            CollectionItem.is_active.is_(True),
        )
    )

    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A gyűjteményi elem nem található.",
        )

    require_household_viewer_by_id(
        session=session,
        current_user=current_user,
        household_id=item.household_id,
    )

    images = list_item_images(
        session=session,
        item=item,
    )

    return [
        _build_item_image_response(image)
        for image in images
    ]


@router.get(
    "/{public_id}",
    response_model=CollectionItemResponse,
)
def get_item(
    public_id: str,
    current_user: User = Depends(
        get_current_user
    ),
    session: Session = Depends(get_db_session),
) -> CollectionItemResponse:
    item = session.scalar(
        select(CollectionItem)
        .options(
            selectinload(CollectionItem.identifiers),
            selectinload(CollectionItem.field_values).selectinload(
                ItemFieldValue.field
            ),
        )
        .where(
            CollectionItem.public_id == public_id,
            CollectionItem.is_active.is_(True),
        )
    )

    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A gyűjteményi elem nem található.",
        )

    require_household_viewer_by_id(
        session=session,
        current_user=current_user,
        household_id=item.household_id,
    )

    return _build_item_response(item)

@router.delete(
    "/{public_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_item(
    public_id: str,
    current_user: User = Depends(
        get_current_user
    ),
    session: Session = Depends(get_db_session),
) -> None:
    item = session.scalar(
        select(CollectionItem).where(
            CollectionItem.public_id == public_id,
            CollectionItem.is_active.is_(True),
        )
    )

    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A gyűjteményi elem nem található.",
        )

    require_household_editor_by_id(
        session=session,
        current_user=current_user,
        household_id=item.household_id,
    )

    item.is_active = False

    session.commit()

@router.post(
    "/{public_id}/restore",
    response_model=CollectionItemResponse,
)
def restore_item(
    public_id: str,
    current_user: User = Depends(
        get_current_user
    ),
    session: Session = Depends(get_db_session),
) -> CollectionItemResponse:
    item = session.scalar(
        select(CollectionItem).where(
            CollectionItem.public_id == public_id,
            CollectionItem.is_active.is_(False),
        )
    )

    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A törölt gyűjteményi elem nem található.",
        )

    require_household_editor_by_id(
        session=session,
        current_user=current_user,
        household_id=item.household_id,
    )

    item.is_active = True

    session.commit()

    loaded_item = _load_item_for_response(
        session=session,
        item_id=item.id,
    )

    return _build_item_response(loaded_item)
