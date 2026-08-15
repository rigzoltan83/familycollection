#!/usr/bin/env python3

import argparse
import csv
import secrets
import subprocess
import sys
import time
from decimal import Decimal, InvalidOperation
from pathlib import Path


DB_CONTAINER = "family-db"
DB_USER = "familyuser"
DB_NAME = "familycollection"

CATEGORY_ID = 3
STORAGE_LOCATION_ID = 40

FIELD_IDS = {
    "number": 13,
    "year": 14,
    "used_price": 17,
    "new_price": 18,
    "pcs": 20,
    "mfigs": 21,
}

CSV_MAPPING = {
    "title": "SetName",
    "subtitle": "Theme",
    "number": "Number",
    "year": "YearFrom",
    "pcs": "Pieces",
    "mfigs": "Minifigs",
    "used_price": "BrickLinkSoldPriceUsed",
    "new_price": "BrickLinkSoldPriceNew",
}

CROCKFORD32 = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def die(message):
    print(f"HIBA: {message}", file=sys.stderr)
    sys.exit(1)


def psql(sql, tuples_only=False):
    cmd = [
        "docker",
        "exec",
        "-i",
        DB_CONTAINER,
        "psql",
        "-v",
        "ON_ERROR_STOP=1",
        "-U",
        DB_USER,
        "-d",
        DB_NAME,
    ]

    if tuples_only:
        cmd.extend(["-A", "-t"])

    result = subprocess.run(
        cmd,
        input=sql,
        text=True,
        capture_output=True,
    )

    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        die("A PostgreSQL parancs hibával leállt.")

    return result.stdout


def sql_quote(value):
    if value is None:
        return "NULL"

    value = str(value)
    return "'" + value.replace("'", "''") + "'"


def generate_ulid():
    timestamp_ms = int(time.time() * 1000)

    random_bits = secrets.randbits(80)

    value = (timestamp_ms << 80) | random_bits

    chars = []

    for _ in range(26):
        chars.append(CROCKFORD32[value & 31])
        value >>= 5

    return "".join(reversed(chars))


def clean_text(value):
    if value is None:
        return None

    value = str(value).strip()

    if not value:
        return None

    return value


def parse_integer(value, field_name, row_number):
    value = clean_text(value)

    if value is None:
        return None

    try:
        number = Decimal(value.replace(",", "."))

        if number != number.to_integral_value():
            raise ValueError

        return int(number)

    except (InvalidOperation, ValueError):
        die(
            f"{row_number}. CSV sor: "
            f"{field_name} nem egész szám: {value!r}"
        )


def parse_decimal(value, field_name, row_number):
    value = clean_text(value)

    if value is None:
        return None

    normalized = value.replace(" ", "")

    # 12,34 -> 12.34
    if "," in normalized and "." not in normalized:
        normalized = normalized.replace(",", ".")

    # 1,234.56 -> 1234.56
    elif "," in normalized and "." in normalized:
        normalized = normalized.replace(",", "")

    try:
        return Decimal(normalized)

    except InvalidOperation:
        die(
            f"{row_number}. CSV sor: "
            f"{field_name} nem szám: {value!r}"
        )


def detect_csv(path):
    raw = path.read_text(
        encoding="utf-8-sig",
        errors="replace",
    )

    try:
        dialect = csv.Sniffer().sniff(
            raw[:10000],
            delimiters=",;\t",
        )
    except csv.Error:
        dialect = csv.excel

    return raw, dialect


def get_household_id(explicit_id):
    if explicit_id is not None:
        sql = f"""
SELECT id
FROM households
WHERE id = {int(explicit_id)};
"""

        result = psql(
            sql,
            tuples_only=True,
        ).strip()

        if not result:
            die(
                f"Nincs household id={explicit_id}."
            )

        return int(explicit_id)

    result = psql(
        """
SELECT id
FROM households
ORDER BY id;
""",
        tuples_only=True,
    )

    ids = [
        int(x.strip())
        for x in result.splitlines()
        if x.strip()
    ]

    if len(ids) == 1:
        return ids[0]

    if not ids:
        die("Nincs household rekord.")

    die(
        "Több household van. "
        "Add meg: --household-id ID"
    )


def validate_database():
    sql = f"""
SELECT
    CASE
        WHEN EXISTS (
            SELECT 1
            FROM categories
            WHERE id = {CATEGORY_ID}
              AND LOWER(name) = 'lego'
        )
        THEN 'OK'
        ELSE 'HIBA'
    END;
"""

    result = psql(
        sql,
        tuples_only=True,
    ).strip()

    if result != "OK":
        die(
            "A LEGO kategória "
            f"(category_id={CATEGORY_ID}) nem található."
        )

    sql = f"""
SELECT
    CASE
        WHEN EXISTS (
            SELECT 1
            FROM storage_locations
            WHERE id = {STORAGE_LOCATION_ID}
              AND slug = 'slot-5'
              AND is_active = true
        )
        THEN 'OK'
        ELSE 'HIBA'
    END;
"""

    result = psql(
        sql,
        tuples_only=True,
    ).strip()

    if result != "OK":
        die(
            "A cél tárhely "
            f"(id={STORAGE_LOCATION_ID}) nem található."
        )

    expected = {
        13: ("number", "text"),
        14: ("year", "year"),
        17: ("used_price", "decimal"),
        18: ("new_price", "decimal"),
        20: ("pcs", "integer"),
        21: ("mfigs", "integer"),
    }

    result = psql(
        """
SELECT
    id,
    field_key,
    field_type
FROM category_fields
WHERE category_id = 3
  AND id IN (13,14,17,18,20,21)
ORDER BY id;
""",
        tuples_only=True,
    )

    found = {}

    for line in result.splitlines():
        line = line.strip()

        if not line:
            continue

        parts = line.split("|")

        if len(parts) == 3:
            found[int(parts[0])] = (
                parts[1],
                parts[2],
            )

    if found != expected:
        print("Elvárt mezők:")
        print(expected)

        print("Adatbázisban talált:")
        print(found)

        die("A LEGO mezőszerkezet eltér a várttól.")


def get_existing_numbers():
    sql = """
SELECT DISTINCT ifv.value_text
FROM collection_items ci
JOIN item_field_values ifv
    ON ifv.item_id = ci.id
WHERE ci.category_id = 3
  AND ifv.field_id = 13
  AND ifv.value_text IS NOT NULL;
"""

    result = psql(
        sql,
        tuples_only=True,
    )

    return {
        line.strip()
        for line in result.splitlines()
        if line.strip()
    }


def read_csv(csv_path):
    raw, dialect = detect_csv(csv_path)

    reader = csv.DictReader(
        raw.splitlines(),
        dialect=dialect,
    )

    if reader.fieldnames is None:
        die("A CSV-nek nincs fejléce.")

    available = {
        name.strip()
        for name in reader.fieldnames
        if name
    }

    required_columns = set(CSV_MAPPING.values())

    missing = required_columns - available

    if missing:
        die(
            "Hiányzó CSV oszlop(ok): "
            + ", ".join(sorted(missing))
        )

    rows = []

    seen_numbers = set()

    for csv_row_number, row in enumerate(
        reader,
        start=2,
    ):
        title = clean_text(
            row.get(CSV_MAPPING["title"])
        )

        subtitle = clean_text(
            row.get(CSV_MAPPING["subtitle"])
        )

        number = clean_text(
            row.get(CSV_MAPPING["number"])
        )

        if not title:
            die(
                f"{csv_row_number}. sor: "
                "SetName üres."
            )

        if not number:
            die(
                f"{csv_row_number}. sor: "
                "Number üres."
            )

        if number in seen_numbers:
            die(
                f"{csv_row_number}. sor: "
                f"duplikált Number a CSV-ben: {number}"
            )

        seen_numbers.add(number)

        parsed = {
            "csv_row": csv_row_number,
            "title": title,
            "subtitle": subtitle,
            "number": number,
            "year": parse_integer(
                row.get(CSV_MAPPING["year"]),
                "YearFrom",
                csv_row_number,
            ),
            "pcs": parse_integer(
                row.get(CSV_MAPPING["pcs"]),
                "Pieces",
                csv_row_number,
            ),
            "mfigs": parse_integer(
                row.get(CSV_MAPPING["mfigs"]),
                "Minifigs",
                csv_row_number,
            ),
            "used_price": (
                parse_decimal(
                    row.get(
                        CSV_MAPPING["used_price"]
                    ),
                    "BrickLinkSoldPriceUsed",
                    csv_row_number,
                ) * Decimal("316")
                if clean_text(
                    row.get(
                        CSV_MAPPING["used_price"]
                    )
                )
                else None
            ),
            "new_price": (
                parse_decimal(
                    row.get(
                        CSV_MAPPING["new_price"]
                    ),
                    "BrickLinkSoldPriceNew",
                    csv_row_number,
                ) * Decimal("316")
                if clean_text(
                    row.get(
                        CSV_MAPPING["new_price"]
                    )
                )
                else None
            ),
        }

        rows.append(parsed)

    return rows


def field_insert_sql(
    item_public_id,
    field_id,
    value_column,
    value,
):
    if value is None:
        return ""

    field_public_id = generate_ulid()

    if value_column == "value_text":
        sql_value = sql_quote(value)
    else:
        sql_value = str(value)

    return f"""
INSERT INTO item_field_values (
    item_id,
    field_id,
    {value_column},
    public_id
)
SELECT
    id,
    {field_id},
    {sql_value},
    {sql_quote(field_public_id)}
FROM collection_items
WHERE public_id = {sql_quote(item_public_id)};
"""


def build_item_sql(row, household_id):
    item_public_id = generate_ulid()

    storage_public_id = generate_ulid()

    sql = f"""
INSERT INTO collection_items (
    household_id,
    category_id,
    title,
    subtitle,
    status,
    is_active,
    public_id
)
VALUES (
    {household_id},
    {CATEGORY_ID},
    {sql_quote(row["title"])},
    {sql_quote(row["subtitle"])},
    'active',
    true,
    {sql_quote(item_public_id)}
);
"""

    sql += field_insert_sql(
        item_public_id,
        FIELD_IDS["number"],
        "value_text",
        row["number"],
    )

    # A 'year' mezőt egész számként tároljuk.
    sql += field_insert_sql(
        item_public_id,
        FIELD_IDS["year"],
        "value_integer",
        row["year"],
    )

    sql += field_insert_sql(
        item_public_id,
        FIELD_IDS["pcs"],
        "value_integer",
        row["pcs"],
    )

    sql += field_insert_sql(
        item_public_id,
        FIELD_IDS["mfigs"],
        "value_integer",
        row["mfigs"],
    )

    sql += field_insert_sql(
        item_public_id,
        FIELD_IDS["used_price"],
        "value_decimal",
        row["used_price"],
    )

    sql += field_insert_sql(
        item_public_id,
        FIELD_IDS["new_price"],
        "value_decimal",
        row["new_price"],
    )

    sql += f"""
INSERT INTO item_storage_assignments (
    item_id,
    storage_location_id,
    is_active,
    movement_reason,
    notes,
    public_id
)
SELECT
    id,
    {STORAGE_LOCATION_ID},
    true,
    'CSV import',
    'Brickset CSV import',
    {sql_quote(storage_public_id)}
FROM collection_items
WHERE public_id = {sql_quote(item_public_id)};
"""

    return sql


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Brickset CSV -> "
            "FamilyCollection LEGO import"
        )
    )

    parser.add_argument(
        "csv_file",
        help="A Brickset CSV fájl elérési útja",
    )

    parser.add_argument(
        "--household-id",
        type=int,
        default=None,
        help=(
            "Household ID. Ha csak egy household "
            "van, automatikusan felismeri."
        ),
    )

    parser.add_argument(
        "--commit",
        action="store_true",
        help=(
            "Tényleges import. Enélkül csak dry-run."
        ),
    )

    args = parser.parse_args()

    csv_path = Path(args.csv_file)

    if not csv_path.is_file():
        die(
            f"A CSV nem található: {csv_path}"
        )

    print("Adatbázis ellenőrzése...")
    validate_database()

    household_id = get_household_id(
        args.household_id
    )

    print(
        f"Household ID: {household_id}"
    )

    print("CSV feldolgozása...")

    rows = read_csv(csv_path)

    existing_numbers = get_existing_numbers()

    new_rows = []
    skipped_rows = []

    for row in rows:
        if row["number"] in existing_numbers:
            skipped_rows.append(row)
        else:
            new_rows.append(row)

    print()
    print("===================================")
    print("IMPORT ÖSSZESÍTÉS")
    print("===================================")
    print(f"CSV rekordok:       {len(rows)}")
    print(f"Új rekordok:        {len(new_rows)}")
    print(f"Már meglévők:       {len(skipped_rows)}")
    print(
        f"Cél tárhely ID:     "
        f"{STORAGE_LOCATION_ID}"
    )
    print()

    for index, row in enumerate(
        new_rows,
        start=1,
    ):
        print(
            f"{index:3}. "
            f"{row['number']:12} | "
            f"{row['title']} | "
            f"{row['subtitle'] or ''}"
        )

    if skipped_rows:
        print()
        print("KIHAGYOTT, MÁR MEGLÉVŐ:")
        print("-----------------------------------")

        for row in skipped_rows:
            print(
                f"{row['number']:12} | "
                f"{row['title']}"
            )

    if not args.commit:
        print()
        print("===================================")
        print("DRY-RUN KÉSZ")
        print("Az adatbázis NEM változott.")
        print()
        print(
            "Ha minden megfelelő, "
            "futtasd újra --commit kapcsolóval."
        )
        print("===================================")

        return

    if not new_rows:
        print()
        print("Nincs importálandó új LEGO.")
        return

    sql_parts = [
        "BEGIN;",
    ]

    for row in new_rows:
        sql_parts.append(
            build_item_sql(
                row,
                household_id,
            )
        )

    sql_parts.append("COMMIT;")

    sql = "\n".join(sql_parts)

    print()
    print(
        f"{len(new_rows)} LEGO importálása..."
    )

    psql(sql)

    print()
    print("===================================")
    print("IMPORT SIKERES")
    print(
        f"Importált LEGO-k: {len(new_rows)}"
    )
    print(
        f"Kihagyott meglévők: "
        f"{len(skipped_rows)}"
    )
    print("===================================")


if __name__ == "__main__":
    main()
