from contextlib import contextmanager

from psycopg2.pool import ThreadedConnectionPool

from settings import (
    DB_HOST,
    DB_PORT,
    DB_NAME,
    DB_USER,
    DB_PASS,
)

# -----------------------
# CONNECTION POOL
# -----------------------
pool = ThreadedConnectionPool(
    minconn=1,
    maxconn=10,
    host=DB_HOST,
    port=DB_PORT,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASS
)


@contextmanager
def db_connection():
    """
    Kivesz egy kapcsolatot a poolból.

    Siker esetén commitol.
    Hiba esetén rollbackel.
    A végén mindig visszateszi a kapcsolatot a poolba.
    """
    conn = pool.getconn()

    try:
        yield conn
        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        pool.putconn(conn)


# -----------------------
# LOCATIONS
# -----------------------
def get_places():
    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    id,
                    room,
                    shelf,
                    slot
                FROM locations
                ORDER BY room, shelf, slot
            """)

            rows = cur.fetchall()

    return [
        {
            "id": row[0],
            "room": row[1],
            "shelf": row[2],
            "slot": row[3]
        }
        for row in rows
    ]


# -----------------------
# INSERT BOOK
# -----------------------
def insert_book(
    isbn,
    title,
    author,
    publisher,
    publish_year,
    location_id,
    borrowed_to=None
):
    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO books
                (
                    isbn,
                    title,
                    author,
                    publisher,
                    publish_year,
                    location_id,
                    borrowed_to
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                isbn,
                title,
                author,
                publisher,
                publish_year,
                location_id,
                borrowed_to
            ))

            book_id = cur.fetchone()[0]

    return book_id


# -----------------------
# LATEST BOOKS
# -----------------------
def latest_books(limit=20):
    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    b.id,
                    b.title,
                    b.author,
                    b.isbn,
                    b.publisher,
                    b.publish_year,
                    b.created,
                    l.room,
                    l.shelf,
                    l.slot,
                    b.borrowed_to
                FROM books b
                LEFT JOIN locations l
                    ON l.id = b.location_id
                ORDER BY b.created DESC, b.id DESC
                LIMIT %s
            """, (limit,))

            rows = cur.fetchall()

    return rows


# -----------------------
# ALL BOOKS
# -----------------------
def all_books(page=1, page_size=50, search=""):
    page = max(1, int(page))
    page_size = max(1, min(int(page_size), 100))

    offset = (page - 1) * page_size
    search = (search or "").strip()

    with db_connection() as conn:
        with conn.cursor() as cur:

            if search:
                search_pattern = f"%{search}%"

                cur.execute(
                    """
                    SELECT COUNT(*)
                    FROM books b
                    LEFT JOIN locations l
                        ON l.id = b.location_id
                    WHERE
                        COALESCE(b.isbn, '') ILIKE %s
                        OR COALESCE(b.title, '') ILIKE %s
                        OR COALESCE(b.author, '') ILIKE %s
                        OR COALESCE(b.publisher, '') ILIKE %s
                        OR COALESCE(b.borrowed_to, '') ILIKE %s
                        OR COALESCE(l.room, '') ILIKE %s
                        OR COALESCE(l.shelf, '') ILIKE %s
                        OR COALESCE(l.slot::text, '') ILIKE %s
                    """,
                    (
                        search_pattern,
                        search_pattern,
                        search_pattern,
                        search_pattern,
                        search_pattern,
                        search_pattern,
                        search_pattern,
                        search_pattern,
                    ),
                )

                total = cur.fetchone()[0]

                cur.execute(
                    """
                    SELECT
                        b.id,
                        b.isbn,
                        b.title,
                        b.author,
                        b.publisher,
                        b.publish_year,
                        b.created,
                        l.room,
                        l.shelf,
                        l.slot,
                        b.borrowed_to
                    FROM books b
                    LEFT JOIN locations l
                        ON l.id = b.location_id
                    WHERE
                        COALESCE(b.isbn, '') ILIKE %s
                        OR COALESCE(b.title, '') ILIKE %s
                        OR COALESCE(b.author, '') ILIKE %s
                        OR COALESCE(b.publisher, '') ILIKE %s
                        OR COALESCE(b.borrowed_to, '') ILIKE %s
                        OR COALESCE(l.room, '') ILIKE %s
                        OR COALESCE(l.shelf, '') ILIKE %s
                        OR COALESCE(l.slot::text, '') ILIKE %s
                    ORDER BY b.title, b.id
                    LIMIT %s
                    OFFSET %s
                    """,
                    (
                        search_pattern,
                        search_pattern,
                        search_pattern,
                        search_pattern,
                        search_pattern,
                        search_pattern,
                        search_pattern,
                        search_pattern,
                        page_size,
                        offset,
                    ),
                )

            else:
                cur.execute(
                    """
                    SELECT COUNT(*)
                    FROM books
                    """
                )

                total = cur.fetchone()[0]

                cur.execute(
                    """
                    SELECT
                        b.id,
                        b.isbn,
                        b.title,
                        b.author,
                        b.publisher,
                        b.publish_year,
                        b.created,
                        l.room,
                        l.shelf,
                        l.slot,
                        b.borrowed_to
                    FROM books b
                    LEFT JOIN locations l
                        ON l.id = b.location_id
                    ORDER BY b.title, b.id
                    LIMIT %s
                    OFFSET %s
                    """,
                    (
                        page_size,
                        offset,
                    ),
                )

            rows = cur.fetchall()

    return rows, total

# -----------------------
# GET ONE BOOK
# -----------------------
def get_book(book_id):
    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    b.id,
                    b.isbn,
                    b.title,
                    b.author,
                    b.publisher,
                    b.publish_year,
                    b.created,
                    b.location_id,
                    b.borrowed_to,
                    l.room,
                    l.shelf,
                    l.slot
                FROM books b
                LEFT JOIN locations l
                    ON l.id = b.location_id
                WHERE b.id = %s
            """, (book_id,))

            row = cur.fetchone()

    return row


# -----------------------
# DELETE BOOK
# -----------------------
def delete_book(book_id):
    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM books
                WHERE id = %s
            """, (book_id,))

            deleted = cur.rowcount > 0

    return deleted


# -----------------------
# UPDATE BOOK
# -----------------------
def update_book(
    book_id,
    isbn,
    title,
    author,
    publisher,
    publish_year,
    location_id,
    borrowed_to
):
    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE books
                SET
                    isbn = %s,
                    title = %s,
                    author = %s,
                    publisher = %s,
                    publish_year = %s,
                    location_id = %s,
                    borrowed_to = %s,
                    updated = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (
                isbn,
                title,
                author,
                publisher,
                publish_year,
                location_id,
                borrowed_to,
                book_id
            ))

            updated = cur.rowcount > 0

    return updated

def export_books():
    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    b.id,
                    b.isbn,
                    b.title,
                    b.author,
                    b.publish_year,
                    b.publisher,
                    b.created,
                    b.updated,
                    b.borrowed_to,
                    l.room,
                    l.shelf,
                    l.slot
                FROM books b
                LEFT JOIN locations l
                    ON l.id = b.location_id
                ORDER BY b.id
            """)

            rows = cur.fetchall()

    return rows
