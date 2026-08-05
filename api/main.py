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

from app.models import LegacyBookMigration
from app.core.database import get_db_session
from app.services import (
    get_book_by_legacy_id,
    list_books,
    list_latest_books,
    soft_delete_book_by_legacy_id,
    resolve_storage_location_from_legacy_id,
    update_book_by_legacy_id,
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
def scan(req: ScanRequest):
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

    places = db.get_places()

    selected_place = next(
        (
            place
            for place in places
            if place["id"] == req.location_id
        ),
        None
    )

    if not selected_place:
        return {
            "status": "error",
            "message": "A kiválasztott tárhely nem található."
        }

    borrowed_to = (
        req.borrower.strip()
        if req.borrower
        else None
    )

    if (
        selected_place["room"] == "Kölcsönadva"
        and not borrowed_to
    ):
        return {
            "status": "error",
            "message": "Add meg, kinél van a könyv."
        }

    if selected_place["room"] != "Kölcsönadva":
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
        book_id = db.insert_book(
            isbn=clean_isbn,
            title=metadata.get("title") or clean_isbn,
            author=metadata.get("author"),
            publisher=metadata.get("publisher"),
            publish_year=metadata.get("year"),
            location_id=req.location_id,
            borrowed_to=borrowed_to
        )

        return {
            "status": "created",
            "id": book_id,
            "data": metadata
        }

    except Exception as error:
        print("BOOK INSERT ERROR:", error)

        return {
            "status": "error",
            "message": str(error)
        }

@app.post("/books/manual")
def add_manual_book(req: ManualBookRequest):
    identifier = req.identifier.strip()
    title = req.title.strip()

    if not identifier:
        return {
            "status": "error",
            "message": "Adj meg valamilyen azonosítót vagy jelzetet."
        }

    if not title:
        return {
            "status": "error",
            "message": "A cím nem lehet üres."
        }

    places = db.get_places()

    selected_place = next(
        (
            place
            for place in places
            if place["id"] == req.location_id
        ),
        None
    )

    if not selected_place:
        return {
            "status": "error",
            "message": "A kiválasztott tárhely nem található."
        }

    try:
        book_id = db.insert_book(
            isbn=identifier,
            title=title,
            author=req.author.strip() if req.author else None,
            publisher=req.publisher.strip() if req.publisher else None,
            publish_year=(
                req.publish_year.strip()
                if req.publish_year
                else None
            ),
            location_id=req.location_id,
            borrowed_to=None
        )

        return {
            "status": "created",
            "id": book_id
        }

    except Exception as error:
        print("MANUAL BOOK INSERT ERROR:", error)

        return {
            "status": "error",
            "message": str(error)
        }

@app.post("/books/manual-isbn")
def add_manual_isbn_book(req: ManualIsbnBookRequest):
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
            )
        }

    if not title:
        return {
            "status": "error",
            "message": "A cím nem lehet üres."
        }

    places = db.get_places()

    selected_place = next(
        (
            place
            for place in places
            if place["id"] == req.location_id
        ),
        None
    )

    if not selected_place:
        return {
            "status": "error",
            "message": "A kiválasztott tárhely nem található."
        }

    borrower = (
        req.borrower.strip()
        if req.borrower
        else None
    )

    try:
        book_id = db.insert_book(
            isbn=clean_isbn,
            title=title,
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
            publish_year=(
                req.publish_year.strip()
                if req.publish_year
                else None
            ),
            location_id=req.location_id,
            borrowed_to=borrower
        )

        return {
            "status": "created",
            "id": book_id
        }

    except Exception as error:
        print(
            "MANUAL ISBN INSERT ERROR:",
            error
        )

        return {
            "status": "error",
            "message": str(error)
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
def export_books_csv():
    rows = db.export_books()

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

    for row in rows:
        book_id = row[0]
        isbn = row[1]
        title = row[2]
        author = row[3]
        publish_year = row[4]
        publisher = row[5]
        created = row[6]
        updated = row[7]
        borrowed_to = row[8]
        room = row[9]
        shelf = row[10]
        slot = row[11]

        location_parts = [
            str(value)
            for value in (room, shelf)
            if value not in (None, "", "-")
        ]

        if slot is not None:
            location_parts.append(f"Tárhely {slot}")

        full_location = " / ".join(location_parts)

        writer.writerow([
            book_id,
            isbn or "",
            title or "",
            author or "",
            publish_year or "",
            publisher or "",
            created.isoformat(sep=" ") if created else "",
            updated.isoformat(sep=" ") if updated else "",
            borrowed_to or "",
            room or "",
            shelf or "",
            slot if slot is not None else "",
            full_location
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
