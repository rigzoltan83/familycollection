import csv
import io
from datetime import datetime

from fastapi.responses import StreamingResponse
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import db
from metadata import fetch_book

app = FastAPI(title="Family Collection API")

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
def latest():

    rows = db.latest_books()

    return [
        {
            "id": r[0],
            "title": r[1],
            "author": r[2],
            "isbn": r[3],
            "publisher": r[4],
            "year": r[5],
            "added": r[6].isoformat() if r[6] else None,
            "room": r[7],
            "shelf": r[8],
            "slot": r[9],
            "borrower": r[10]
        }
        for r in rows
    ]

@app.get("/books/all")
def all_books(
    page: int = 1,
    page_size: int = 50,
    search: str = ""
):
    page = max(1, page)
    page_size = max(1, min(page_size, 100))

    rows, total = db.all_books(
        page=page,
        page_size=page_size,
        search=search
    )

    total_pages = (
        (total + page_size - 1) // page_size
        if total > 0
        else 1
    )

    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
        "search": search,
        "books": [
            {
                "id": r[0],
                "isbn": r[1],
                "title": r[2],
                "author": r[3],
                "publisher": r[4],
                "year": r[5],
                "added": (
                    r[6].isoformat()
                    if r[6]
                    else None
                ),
                "room": r[7],
                "shelf": r[8],
                "slot": r[9],
                "borrower": r[10]
            }
            for r in rows
        ]
    }

@app.delete("/books/{book_id}")
def delete_book(book_id: int):
    try:
        deleted = db.delete_book(book_id)

        if not deleted:
            return {
                "status": "not_found",
                "message": "A könyv nem található."
            }

        return {
            "status": "deleted",
            "id": book_id
        }

    except Exception as error:
        print("DELETE BOOK ERROR:", error)

        return {
            "status": "error",
            "message": str(error)
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
def get_book(book_id: int):
    try:
        row = db.get_book(book_id)

        if not row:
            return {
                "status": "not_found",
                "message": "A könyv nem található."
            }

        return {
            "id": row[0],
            "isbn": row[1],
            "title": row[2],
            "author": row[3],
            "publisher": row[4],
            "year": row[5],
            "created": row[6].isoformat() if row[6] else None,
            "location_id": row[7],
            "borrower": row[8],
            "room": row[9],
            "shelf": row[10],
            "slot": row[11]
        }

    except Exception as error:
        print("GET BOOK ERROR:", error)

        return {
            "status": "error",
            "message": str(error)
        }

@app.put("/books/{book_id}")
def update_book(book_id: int, req: EditBookRequest):
    clean_isbn = (
        req.isbn
        .replace("-", "")
        .replace(" ", "")
        .strip()
    )

    if not clean_isbn:
        return {
            "status": "error",
            "message": "Az ISBN nem lehet üres."
        }

    if not clean_isbn.isdigit() or len(clean_isbn) not in (10, 13):
        return {
            "status": "error",
            "message": "Az ISBN 10 vagy 13 számjegyből álljon."
        }

    if not req.title.strip():
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

    borrower = req.borrower.strip() if req.borrower else None

    if (
        selected_place["room"] == "Kölcsönadva"
        and not borrower
    ):
        return {
            "status": "error",
            "message": "Kölcsönadásnál add meg, kinél van a könyv."
        }

    if selected_place["room"] != "Kölcsönadva":
        borrower = None

    try:
        updated = db.update_book(
            book_id=book_id,
            isbn=clean_isbn,
            title=req.title.strip(),
            author=req.author.strip() if req.author else None,
            publisher=req.publisher.strip() if req.publisher else None,
            publish_year=(
                req.publish_year.strip()
                if req.publish_year
                else None
            ),
            location_id=req.location_id,
            borrowed_to=borrower
        )

        if not updated:
            return {
                "status": "not_found",
                "message": "A könyv nem található."
            }

        return {
            "status": "updated",
            "id": book_id
        }

    except Exception as error:
        print("UPDATE BOOK ERROR:", error)

        return {
            "status": "error",
            "message": str(error)
        }

