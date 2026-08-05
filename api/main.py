import csv
import io
from datetime import datetime

from fastapi.responses import StreamingResponse
from pathlib import Path

from fastapi import Depends, FastAPI
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import db
from metadata import fetch_book

from app.api.routers.auth import router as auth_router
from app.api.routers.items import router as items_router

from app.models import (
    Category,
    Household,
    LegacyBookMigration,
)
from app.core.database import get_db_session
from app.services import (
    get_book_by_legacy_id,
    update_book_borrow_state,
    list_books,
    list_latest_books,
    soft_delete_book_by_legacy_id,
    resolve_storage_location_from_legacy_id,
    update_book_by_legacy_id,
    create_manual_book,
    list_all_books_for_export,
)

app = FastAPI(title="Family Collection API")

app.include_router(auth_router)
app.include_router(items_router)

app.mount(
    "/ui",
    StaticFiles(directory=str(Path(__file__).parent.parent / "ui")),
    name="ui"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScanRequest(BaseModel):

    isbn: str

    location_id: int

    borrower: str | None = None

class EditBookRequest(BaseModel):
    isbn: str
    title: str
    author: str | None = None
    publisher: str | None = None
    publish_year: str | None = None
    location_id: int
    borrower: str | None = None

class ManualBookRequest(BaseModel):
    identifier: str
    title: str
    author: str | None = None
    publisher: str | None = None
    publish_year: str | None = None
    location_id: int

class ManualIsbnBookRequest(BaseModel):
    isbn: str
    title: str
    author: str | None = None
    publisher: str | None = None
    publish_year: str | None = None
    location_id: int
    borrower: str | None = None

@app.get("/places")
def places():

    return db.get_places()

@app.post("/scan")
def scan(
    req: ScanRequest,
    session: Session = Depends(get_db_session),
):
    clean_isbn = (
        req.isbn
        .replace("-", "")
        .replace(" ", "")
        .strip()
    )

    if not clean_isbn:
        return {
            "status": "error",
            "message": "Az ISBN nincs megadva."
        }

    if (
        not clean_isbn.isdigit()
        or len(clean_isbn) not in (10, 13)
    ):
        return {
            "status": "error",
            "message": "Érvénytelen ISBN."
        }

    try:
        household = session.scalar(
            select(Household).where(
                Household.is_active.is_(True)
            )
        )

        if household is None:
            return {
                "status": "error",
                "message": "Nincs aktív háztartás.",
            }

        target_location = (
            resolve_storage_location_from_legacy_id(
                session=session,
                household_id=household.id,
                legacy_location_id=req.location_id,
            )
        )

        if target_location is None:
            return {
                "status": "error",
                "message": (
                    "A kiválasztott tárhely nem található."
                ),
            }

    except Exception as error:
        print("SCAN LOCATION ERROR:", error)

        return {
            "status": "error",
            "message": str(error),
        }

    borrowed_to = (
        req.borrower.strip()
        if req.borrower
        else None
    )

    if borrowed_to == "":
        borrowed_to = None

    shelf_location = target_location.parent

    room_location = (
        shelf_location.parent
        if shelf_location is not None
        else None
    )

    if shelf_location is None or room_location is None:
        return {
            "status": "error",
            "message": (
                "A kiválasztott tárhely hierarchiája hiányos."
            ),
        }

    is_borrowed_location = (
        room_location.name.strip().casefold()
        == "Kölcsönadva".casefold()
    )

    if is_borrowed_location and borrowed_to is None:
        return {
            "status": "error",
            "message": "Add meg, kinél van a könyv.",
        }

    if not is_borrowed_location:
        borrowed_to = None

    metadata = fetch_book(clean_isbn)

    metadata_title = str(
        metadata.get("title") or ""
    ).strip()

    if (
        not metadata_title
        or metadata_title == clean_isbn
    ):
        return {
            "status": "metadata_missing",
            "isbn": clean_isbn,
            "location_id": req.location_id,
            "borrower": borrowed_to,
            "message": (
                "Nem találtam használható könyvadatokat "
                "ehhez az ISBN-hez."
            )
        }

    try:
        category = session.scalar(
            select(Category).where(
                Category.slug == "book",
                Category.is_active.is_(True),
            )
        )

        if category is None:
            return {
                "status": "error",
                "message": (
                    "Az aktív book kategória nem található."
                ),
            }

        metadata_year = metadata.get("year")
        publish_year: int | None = None

        if metadata_year is not None:
            metadata_year_text = str(
                metadata_year
            ).strip()

            if (
                metadata_year_text.isdigit()
                and len(metadata_year_text) == 4
            ):
                publish_year = int(
                    metadata_year_text
                )

        legacy_book_id = create_manual_book(
            session=session,
            household_id=household.id,
            category_id=category.id,
            identifier=clean_isbn,
            title=(
                metadata.get("title")
                or clean_isbn
            ),
            author=metadata.get("author"),
            publisher=metadata.get("publisher"),
            publish_year=publish_year,
            legacy_location_id=req.location_id,
            storage_location_id=target_location.id,
        )

        if borrowed_to is not None:
            updated = update_book_borrow_state(
                session=session,
                legacy_book_id=legacy_book_id,
                borrower=borrowed_to,
            )

            if not updated:
                session.rollback()

                return {
                    "status": "error",
                    "message": (
                        "A létrehozott könyv kölcsönadási "
                        "állapota nem frissíthető."
                    ),
                }

        session.commit()

        return {
            "status": "created",
            "id": legacy_book_id,
            "data": metadata,
        }

    except ValueError as error:
        session.rollback()

        return {
            "status": "error",
            "message": str(error),
        }

    except Exception as error:
        session.rollback()

        print("BOOK INSERT ERROR:", error)

        return {
            "status": "error",
            "message": str(error),
        }


@app.post("/books/manual")
def add_manual_book(
    req: ManualBookRequest,
    session: Session = Depends(get_db_session),
):
    identifier = req.identifier.strip()
    title = req.title.strip()

    if not identifier:
        return {
            "status": "error",
            "message": (
                "Adj meg valamilyen azonosítót vagy jelzetet."
            ),
        }

    if not title:
        return {
            "status": "error",
            "message": "A cím nem lehet üres.",
        }

    publish_year: int | None = None

    if req.publish_year:
        publish_year_text = req.publish_year.strip()

        if publish_year_text:
            if (
                not publish_year_text.isdigit()
                or len(publish_year_text) != 4
            ):
                return {
                    "status": "error",
                    "message": (
                        "A kiadás éve négyjegyű szám legyen."
                    ),
                }

            publish_year = int(publish_year_text)

            if publish_year < 1000 or publish_year > 9999:
                return {
                    "status": "error",
                    "message": (
                        "A kiadás éve 1000 és 9999 közé essen."
                    ),
                }

    try:
        household = session.scalar(
            select(Household).where(
                Household.is_active.is_(True)
            )
        )

        if household is None:
            return {
                "status": "error",
                "message": "Nincs aktív háztartás.",
            }

        category = session.scalar(
            select(Category).where(
                Category.slug == "book",
                Category.is_active.is_(True),
            )
        )

        if category is None:
            return {
                "status": "error",
                "message": (
                    "Az aktív book kategória nem található."
                ),
            }

        target_location = (
            resolve_storage_location_from_legacy_id(
                session=session,
                household_id=household.id,
                legacy_location_id=req.location_id,
            )
        )

        if target_location is None:
            return {
                "status": "error",
                "message": (
                    "A kiválasztott tárhely nem található."
                ),
            }

        legacy_book_id = create_manual_book(
            session=session,
            household_id=household.id,
            category_id=category.id,
            identifier=identifier,
            title=title,
            author=req.author,
            publisher=req.publisher,
            publish_year=publish_year,
            legacy_location_id=req.location_id,
            storage_location_id=target_location.id,
        )

        session.commit()

        return {
            "status": "created",
            "id": legacy_book_id,
        }

    except ValueError as error:
        session.rollback()

        return {
            "status": "error",
            "message": str(error),
        }

    except Exception as error:
        session.rollback()

        print("MANUAL BOOK INSERT ERROR:", error)

        return {
            "status": "error",
            "message": str(error),
        }


@app.post("/books/manual-isbn")
def add_manual_isbn_book(
    req: ManualIsbnBookRequest,
    session: Session = Depends(get_db_session),
):
    clean_isbn = (
        req.isbn
        .replace("-", "")
        .replace(" ", "")
        .strip()
    )

    title = req.title.strip()

    if (
        not clean_isbn.isdigit()
        or len(clean_isbn) not in (10, 13)
    ):
        return {
            "status": "error",
            "message": (
                "Az ISBN 10 vagy 13 számjegyből álljon."
            ),
        }

    if not title:
        return {
            "status": "error",
            "message": "A cím nem lehet üres.",
        }

    publish_year: int | None = None

    if req.publish_year:
        publish_year_text = req.publish_year.strip()

        if publish_year_text:
            if (
                not publish_year_text.isdigit()
                or len(publish_year_text) != 4
            ):
                return {
                    "status": "error",
                    "message": (
                        "A kiadás éve négyjegyű szám legyen."
                    ),
                }

            publish_year = int(publish_year_text)

            if publish_year < 1000 or publish_year > 9999:
                return {
                    "status": "error",
                    "message": (
                        "A kiadás éve 1000 és 9999 közé essen."
                    ),
                }

    borrower = (
        req.borrower.strip()
        if req.borrower
        else None
    )

    if borrower == "":
        borrower = None

    try:
        household = session.scalar(
            select(Household).where(
                Household.is_active.is_(True)
            )
        )

        if household is None:
            return {
                "status": "error",
                "message": "Nincs aktív háztartás.",
            }

        category = session.scalar(
            select(Category).where(
                Category.slug == "book",
                Category.is_active.is_(True),
            )
        )

        if category is None:
            return {
                "status": "error",
                "message": (
                    "Az aktív book kategória nem található."
                ),
            }

        target_location = (
            resolve_storage_location_from_legacy_id(
                session=session,
                household_id=household.id,
                legacy_location_id=req.location_id,
            )
        )

        if target_location is None:
            return {
                "status": "error",
                "message": (
                    "A kiválasztott tárhely nem található."
                ),
            }

        shelf_location = target_location.parent

        room_location = (
            shelf_location.parent
            if shelf_location is not None
            else None
        )

        if shelf_location is None or room_location is None:
            return {
                "status": "error",
                "message": (
                    "A kiválasztott tárhely hierarchiája hiányos."
                ),
            }

        is_borrowed_location = (
            room_location.name.strip().casefold()
            == "Kölcsönadva".casefold()
        )

        if is_borrowed_location and borrower is None:
            return {
                "status": "error",
                "message": (
                    "Kölcsönadásnál add meg, "
                    "kinél van a könyv."
                ),
            }

        if not is_borrowed_location:
            borrower = None

        legacy_book_id = create_manual_book(
            session=session,
            household_id=household.id,
            category_id=category.id,
            identifier=clean_isbn,
            title=title,
            author=req.author,
            publisher=req.publisher,
            publish_year=publish_year,
            legacy_location_id=req.location_id,
            storage_location_id=target_location.id,
        )

        if borrower is not None:
            updated = update_book_borrow_state(
                session=session,
                legacy_book_id=legacy_book_id,
                borrower=borrower,
            )

            if not updated:
                session.rollback()

                return {
                    "status": "error",
                    "message": (
                        "A létrehozott könyv kölcsönadási "
                        "állapota nem frissíthető."
                    ),
                }

        session.commit()

        return {
            "status": "created",
            "id": legacy_book_id,
        }

    except ValueError as error:
        session.rollback()

        return {
            "status": "error",
            "message": str(error),
        }

    except Exception as error:
        session.rollback()

        print(
            "MANUAL ISBN INSERT ERROR:",
            error,
        )

        return {
            "status": "error",
            "message": str(error),
        }


@app.get("/books/latest")
def latest(
    session: Session = Depends(get_db_session),
):
    records = list_latest_books(
        session=session,
        limit=20,
    )

    return [
        {
            "id": record.id,
            "title": record.title,
            "author": record.author,
            "isbn": record.isbn,
            "publisher": record.publisher,
            "year": record.year,
            "added": (
                record.added.isoformat()
                if record.added
                else None
            ),
            "room": record.room,
            "shelf": record.shelf,
            "slot": record.slot,
            "borrower": record.borrower,
        }
        for record in records
    ]


@app.get("/books/all")
def all_books(
    page: int = 1,
    page_size: int = 50,
    search: str = "",
    session: Session = Depends(get_db_session),
):
    normalized_page = max(1, page)
    normalized_page_size = max(
        1,
        min(page_size, 100),
    )

    result = list_books(
        session=session,
        page=normalized_page,
        page_size=normalized_page_size,
        search=search,
    )

    total_pages = (
        (
            result.total
            + result.page_size
            - 1
        )
        // result.page_size
        if result.total > 0
        else 1
    )

    return {
        "page": result.page,
        "page_size": result.page_size,
        "total": result.total,
        "total_pages": total_pages,
        "search": search,
        "books": [
            {
                "id": record.id,
                "isbn": record.isbn,
                "title": record.title,
                "author": record.author,
                "publisher": record.publisher,
                "year": record.year,
                "added": (
                    record.added.isoformat()
                    if record.added
                    else None
                ),
                "room": record.room,
                "shelf": record.shelf,
                "slot": record.slot,
                "borrower": record.borrower,
            }
            for record in result.records
        ],
    }


@app.delete("/books/{book_id}")
def delete_book(
    book_id: int,
    session: Session = Depends(get_db_session),
):
    try:
        deleted = soft_delete_book_by_legacy_id(
            session=session,
            legacy_book_id=book_id,
        )

        if not deleted:
            return {
                "status": "not_found",
                "message": "A könyv nem található.",
            }

        session.commit()

        return {
            "status": "deleted",
            "id": book_id,
        }

    except Exception as error:
        session.rollback()

        print("DELETE BOOK ERROR:", error)

        return {
            "status": "error",
            "message": str(error),
        }


@app.get("/books/export.csv")
def export_books_csv(
    session: Session = Depends(get_db_session),
):
    records = list_all_books_for_export(
        session=session
    )

    output = io.StringIO()

    # Excel számára UTF-8 BOM, így az ékezeteket is jól kezeli.
    output.write("\ufeff")

    writer = csv.writer(
        output,
        delimiter=";",
        quoting=csv.QUOTE_MINIMAL,
        lineterminator="\n"
    )

    writer.writerow([
        "Könyv ID",
        "ISBN",
        "Cím",
        "Szerző",
        "Kiadás éve",
        "Kiadó",
        "Felvitel dátuma",
        "Utolsó módosítás",
        "Kölcsönző",
        "Helyiség",
        "Polc",
        "Tárhely",
        "Teljes tárhely"
    ])

    for record in records:
        location_parts = [
            str(value)
            for value in (
                record.room,
                record.shelf,
            )
            if value not in (
                None,
                "",
                "-",
            )
        ]

        if record.slot is not None:
            location_parts.append(
                f"Tárhely {record.slot}"
            )

        full_location = " / ".join(
            location_parts
        )

        writer.writerow([
            record.id,
            record.isbn or "",
            record.title or "",
            record.author or "",
            record.year or "",
            record.publisher or "",
            (
                record.added.isoformat(
                    sep=" "
                )
                if record.added
                else ""
            ),
            (
                record.updated.isoformat(
                    sep=" "
                )
                if record.updated
                else ""
            ),
            record.borrower or "",
            record.room or "",
            record.shelf or "",
            (
                record.slot
                if record.slot is not None
                else ""
            ),
            full_location,
        ])

    csv_content = output.getvalue()
    output.close()

    filename = (
        "familycollection_"
        + datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        + ".csv"
    )

    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition":
                f'attachment; filename="{filename}"'
        }
    )


@app.get("/books/{book_id}")
def get_book(
    book_id: int,
    session: Session = Depends(get_db_session),
):
    try:
        record = get_book_by_legacy_id(
            session=session,
            legacy_book_id=book_id,
        )

        if record is None:
            return {
                "status": "not_found",
                "message": "A könyv nem található.",
            }

        return {
            "id": record.id,
            "isbn": record.isbn,
            "title": record.title,
            "author": record.author,
            "publisher": record.publisher,
            "year": record.year,
            "created": (
                record.added.isoformat()
                if record.added
                else None
            ),
            "location_id": record.location_id,
            "borrower": record.borrower,
            "room": record.room,
            "shelf": record.shelf,
            "slot": record.slot,
        }

    except Exception as error:
        print("GET BOOK ERROR:", error)

        return {
            "status": "error",
            "message": str(error),
        }


@app.put("/books/{book_id}")
def update_book(
    book_id: int,
    req: EditBookRequest,
    session: Session = Depends(get_db_session),
):
    clean_isbn = (
        req.isbn
        .replace("-", "")
        .replace(" ", "")
        .strip()
    )

    if not clean_isbn:
        return {
            "status": "error",
            "message": "Az ISBN nem lehet üres.",
        }

    if (
        not clean_isbn.isdigit()
        or len(clean_isbn) not in (10, 13)
    ):
        return {
            "status": "error",
            "message": (
                "Az ISBN 10 vagy 13 számjegyből álljon."
            ),
        }

    cleaned_title = req.title.strip()

    if not cleaned_title:
        return {
            "status": "error",
            "message": "A cím nem lehet üres.",
        }

    cleaned_publish_year = (
        req.publish_year.strip()
        if req.publish_year
        else None
    )

    publish_year: int | None = None

    if cleaned_publish_year:
        if (
            not cleaned_publish_year.isdigit()
            or len(cleaned_publish_year) != 4
        ):
            return {
                "status": "error",
                "message": (
                    "A kiadás éve négyjegyű szám legyen."
                ),
            }

        publish_year = int(cleaned_publish_year)

        if publish_year < 1000 or publish_year > 9999:
            return {
                "status": "error",
                "message": (
                    "A kiadás éve 1000 és 9999 közé essen."
                ),
            }

    borrower = (
        req.borrower.strip()
        if req.borrower
        else None
    )

    if borrower == "":
        borrower = None

    try:
        migration = session.scalar(
            select(LegacyBookMigration).where(
                LegacyBookMigration.legacy_book_id
                == book_id
            )
        )

        if (
            migration is None
            or migration.collection_item is None
            or not migration.collection_item.is_active
        ):
            return {
                "status": "not_found",
                "message": "A könyv nem található.",
            }

        household_id = (
            migration.collection_item.household_id
        )

        target_location = (
            resolve_storage_location_from_legacy_id(
                session=session,
                household_id=household_id,
                legacy_location_id=req.location_id,
            )
        )

        if target_location is None:
            return {
                "status": "error",
                "message": (
                    "A kiválasztott régi tárhelyhez "
                    "nem található új tárhelyrekord."
                ),
            }

        shelf_location = target_location.parent

        room_location = (
            shelf_location.parent
            if shelf_location is not None
            else None
        )

        if shelf_location is None or room_location is None:
            return {
                "status": "error",
                "message": (
                    "A kiválasztott tárhely hierarchiája hiányos."
                ),
            }

        is_borrowed_location = (
            room_location.name.strip().casefold()
            == "Kölcsönadva".casefold()
        )

        if is_borrowed_location and borrower is None:
            return {
                "status": "error",
                "message": (
                    "Kölcsönadásnál add meg, "
                    "kinél van a könyv."
                ),
            }

        if not is_borrowed_location:
            borrower = None

        identifier_type = (
            "isbn10"
            if len(clean_isbn) == 10
            else "isbn13"
        )

        updated = update_book_by_legacy_id(
            session=session,
            legacy_book_id=book_id,
            title=cleaned_title,
            identifier_type=identifier_type,
            identifier_value=clean_isbn,
            author=(
                req.author.strip()
                if req.author
                else None
            ),
            publisher=(
                req.publisher.strip()
                if req.publisher
                else None
            ),
            publish_year=publish_year,
            storage_location_id=target_location.id,
            borrower=borrower,
        )

        if not updated:
            session.rollback()

            return {
                "status": "not_found",
                "message": "A könyv nem található.",
            }

        session.commit()

        return {
            "status": "updated",
            "id": book_id,
        }

    except ValueError as error:
        session.rollback()

        return {
            "status": "error",
            "message": str(error),
        }

    except Exception as error:
        session.rollback()

        print("UPDATE BOOK ERROR:", error)

        return {
            "status": "error",
            "message": str(error),
        }
