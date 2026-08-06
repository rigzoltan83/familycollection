"""
CollectionItem üzleti szolgáltatások.

A szolgáltatás egy tranzakcióban hozza létre:

- a központi CollectionItem rekordot;
- az opcionális azonosítókat;
- a dinamikus kategóriamező-értékeket.

A HTTP-rétegtől független.
"""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Category,
    CategoryField,
    CategoryFieldOption,
    CollectionItem,
    Household,
    ItemFieldValue,
    ItemIdentifier,
    User,
    ItemImage,
)


@dataclass(slots=True)
class IdentifierInput:
    identifier_type: str
    identifier_value: str
    provider_code: str | None = None
    is_primary: bool = False


@dataclass(slots=True)
class CollectionItemCreateInput:
    household_id: int
    category_id: int
    title: str
    subtitle: str | None = None
    notes: str | None = None
    status: str = "active"
    created_by_user_id: int | None = None
    identifiers: list[IdentifierInput] = field(default_factory=list)
    field_values: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class CollectionItemUpdateInput:
    title: str | None = None
    subtitle: str | None = None
    notes: str | None = None
    status: str | None = None
    is_active: bool | None = None
    updated_by_user_id: int | None = None
    identifiers: list[IdentifierInput] | None = None
    field_values: dict[str, Any] | None = None
    fields_set: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        """
        Közvetlen szolgáltatáshívásnál a nem None mezőket
        automatikusan módosítandónak tekinti.

        Az API-réteg explicit fields_set értékkel a nullára
        állítást is támogatja.
        """
        if not self.fields_set:
            self.fields_set = {
                field_name
                for field_name in (
                    "title",
                    "subtitle",
                    "notes",
                    "status",
                    "is_active",
                    "updated_by_user_id",
                    "identifiers",
                    "field_values",
                )
                if getattr(self, field_name) is not None
            }


def _ensure_household_exists(
    session: Session,
    household_id: int,
) -> Household:
    household = session.get(Household, household_id)

    if household is None:
        raise ValueError("A megadott háztartás nem létezik.")

    return household


def _ensure_category_available(
    session: Session,
    category_id: int,
    household_id: int,
) -> Category:
    category = session.get(Category, category_id)

    if category is None or not category.is_active:
        raise ValueError("A megadott kategória nem elérhető.")

    if category.is_system:
        return category

    if category.household_id != household_id:
        raise ValueError(
            "A kategória nem a megadott háztartáshoz tartozik."
        )

    return category


def _ensure_user_exists(
    session: Session,
    user_id: int | None,
) -> User | None:
    if user_id is None:
        return None

    user = session.get(User, user_id)

    if user is None:
        raise ValueError("A megadott felhasználó nem létezik.")

    return user


def _get_category_fields(
    session: Session,
    category_id: int,
) -> dict[str, CategoryField]:
    fields = session.scalars(
        select(CategoryField).where(
            CategoryField.category_id == category_id,
            CategoryField.is_active.is_(True),
        )
    ).all()

    return {
        category_field.field_key: category_field
        for category_field in fields
    }


def _get_field_options(
    session: Session,
    field_id: int,
) -> set[str]:
    """
    Az aktív választható értékek lekérése.
    """
    option_values = session.scalars(
        select(CategoryFieldOption.value).where(
            CategoryFieldOption.field_id == field_id,
            CategoryFieldOption.is_active.is_(True),
        )
    ).all()

    return set(option_values)


def _validate_numeric_rules(
    category_field: CategoryField,
    numeric_value: int | Decimal,
) -> None:
    rules = category_field.validation_rules or {}

    minimum = rules.get("minimum")
    maximum = rules.get("maximum")

    if minimum is not None and numeric_value < Decimal(str(minimum)):
        raise ValueError(
            f"A(z) {category_field.field_key} mező értéke "
            f"nem lehet kisebb mint {minimum}."
        )

    if maximum is not None and numeric_value > Decimal(str(maximum)):
        raise ValueError(
            f"A(z) {category_field.field_key} mező értéke "
            f"nem lehet nagyobb mint {maximum}."
        )


def _validate_text_rules(
    category_field: CategoryField,
    text_value: str,
) -> None:
    rules = category_field.validation_rules or {}

    minimum_length = rules.get("minimum_length")
    maximum_length = rules.get("maximum_length")

    if (
        minimum_length is not None
        and len(text_value) < int(minimum_length)
    ):
        raise ValueError(
            f"A(z) {category_field.field_key} mező legalább "
            f"{minimum_length} karakter hosszú legyen."
        )

    if (
        maximum_length is not None
        and len(text_value) > int(maximum_length)
    ):
        raise ValueError(
            f"A(z) {category_field.field_key} mező legfeljebb "
            f"{maximum_length} karakter hosszú lehet."
        )


def _validate_select_value(
    session: Session,
    category_field: CategoryField,
    value: Any,
) -> None:
    allowed_values = _get_field_options(
        session=session,
        field_id=category_field.id,
    )

    if category_field.field_type == "single_select":
        if not isinstance(value, str):
            raise ValueError(
                f"A(z) {category_field.field_key} mező "
                "egyetlen szöveges értéket vár."
            )

        if value not in allowed_values:
            raise ValueError(
                f"Érvénytelen választási érték a(z) "
                f"{category_field.field_key} mezőnél: {value}"
            )

        return

    if not isinstance(value, list):
        raise ValueError(
            f"A(z) {category_field.field_key} mező "
            "értéklistát vár."
        )

    invalid_values = set(value) - allowed_values

    if invalid_values:
        invalid = ", ".join(sorted(str(item) for item in invalid_values))

        raise ValueError(
            f"Érvénytelen választási értékek a(z) "
            f"{category_field.field_key} mezőnél: {invalid}"
        )


def _build_field_value(
    session: Session,
    item: CollectionItem,
    category_field: CategoryField,
    value: Any,
) -> ItemFieldValue:
    field_value = ItemFieldValue(
        item=item,
        field=category_field,
    )

    field_type = category_field.field_type

    if field_type in {
        "text",
        "long_text",
        "url",
        "email",
        "barcode",
        "image",
        "file",
    }:
        text_value = str(value).strip()

        _validate_text_rules(
            category_field=category_field,
            text_value=text_value,
        )

        field_value.value_text = text_value

    elif field_type in {
        "integer",
        "year",
    }:
        try:
            integer_value = int(value)
        except (TypeError, ValueError) as error:
            raise ValueError(
                f"A(z) {category_field.field_key} mező "
                "egész számot vár."
            ) from error

        _validate_numeric_rules(
            category_field=category_field,
            numeric_value=integer_value,
        )

        field_value.value_integer = integer_value

    elif field_type == "decimal":
        try:
            decimal_value = Decimal(str(value))
        except Exception as error:
            raise ValueError(
                f"A(z) {category_field.field_key} mező "
                "decimális számot vár."
            ) from error

        _validate_numeric_rules(
            category_field=category_field,
            numeric_value=decimal_value,
        )

        field_value.value_decimal = decimal_value

    elif field_type == "boolean":
        if not isinstance(value, bool):
            raise ValueError(
                f"A(z) {category_field.field_key} mező "
                "logikai értéket vár."
            )

        field_value.value_boolean = value

    elif field_type == "date":
        if not isinstance(value, date):
            raise ValueError(
                f"A(z) {category_field.field_key} mező dátumot vár."
            )

        field_value.value_date = value

    elif field_type in {
        "single_select",
        "multi_select",
    }:
        _validate_select_value(
            session=session,
            category_field=category_field,
            value=value,
        )

        field_value.value_json = value

    else:
        raise ValueError(
            f"Nem támogatott mezőtípus: {field_type}"
        )

    return field_value

def create_collection_item(
    session: Session,
    data: CollectionItemCreateInput,
) -> CollectionItem:
    """
    Új gyűjteményi elem létrehozása.

    A hívó kezeli a commitot vagy rollbacket.
    """
    _ensure_household_exists(
        session=session,
        household_id=data.household_id,
    )

    category = _ensure_category_available(
        session=session,
        category_id=data.category_id,
        household_id=data.household_id,
    )

    creator = _ensure_user_exists(
        session=session,
        user_id=data.created_by_user_id,
    )

    normalized_title = data.title.strip()

    if not normalized_title:
        raise ValueError("A cím nem lehet üres.")

    category_fields = _get_category_fields(
        session=session,
        category_id=category.id,
    )

    unknown_field_keys = (
        set(data.field_values) - set(category_fields)
    )

    if unknown_field_keys:
        unknown = ", ".join(sorted(unknown_field_keys))

        raise ValueError(
            f"Ismeretlen kategóriamezők: {unknown}"
        )

    missing_required_fields = [
        category_field.field_key
        for category_field in category_fields.values()
        if category_field.is_required
        and category_field.field_key not in data.field_values
    ]

    if missing_required_fields:
        missing = ", ".join(sorted(missing_required_fields))

        raise ValueError(
            f"Hiányzó kötelező mezők: {missing}"
        )

    item = CollectionItem(
        household_id=data.household_id,
        category=category,
        title=normalized_title,
        subtitle=data.subtitle,
        notes=data.notes,
        status=data.status,
        created_by_user=creator,
        updated_by_user=creator,
    )

    session.add(item)
    session.flush()

    for identifier_input in data.identifiers:
        identifier_value = (
            identifier_input.identifier_value.strip()
        )

        if not identifier_value:
            raise ValueError(
                "Az azonosító értéke nem lehet üres."
            )

        session.add(
            ItemIdentifier(
                item=item,
                identifier_type=identifier_input.identifier_type,
                identifier_value=identifier_value,
                provider_code=identifier_input.provider_code,
                is_primary=identifier_input.is_primary,
            )
        )

    for field_key, value in data.field_values.items():
        if value is None:
            continue

        session.add(
            _build_field_value(
                session=session,
                item=item,
                category_field=category_fields[field_key],
                value=value,
            )
        )

    session.flush()

    return item

def update_collection_item(
    session: Session,
    item: CollectionItem,
    data: CollectionItemUpdateInput,
) -> CollectionItem:
    """
    Meglévő gyűjteményi elem részleges módosítása.

    A None értékű inputmezők nem módosítják az adott mezőt.
    Az identifiers és field_values listák megadása teljes cserét jelent.
    A hívó kezeli a commitot vagy rollbacket.
    """

    if "title" in data.fields_set:
        if data.title is None:
            raise ValueError("A cím nem lehet üres.")

        normalized_title = data.title.strip()

        if not normalized_title:
            raise ValueError("A cím nem lehet üres.")

        item.title = normalized_title

    if "subtitle" in data.fields_set:
        item.subtitle = data.subtitle

    if "notes" in data.fields_set:
        item.notes = data.notes

    if "status" in data.fields_set:
        if data.status is None:
            raise ValueError("A státusz nem lehet üres.")

        item.status = data.status

    if "is_active" in data.fields_set:
        if data.is_active is None:
            raise ValueError(
                "Az is_active értéke nem lehet üres."
            )

        item.is_active = data.is_active

    updater = _ensure_user_exists(
        session=session,
        user_id=data.updated_by_user_id,
    )

    if "updated_by_user_id" in data.fields_set:
        item.updated_by_user = updater

    category_fields = _get_category_fields(
        session=session,
        category_id=item.category_id,
    )

    if "identifiers" in data.fields_set:
        identifiers = data.identifiers or []

        item.identifiers.clear()
        session.flush()

        for identifier_input in identifiers:
            identifier_value = (
                identifier_input.identifier_value.strip()
            )

            if not identifier_value:
                raise ValueError(
                    "Az azonosító értéke nem lehet üres."
                )

            item.identifiers.append(
                ItemIdentifier(
                    identifier_type=identifier_input.identifier_type,
                    identifier_value=identifier_value,
                    provider_code=identifier_input.provider_code,
                    is_primary=identifier_input.is_primary,
                )
            )

    if "field_values" in data.fields_set:
        field_values = data.field_values or {}
        unknown_field_keys = (
            set(field_values) - set(category_fields)
        )

        if unknown_field_keys:
            unknown = ", ".join(sorted(unknown_field_keys))

            raise ValueError(
                f"Ismeretlen kategóriamezők: {unknown}"
            )

        missing_required_fields = [
            category_field.field_key
            for category_field in category_fields.values()
            if category_field.is_required
            and (
                category_field.field_key
                not in data.field_values
                or data.field_values[
                    category_field.field_key
                ] is None
            )
        ]

        if missing_required_fields:
            missing = ", ".join(
                sorted(missing_required_fields)
            )

            raise ValueError(
                f"Hiányzó kötelező mezők: {missing}"
            )

        item.field_values.clear()
        session.flush()

        for field_key, value in field_values.items():
            if value is None:
                continue

            item.field_values.append(
                _build_field_value(
                    session=session,
                    item=item,
                    category_field=category_fields[field_key],
                    value=value,
                )
            )

    session.flush()

    return item


@dataclass(slots=True)
class ItemImageCreateInput:
    stored_filename: str
    mime_type: str
    file_size: int
    width: int | None = None
    height: int | None = None
    original_filename: str | None = None
    caption: str | None = None
    sort_order: int = 0
    is_primary: bool | None = None


def create_item_image(
    session: Session,
    item: CollectionItem,
    data: ItemImageCreateInput,
) -> ItemImage:
    """
    Új képrekord létrehozása egy gyűjteményi elemhez.

    A hívó kezeli a commitot vagy rollbacket.
    """
    if item.id is None:
        raise ValueError(
            "A gyűjteményi elem még nincs elmentve."
        )

    stored_filename = data.stored_filename.strip()

    if not stored_filename:
        raise ValueError(
            "A tárolt képfájlnév nem lehet üres."
        )

    mime_type = data.mime_type.strip()

    if not mime_type:
        raise ValueError(
            "A kép MIME-típusa nem lehet üres."
        )

    if data.file_size < 0:
        raise ValueError(
            "A képfájl mérete nem lehet negatív."
        )

    if data.width is not None and data.width <= 0:
        raise ValueError(
            "A kép szélességének pozitívnak kell lennie."
        )

    if data.height is not None and data.height <= 0:
        raise ValueError(
            "A kép magasságának pozitívnak kell lennie."
        )

    if data.sort_order < 0:
        raise ValueError(
            "A kép rendezési sorrendje nem lehet negatív."
        )

    caption = (
        data.caption.strip()
        if data.caption
        else None
    )

    if caption == "":
        caption = None

    if caption is not None and len(caption) > 200:
        raise ValueError(
            "A képaláírás legfeljebb 200 karakter lehet."
        )

    original_filename = (
        data.original_filename.strip()
        if data.original_filename
        else None
    )

    if original_filename == "":
        original_filename = None

    active_image_count = session.scalar(
        select(ItemImage)
        .where(
            ItemImage.item_id == item.id,
            ItemImage.is_active.is_(True),
        )
        .with_only_columns(
            ItemImage.id
        )
        .limit(1)
    )

    should_be_primary = (
        data.is_primary
        if data.is_primary is not None
        else active_image_count is None
    )

    if should_be_primary:
        existing_primary_images = session.scalars(
            select(ItemImage).where(
                ItemImage.item_id == item.id,
                ItemImage.is_primary.is_(True),
            )
        ).all()

        for image in existing_primary_images:
            image.is_primary = False

    image = ItemImage(
        item=item,
        original_filename=original_filename,
        caption=caption,
        stored_filename=stored_filename,
        mime_type=mime_type,
        file_size=data.file_size,
        width=data.width,
        height=data.height,
        sort_order=data.sort_order,
        is_primary=should_be_primary,
        is_active=True,
    )

    session.add(image)
    session.flush()

    return image


def list_item_images(
    session: Session,
    item: CollectionItem,
    *,
    include_inactive: bool = False,
) -> list[ItemImage]:
    """
    Egy gyűjteményi elem képeinek listázása.
    """
    statement = (
        select(ItemImage)
        .where(
            ItemImage.item_id == item.id
        )
        .order_by(
            ItemImage.is_primary.desc(),
            ItemImage.sort_order,
            ItemImage.id,
        )
    )

    if not include_inactive:
        statement = statement.where(
            ItemImage.is_active.is_(True)
        )

    return list(
        session.scalars(statement).all()
    )


def get_item_image_by_public_id(
    session: Session,
    public_id: str,
) -> ItemImage | None:
    """
    Képrekord lekérése public ID alapján.
    """
    normalized_public_id = public_id.strip()

    if not normalized_public_id:
        return None

    return session.scalar(
        select(ItemImage).where(
            ItemImage.public_id
            == normalized_public_id
        )
    )


def set_primary_item_image(
    session: Session,
    image: ItemImage,
) -> ItemImage:
    """
    A megadott képet elsődlegessé teszi.
    """
    if not image.is_active:
        raise ValueError(
            "Inaktív kép nem lehet elsődleges."
        )

    images = session.scalars(
        select(ItemImage).where(
            ItemImage.item_id == image.item_id
        )
    ).all()

    for current_image in images:
        current_image.is_primary = (
            current_image.id == image.id
        )

    session.flush()

    return image


def delete_item_image(
    session: Session,
    image: ItemImage,
) -> None:
    """
    Képrekord törlése.

    A fájlrendszerben lévő kép törlését a hívó kezeli.
    """
    item_id = image.item_id
    was_primary = image.is_primary

    session.delete(image)
    session.flush()

    if not was_primary:
        return

    replacement = session.scalar(
        select(ItemImage)
        .where(
            ItemImage.item_id == item_id,
            ItemImage.is_active.is_(True),
        )
        .order_by(
            ItemImage.sort_order,
            ItemImage.id,
        )
        .limit(1)
    )

    if replacement is not None:
        replacement.is_primary = True

    session.flush()
