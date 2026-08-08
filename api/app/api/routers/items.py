"""
CollectionItem HTTP-végpontok.
"""

import json
from datetime import date
from decimal import Decimal, InvalidOperation

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
from sqlalchemy import String, cast, exists, func, select
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.dialects.postgresql import JSONB

from app.core.database import get_db_session
from app.models import (
    CategoryField,
    CollectionItem,
    ItemFieldValue,
    ItemIdentifier,
    ItemImage,
    ItemStorageAssignment,
    StorageLocation,
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
    get_active_item_storage_assignment,
    set_item_storage_location,
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
            selectinload(
                CollectionItem.storage_assignments
            ).selectinload(
                ItemStorageAssignment.storage_location
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
    active_storage_assignment = next(
        (
            assignment
            for assignment in item.storage_assignments
            if assignment.is_active
        ),
        None,
    )

    storage_public_id = (
        active_storage_assignment.storage_location.public_id
        if (
            active_storage_assignment is not None
            and active_storage_assignment.storage_location is not None
        )
        else None
    )
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
        storage_public_id=storage_public_id,
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
    storage_public_id: str | None = None,
    query: str | None = None,
    identifier: str | None = None,
    field_filters: str | None = None,
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

    normalized_storage_public_id = (
        storage_public_id.strip()
        if storage_public_id is not None
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

    if normalized_storage_public_id == "":
        normalized_storage_public_id = None

    if normalized_query == "":
        normalized_query = None

    filters = [
        CollectionItem.household_id == household_id,
        CollectionItem.is_active.is_(True),
    ]

    if normalized_storage_public_id is not None:
        storage_location = session.scalar(
            select(StorageLocation).where(
                StorageLocation.public_id
                == normalized_storage_public_id,
                StorageLocation.household_id
                == household_id,
                StorageLocation.is_active.is_(True),
            )
        )

        if storage_location is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "A megadott tárolóhely nem létezik "
                    "ebben a háztartásban."
                ),
            )

        filters.append(
            exists(
                select(ItemStorageAssignment.id).where(
                    ItemStorageAssignment.item_id
                    == CollectionItem.id,
                    ItemStorageAssignment.storage_location_id
                    == storage_location.id,
                    ItemStorageAssignment.is_active.is_(True),
                )
            )
        )

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

    if field_filters is not None:
        if category_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "A field_filters használatához "
                    "category_id szükséges."
                ),
            )

        try:
            parsed_field_filters = json.loads(
                field_filters
            )
        except json.JSONDecodeError as error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "A field_filters nem érvényes JSON."
                ),
            ) from error

        if not isinstance(
            parsed_field_filters,
            dict,
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "A field_filters JSON objektum "
                    "kell legyen."
                ),
            )

        filterable_fields = session.scalars(
            select(CategoryField).where(
                CategoryField.category_id
                == category_id,
                CategoryField.is_active.is_(True),
                CategoryField.is_filterable.is_(True),
            )
        ).all()

        filterable_fields_by_key = {
            field.field_key: field
            for field in filterable_fields
        }

        for field_key, filter_definition in (
            parsed_field_filters.items()
        ):
            field = filterable_fields_by_key.get(
                field_key
            )

            if field is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "Ismeretlen vagy nem szűrhető mező: "
                        f"{field_key}"
                    ),
                )

            if not isinstance(
                filter_definition,
                dict,
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "A mezőszűrő objektum kell legyen: "
                        f"{field_key}"
                    ),
                )

            field_conditions = [
                ItemFieldValue.item_id
                == CollectionItem.id,
                ItemFieldValue.field_id
                == field.id,
            ]

            if field.field_type in {
                "text",
                "long_text",
                "url",
                "email",
                "barcode",
            }:
                value = filter_definition.get(
                    "value"
                )

                if (
                    value is None
                    or not isinstance(value, str)
                ):
                    raise HTTPException(
                        status_code=(
                            status.HTTP_400_BAD_REQUEST
                        ),
                        detail=(
                            "Szöveges szűrőhöz value "
                            "szükséges: "
                            f"{field_key}"
                        ),
                    )

                normalized_value = value.strip()

                if not normalized_value:
                    continue

                field_conditions.append(
                    ItemFieldValue.value_text.ilike(
                        f"%{normalized_value}%"
                    )
                )

            elif field.field_type == "single_select":
                value = filter_definition.get(
                    "value"
                )

                if (
                    value is None
                    or not isinstance(value, str)
                    or not value.strip()
                ):
                    continue

                normalized_value = value.strip()

                field_conditions.append(
                    cast(
                        ItemFieldValue.value_json,
                        String,
                    )
                    == json.dumps(
                        normalized_value
                    )
                )

            elif field.field_type in {
                "integer",
                "year",
            }:
                minimum = filter_definition.get(
                    "min"
                )
                maximum = filter_definition.get(
                    "max"
                )

                try:
                    if minimum is not None:
                        minimum = int(minimum)

                    if maximum is not None:
                        maximum = int(maximum)

                except (TypeError, ValueError) as error:
                    raise HTTPException(
                        status_code=(
                            status.HTTP_400_BAD_REQUEST
                        ),
                        detail=(
                            "Egész számos szűrő hibás: "
                            f"{field_key}"
                        ),
                    ) from error

                if minimum is None and maximum is None:
                    continue

                if (
                    minimum is not None
                    and maximum is not None
                    and minimum > maximum
                ):
                    raise HTTPException(
                        status_code=(
                            status.HTTP_400_BAD_REQUEST
                        ),
                        detail=(
                            "A minimum nem lehet nagyobb "
                            "a maximumnál: "
                            f"{field_key}"
                        ),
                    )

                if minimum is not None:
                    field_conditions.append(
                        ItemFieldValue.value_integer
                        >= minimum
                    )

                if maximum is not None:
                    field_conditions.append(
                        ItemFieldValue.value_integer
                        <= maximum
                    )

            elif field.field_type == "decimal":
                minimum = filter_definition.get(
                    "min"
                )
                maximum = filter_definition.get(
                    "max"
                )

                try:
                    if minimum is not None:
                        minimum = Decimal(
                            str(minimum)
                        )

                    if maximum is not None:
                        maximum = Decimal(
                            str(maximum)
                        )

                except (
                    InvalidOperation,
                    TypeError,
                    ValueError,
                ) as error:
                    raise HTTPException(
                        status_code=(
                            status.HTTP_400_BAD_REQUEST
                        ),
                        detail=(
                            "Tizedes szűrő hibás: "
                            f"{field_key}"
                        ),
                    ) from error

                if minimum is None and maximum is None:
                    continue

                if (
                    minimum is not None
                    and maximum is not None
                    and minimum > maximum
                ):
                    raise HTTPException(
                        status_code=(
                            status.HTTP_400_BAD_REQUEST
                        ),
                        detail=(
                            "A minimum nem lehet nagyobb "
                            "a maximumnál: "
                            f"{field_key}"
                        ),
                    )

                if minimum is not None:
                    field_conditions.append(
                        ItemFieldValue.value_decimal
                        >= minimum
                    )

                if maximum is not None:
                    field_conditions.append(
                        ItemFieldValue.value_decimal
                        <= maximum
                    )

            elif field.field_type == "boolean":
                value = filter_definition.get(
                    "value"
                )

                if not isinstance(value, bool):
                    raise HTTPException(
                        status_code=(
                            status.HTTP_400_BAD_REQUEST
                        ),
                        detail=(
                            "Logikai szűrőhöz true vagy "
                            "false szükséges: "
                            f"{field_key}"
                        ),
                    )

                field_conditions.append(
                    ItemFieldValue.value_boolean
                    == value
                )

            elif field.field_type == "date":
                minimum = filter_definition.get(
                    "min"
                )
                maximum = filter_definition.get(
                    "max"
                )

                try:
                    if minimum is not None:
                        minimum = date.fromisoformat(
                            str(minimum)
                        )

                    if maximum is not None:
                        maximum = date.fromisoformat(
                            str(maximum)
                        )

                except ValueError as error:
                    raise HTTPException(
                        status_code=(
                            status.HTTP_400_BAD_REQUEST
                        ),
                        detail=(
                            "A dátumszűrő YYYY-MM-DD "
                            "formátumú legyen: "
                            f"{field_key}"
                        ),
                    ) from error

                if minimum is None and maximum is None:
                    continue

                if (
                    minimum is not None
                    and maximum is not None
                    and minimum > maximum
                ):
                    raise HTTPException(
                        status_code=(
                            status.HTTP_400_BAD_REQUEST
                        ),
                        detail=(
                            "A kezdődátum nem lehet későbbi "
                            "a záródátumnál: "
                            f"{field_key}"
                        ),
                    )

                if minimum is not None:
                    field_conditions.append(
                        ItemFieldValue.value_date
                        >= minimum
                    )

                if maximum is not None:
                    field_conditions.append(
                        ItemFieldValue.value_date
                        <= maximum
                    )

            elif field.field_type == "multi_select":
                value = filter_definition.get(
                    "value"
                )

                if (
                    value is None
                    or not isinstance(value, str)
                    or not value.strip()
                ):
                    continue

                normalized_value = value.strip()

                field_conditions.append(
                    func.jsonb_exists(
                        cast(
                            ItemFieldValue.value_json,
                            JSONB,
                        ),
                        normalized_value,
                    )
                )

            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "Ez a mezőtípus nem szűrhető: "
                        f"{field.field_type}"
                    ),
                )

            filters.append(
                exists(
                    select(ItemFieldValue.id).where(
                        *field_conditions
                    )
                )
            )


    total = session.scalar(
        select(func.count(CollectionItem.id)).where(*filters)
    )

    items = session.scalars(
        select(CollectionItem)
        .options(
            selectinload(
                CollectionItem.field_values
            ).selectinload(
                ItemFieldValue.field
            )
        )
        .where(*filters)
        .order_by(
            primary_order,
            CollectionItem.id.asc(),
        )
        .limit(limit)
        .offset(offset)
    ).all()

    item_ids = [
        item.id
        for item in items
    ]

    primary_images_by_item_id: dict[
        int,
        ItemImage,
    ] = {}

    if item_ids:
        primary_images = session.scalars(
            select(ItemImage)
            .where(
                ItemImage.item_id.in_(item_ids),
                ItemImage.is_active.is_(True),
                ItemImage.is_primary.is_(True),
            )
        ).all()

        primary_images_by_item_id = {
            image.item_id: image
            for image in primary_images
        }

    active_storage_by_item_id: dict[
        int,
        ItemStorageAssignment,
    ] = {}

    if item_ids:
        active_storage_assignments = session.scalars(
            select(ItemStorageAssignment)
            .options(
                selectinload(
                    ItemStorageAssignment.storage_location
                )
            )
            .where(
                ItemStorageAssignment.item_id.in_(item_ids),
                ItemStorageAssignment.is_active.is_(True),
            )
        ).all()

        active_storage_by_item_id = {
            assignment.item_id: assignment
            for assignment in active_storage_assignments
        }

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
                storage_public_id=(
                    active_storage_by_item_id[
                        item.id
                    ].storage_location.public_id
                    if (
                        item.id in active_storage_by_item_id
                        and active_storage_by_item_id[
                            item.id
                        ].storage_location is not None
                    )
                    else None
                ),
                primary_image_thumbnail_url=(
                    (
                        f"/item-images/"
                        f"{primary_images_by_item_id[item.id].public_id}"
                        f"/thumbnail"
                    )
                    if item.id in primary_images_by_item_id
                    else None
                ),
                field_values=[
                    ItemFieldValueResponse(
                        field_key=field_value.field.field_key,
                        field_type=field_value.field.field_type,
                        value_text=field_value.value_text,
                        value_integer=(
                            field_value.value_integer
                        ),
                        value_decimal=(
                            field_value.value_decimal
                        ),
                        value_boolean=(
                            field_value.value_boolean
                        ),
                        value_date=field_value.value_date,
                        value_json=field_value.value_json,
                    )
                    for field_value in item.field_values
                    if (
                        field_value.field is not None
                        and field_value.field.is_active
                    )
                 ],
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
                storage_public_id=request.storage_public_id,
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

        if request.storage_public_id is not None:
            set_item_storage_location(
                session=session,
                item=item,
                storage_public_id=request.storage_public_id,
                moved_by_user_id=request.created_by_user_id,
                movement_reason="item_creation",
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
                storage_public_id=request.storage_public_id,
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

        if "storage_public_id" in request.model_fields_set:
            set_item_storage_location(
                session=session,
                item=updated_item,
                storage_public_id=request.storage_public_id,
                moved_by_user_id=request.updated_by_user_id,
                movement_reason="item_update",
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
