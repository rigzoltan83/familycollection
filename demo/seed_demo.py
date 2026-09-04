from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
API_DIR = PROJECT_DIR / "api"

sys.path.insert(0, str(API_DIR))

EXPECTED_DB = "familycollection_demo"

if os.environ.get("DB_NAME") != EXPECTED_DB:
    raise SystemExit(
        "REFUSED: demo seed may only run against "
        "familycollection_demo"
    )

from sqlalchemy import select, text

from app.core.database import SessionLocal
from app.core.ids import generate_public_id
from app.core.security import hash_password
from app.models import (
    Category,
    CategoryField,
    CollectionItem,
    Household,
    HouseholdMember,
    ItemFieldValue,
    ItemStorageAssignment,
    StorageLocation,
    User,
)


def main() -> None:
    session = SessionLocal()

    try:
        actual_db = session.execute(
            text("SELECT current_database()")
        ).scalar_one()

        if actual_db != EXPECTED_DB:
            raise RuntimeError(
                f"REFUSED: connected to {actual_db!r}, "
                f"expected {EXPECTED_DB!r}"
            )

        existing_items = session.scalar(
            select(CollectionItem.id).limit(1)
        )

        existing_users = session.scalar(
            select(User.id).limit(1)
        )

        existing_storage = session.scalar(
            select(StorageLocation.id).limit(1)
        )

        if any(
            value is not None
            for value in (
                existing_items,
                existing_users,
                existing_storage,
            )
        ):
            raise RuntimeError(
                "REFUSED: demo database already contains "
                "user/item/storage data."
            )

        household = session.scalar(
            select(Household).where(
                Household.slug == "default-household"
            )
        )

        if household is None:
            raise RuntimeError(
                "Default household not found."
            )

        household.name = "Demo Family Collection"

        user = User(
            email="demo@example.com",
            username="demo",
            password_hash=hash_password(
                "FamilyCollectionDemo2026!"
            ),
            display_name="Demo User",
            is_active=True,
            is_platform_admin=True,
            email_verified=True,
        )
        session.add(user)
        session.flush()

        session.add(
            HouseholdMember(
                household_id=household.id,
                user_id=user.id,
                role="owner",
                is_active=True,
            )
        )

        book_category = session.scalar(
            select(Category).where(
                Category.slug == "book",
                Category.is_system.is_(True),
            )
        )

        if book_category is None:
            raise RuntimeError(
                "System book category not found."
            )

        board_games = Category(
            household_id=household.id,
            name="Board Games",
            slug="board-games",
            description=(
                "Tabletop games in the demo collection."
            ),
            icon="dice",
            is_system=False,
            is_active=True,
            supports_barcode=False,
            metadata_lookup_type="manual",
            sort_order=20,
        )

        video_games = Category(
            household_id=household.id,
            name="Video Games",
            slug="video-games",
            description=(
                "Video games in the demo collection."
            ),
            icon="gamepad",
            is_system=False,
            is_active=True,
            supports_barcode=False,
            metadata_lookup_type="manual",
            sort_order=30,
        )

        session.add_all(
            [
                board_games,
                video_games,
            ]
        )
        session.flush()

        room_living = make_storage(
            session,
            household.id,
            None,
            "Living Room",
            "living-room",
            "room",
            10,
        )

        bookcase = make_storage(
            session,
            household.id,
            room_living.id,
            "Main Bookcase",
            "main-bookcase",
            "shelf",
            10,
        )

        shelf_a = make_storage(
            session,
            household.id,
            bookcase.id,
            "Shelf A",
            "shelf-a",
            "slot",
            10,
        )

        shelf_b = make_storage(
            session,
            household.id,
            bookcase.id,
            "Shelf B",
            "shelf-b",
            "slot",
            20,
        )

        room_study = make_storage(
            session,
            household.id,
            None,
            "Study",
            "study",
            "room",
            20,
        )

        media_cabinet = make_storage(
            session,
            household.id,
            room_study.id,
            "Media Cabinet",
            "media-cabinet",
            "cabinet",
            10,
        )

        drawer_1 = make_storage(
            session,
            household.id,
            media_cabinet.id,
            "Drawer 1",
            "drawer-1",
            "drawer",
            10,
        )

        game_room = make_storage(
            session,
            household.id,
            None,
            "Game Room",
            "game-room",
            "room",
            30,
        )

        game_shelf = make_storage(
            session,
            household.id,
            game_room.id,
            "Game Shelf",
            "game-shelf",
            "shelf",
            10,
        )

        book_fields = {
            field.field_key: field
            for field in session.scalars(
                select(CategoryField).where(
                    CategoryField.category_id
                    == book_category.id
                )
            ).all()
        }

        add_book(
            session,
            household.id,
            book_category,
            user,
            shelf_a,
            book_fields,
            title="The Clockmaker's Map",
            author="Elena Hart",
            publisher="Northbridge Press",
            year=2021,
            pages=352,
        )

        add_book(
            session,
            household.id,
            book_category,
            user,
            shelf_a,
            book_fields,
            title="Gardens Beyond the Moon",
            author="Mira Vale",
            publisher="Silver Fern Books",
            year=2019,
            pages=288,
        )

        add_book(
            session,
            household.id,
            book_category,
            user,
            shelf_b,
            book_fields,
            title="Practical Astronomy at Home",
            author="Daniel Mercer",
            publisher="Clear Sky Publishing",
            year=2024,
            pages=416,
        )

        for title, subtitle in (
            (
                "Rails & Rivers",
                "Build routes across a changing landscape",
            ),
            (
                "Kingdom of Glass",
                "Strategy among fragile alliances",
            ),
            (
                "Signal Station",
                "A cooperative deep-space communication game",
            ),
        ):
            add_simple_item(
                session,
                household.id,
                board_games,
                user,
                game_shelf,
                title,
                subtitle,
            )

        for title, subtitle in (
            (
                "Orbital Colony",
                "City building beyond Earth",
            ),
            (
                "Deep Signal",
                "Explore a mysterious transmission",
            ),
            (
                "Northern Circuit",
                "High-speed racing through frozen landscapes",
            ),
        ):
            add_simple_item(
                session,
                household.id,
                video_games,
                user,
                drawer_1,
                title,
                subtitle,
            )

        session.commit()

        print("Demo data created successfully.")
        print()
        print("Database: familycollection_demo")
        print("Username: demo")
        print("Password: FamilyCollectionDemo2026!")
        print()
        print("All collection data is synthetic.")

    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def make_storage(
    session,
    household_id: int,
    parent_id: int | None,
    name: str,
    slug: str,
    location_type: str,
    sort_order: int,
) -> StorageLocation:
    location = StorageLocation(
        public_id=generate_public_id(),
        household_id=household_id,
        parent_id=parent_id,
        name=name,
        slug=slug,
        location_type=location_type,
        description="Synthetic demo storage location.",
        sort_order=sort_order,
        is_active=True,
    )
    session.add(location)
    session.flush()
    return location


def assign_storage(
    session,
    item: CollectionItem,
    location: StorageLocation,
    user: User,
) -> None:
    assignment = ItemStorageAssignment(
        public_id=generate_public_id(),
        item_id=item.id,
        storage_location_id=location.id,
        is_active=True,
        moved_by_user_id=user.id,
        movement_reason="demo_seed",
        notes="Synthetic demo assignment.",
    )
    session.add(assignment)


def add_simple_item(
    session,
    household_id: int,
    category: Category,
    user: User,
    location: StorageLocation,
    title: str,
    subtitle: str,
) -> CollectionItem:
    item = CollectionItem(
        public_id=generate_public_id(),
        household_id=household_id,
        category_id=category.id,
        title=title,
        subtitle=subtitle,
        notes="Synthetic demonstration item.",
        status="active",
        is_active=True,
        created_by_user_id=user.id,
        updated_by_user_id=user.id,
    )
    session.add(item)
    session.flush()

    assign_storage(
        session,
        item,
        location,
        user,
    )

    return item


def add_book(
    session,
    household_id: int,
    category: Category,
    user: User,
    location: StorageLocation,
    fields: dict[str, CategoryField],
    *,
    title: str,
    author: str,
    publisher: str,
    year: int,
    pages: int,
) -> CollectionItem:
    item = add_simple_item(
        session,
        household_id,
        category,
        user,
        location,
        title,
        "Synthetic demo edition",
    )

    values = {
        "author": author,
        "publisher": publisher,
        "publish_year": year,
        "page_count": pages,
    }

    for key, value in values.items():
        field = fields.get(key)

        if field is None:
            raise RuntimeError(
                f"Book field not found: {key}"
            )

        field_value = ItemFieldValue(
            public_id=generate_public_id(),
            item_id=item.id,
            field_id=field.id,
        )

        if key in {
            "publish_year",
            "page_count",
        }:
            field_value.value_integer = int(value)
        else:
            field_value.value_text = str(value)

        session.add(field_value)

    return item


if __name__ == "__main__":
    main()
