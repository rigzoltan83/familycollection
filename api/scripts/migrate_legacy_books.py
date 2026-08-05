"""
A régi books és locations táblák könyveinek migrálása
az új CollectionItem adatmodellbe.

Példák:

Ellenőrző futás, adatmentés nélkül:

    python scripts/migrate_legacy_books.py --dry-run

Az első 10 könyv ellenőrzése:

    python scripts/migrate_legacy_books.py \
        --dry-run \
        --limit 10

Tényleges migráció:

    python scripts/migrate_legacy_books.py --apply

Tényleges migráció úgy, hogy egy hibás rekord után is folytassa:

    python scripts/migrate_legacy_books.py \
        --apply \
        --continue-on-error
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from app.core.database import SessionLocal
from app.models import Category, Household
from app.services import (
    LegacyBookBatchResult,
    load_legacy_book_sources_from_database,
    migrate_legacy_books_batch,
)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "A régi books rekordok migrálása az új "
            "CollectionItem rendszerbe."
        )
    )

    execution_mode = parser.add_mutually_exclusive_group(
        required=True
    )

    execution_mode.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Végrehajtja a teljes migrációs logikát, "
            "majd visszagörget minden módosítást."
        ),
    )

    execution_mode.add_argument(
        "--apply",
        action="store_true",
        help=(
            "Végrehajtja és commitolja a migrációt."
        ),
    )

    parser.add_argument(
        "--household-id",
        type=int,
        default=None,
        help=(
            "Célháztartás belső adatbázis-azonosítója. "
            "Ha nincs megadva, az egyetlen aktív háztartást "
            "választja ki."
        ),
    )

    parser.add_argument(
        "--category-id",
        type=int,
        default=None,
        help=(
            "A book kategória belső adatbázis-azonosítója. "
            "Ha nincs megadva, az aktív book kategóriát "
            "választja ki."
        ),
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help=(
            "Csak az első megadott számú legacy könyvet "
            "dolgozza fel."
        ),
    )

    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help=(
            "Hibás rekord esetén folytatja a következő könyvvel. "
            "A hibákat a futás végén kilistázza."
        ),
    )

    arguments = parser.parse_args()

    if arguments.household_id is not None:
        if arguments.household_id <= 0:
            parser.error(
                "A --household-id csak pozitív egész szám lehet."
            )

    if arguments.category_id is not None:
        if arguments.category_id <= 0:
            parser.error(
                "A --category-id csak pozitív egész szám lehet."
            )

    if arguments.limit is not None:
        if arguments.limit <= 0:
            parser.error(
                "A --limit csak pozitív egész szám lehet."
            )

    return arguments


def resolve_household(
    session: Session,
    household_id: int | None,
) -> Household:
    if household_id is not None:
        household = session.get(
            Household,
            household_id,
        )

        if household is None:
            raise ValueError(
                f"A megadott háztartás nem létezik: "
                f"id={household_id}"
            )

        if not household.is_active:
            raise ValueError(
                f"A megadott háztartás nem aktív: "
                f"id={household_id}"
            )

        return household

    households = session.scalars(
        select(Household)
        .where(Household.is_active.is_(True))
        .order_by(Household.id)
    ).all()

    if not households:
        raise ValueError(
            "Nem található aktív háztartás."
        )

    if len(households) > 1:
        ids = ", ".join(
            str(household.id)
            for household in households
        )

        raise ValueError(
            "Több aktív háztartás található. "
            "Add meg a --household-id kapcsolót. "
            f"Aktív azonosítók: {ids}"
        )

    return households[0]


def resolve_book_category(
    session: Session,
    category_id: int | None,
) -> Category:
    if category_id is not None:
        category = session.get(
            Category,
            category_id,
        )

        if category is None:
            raise ValueError(
                f"A megadott kategória nem létezik: "
                f"id={category_id}"
            )

        if not category.is_active:
            raise ValueError(
                f"A megadott kategória nem aktív: "
                f"id={category_id}"
            )

        if category.slug != "book":
            raise ValueError(
                "A megadott kategória nem a book kategória: "
                f"id={category_id}, slug={category.slug}"
            )

        return category

    categories = session.scalars(
        select(Category)
        .where(
            Category.slug == "book",
            Category.is_active.is_(True),
        )
        .order_by(Category.id)
    ).all()

    if not categories:
        raise ValueError(
            "Nem található aktív book kategória."
        )

    if len(categories) > 1:
        ids = ", ".join(
            str(category.id)
            for category in categories
        )

        raise ValueError(
            "Több aktív book kategória található. "
            "Add meg a --category-id kapcsolót. "
            f"Aktív azonosítók: {ids}"
        )

    return categories[0]


def print_result(
    result: LegacyBookBatchResult,
) -> None:
    print()
    print("Migrációs összesítés")
    print("====================")
    print(
        f"Forrásrekordok:       "
        f"{result.total_source_records}"
    )
    print(
        f"Újonnan létrehozva:   "
        f"{result.created_count}"
    )
    print(
        f"Korábban migrálva:    "
        f"{result.skipped_count}"
    )
    print(
        f"Hiba nélkül migrálva: "
        f"{result.migrated_count}"
    )
    print(
        f"Figyelmeztetéssel:     "
        f"{result.warning_count}"
    )
    print(
        f"Hibás rekordok:        "
        f"{result.error_count}"
    )

    if result.errors:
        print()
        print("Hibák")
        print("=====")

        for error in result.errors:
            print(
                f"books.id={error.legacy_book_id}: "
                f"{error.message}"
            )


def run_migration(
    arguments: argparse.Namespace,
) -> int:
    session = SessionLocal()

    try:
        household = resolve_household(
            session=session,
            household_id=arguments.household_id,
        )

        category = resolve_book_category(
            session=session,
            category_id=arguments.category_id,
        )

        source_records = (
            load_legacy_book_sources_from_database(
                session=session
            )
        )

        if arguments.limit is not None:
            source_records = source_records[
                : arguments.limit
            ]

        mode_name = (
            "DRY-RUN"
            if arguments.dry_run
            else "APPLY"
        )

        print(
            f"Futtatási mód: {mode_name}"
        )
        print(
            f"Háztartás: {household.name} "
            f"(id={household.id})"
        )
        print(
            f"Kategória: {category.name} "
            f"(id={category.id}, slug={category.slug})"
        )
        print(
            f"Feldolgozandó rekordok: "
            f"{len(source_records)}"
        )
        print(
            "Hibánál folytatás: "
            f"{'igen' if arguments.continue_on_error else 'nem'}"
        )

        result = migrate_legacy_books_batch(
            session=session,
            source_records=source_records,
            household_id=household.id,
            category_id=category.id,
            continue_on_error=(
                arguments.continue_on_error
            ),
        )

        print_result(result)

        if arguments.dry_run:
            session.rollback()

            print()
            print(
                "DRY-RUN kész: minden módosítás "
                "visszagörgetve."
            )

        else:
            if (
                result.error_count > 0
                and not arguments.continue_on_error
            ):
                session.rollback()

                print()
                print(
                    "A migráció hibák miatt "
                    "visszagörgetve."
                )

                return 1

            session.commit()

            print()
            print(
                "A migráció sikeresen commitolva."
            )

        if result.error_count > 0:
            return 2

        return 0

    except Exception as error:
        session.rollback()

        print(
            f"HIBA: {error}",
            file=sys.stderr,
        )

        return 1

    finally:
        session.close()


def main() -> int:
    arguments = parse_arguments()

    return run_migration(arguments)


if __name__ == "__main__":
    raise SystemExit(main())
