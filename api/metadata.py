import requests
import time

from settings import (
    ISBNDB_KEY,
    USE_ISBNDB,
    USE_OPENLIBRARY,
    USE_ISBNSEARCH,
)

def normalize_isbn(isbn: str):

    return isbn.replace("-", "").strip()

def fetch_isbndb(isbn):

    if not USE_ISBNDB:
        return None

    if not ISBNDB_KEY:
        return None

    isbn = normalize_isbn(isbn)

    headers = {
        "Authorization": ISBNDB_KEY,
        "Content-Type": "application/json"
    }

    try:

        r = requests.get(
            f"https://api2.isbndb.com/book/{isbn}",
            headers=headers,
            timeout=10
        )

        if r.status_code != 200:
            return None

        data = r.json()

        book = data.get("book")

        if not book:
            return None

        authors = book.get("authors") or []

        if isinstance(authors, str):
            authors = [authors]

        year = None

        if book.get("date_published"):
            year = str(book["date_published"])[:4]

        return {

            "isbn": book.get("isbn13")
                    or book.get("isbn")
                    or isbn,

            "title": book.get("title"),

            "author": ", ".join(authors),

            "publisher": book.get("publisher"),

            "year": year,

            "cover": book.get("image")

        }

    except Exception as e:

        print("ISBNdb:", e)

        return None

def fetch_openlibrary(isbn):

    if not USE_OPENLIBRARY:
        return None

    isbn = normalize_isbn(isbn)

    try:

        url = (
            "https://openlibrary.org/api/books"
            f"?bibkeys=ISBN:{isbn}"
            "&format=json"
            "&jscmd=data"
        )

        r = requests.get(url, timeout=8)

        data = r.json()

        book = data.get(f"ISBN:{isbn}")

        if not book:
            return None

        authors = []

        for a in book.get("authors", []):

            if a.get("name"):
                authors.append(a["name"])

        publisher = None

        if book.get("publishers"):
            publisher = book["publishers"][0]["name"]

        return {

            "isbn": isbn,

            "title": book.get("title"),

            "author": ", ".join(authors),

            "publisher": publisher,

            "year": book.get("publish_date"),

            "cover": None

        }

    except Exception as e:

        print("OpenLibrary:", e)

        return None

def fetch_isbnsearch(isbn):

    return None

def fetch_book(isbn):

    isbn = normalize_isbn(isbn)

    data = fetch_isbndb(isbn)

    if data:
        print("Metadata: ISBNdb")
        return data

    data = fetch_openlibrary(isbn)

    if data:
        print("Metadata: OpenLibrary")
        return data

    data = fetch_isbnsearch(isbn)

    if data:
        print("Metadata: ISBNSearch")
        return data

    return {

        "isbn": isbn,

        "title": isbn,

        "author": None,

        "publisher": None,

        "year": None,

        "cover": None

    }


