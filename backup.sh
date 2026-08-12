#!/bin/bash

set -euo pipefail

DATE=$(date +%Y%m%d_%H%M%S)

BACKUPROOT="/backup/familycoll"
BACKUPDIR="$BACKUPROOT/$DATE"

if [ -f /opt/familycollection/api/.env ]; then
    set -a
    . /opt/familycollection/api/.env
    set +a
fi

if [ -z "${DB_PASS:-}" ]; then
    echo "HIBA: DB_PASS nincs beállítva."
    exit 1
fi

echo "===================================="
echo "FamilyCollection backup indul"
echo "Időpont: $(date)"
echo "Backup mappa:"
echo "$BACKUPDIR"
echo "===================================="

mkdir -p "$BACKUPDIR"

echo "== API =="
cp -a \
    /opt/familycollection/api \
    "$BACKUPDIR/"

echo "== UI =="
cp -a \
    /opt/familycollection/ui \
    "$BACKUPDIR/"

echo "== DATA / KÉPEK =="
cp -a \
    /opt/familycollection/data \
    "$BACKUPDIR/"

echo "== Systemd =="
cp -a \
    /etc/systemd/system/family-api.service \
    "$BACKUPDIR/"

echo "== SQL dump =="

PGPASSWORD="$DB_PASS" pg_dump \
    -h localhost \
    -U familyuser \
    -d familycollection \
    > "$BACKUPDIR/familycollection.sql"

echo "== PostgreSQL custom dump =="

PGPASSWORD="$DB_PASS" pg_dump \
    -Fc \
    -h localhost \
    -U familyuser \
    -d familycollection \
    -f "$BACKUPDIR/familycollection.dump"

echo "== Könyvtárlista =="

tree /opt/familycollection \
    > "$BACKUPDIR/tree.txt" \
    || true

echo "== Verziók =="

python3 --version \
    > "$BACKUPDIR/versions.txt"

psql --version \
    >> "$BACKUPDIR/versions.txt"

echo "== Backup ellenőrzése =="

test -s \
    "$BACKUPDIR/familycollection.sql"

test -s \
    "$BACKUPDIR/familycollection.dump"

test -d \
    "$BACKUPDIR/api"

test -d \
    "$BACKUPDIR/ui"

test -d \
    "$BACKUPDIR/data"

echo "== 5 napnál régebbi mentések törlése =="

find "$BACKUPROOT" \
    -mindepth 1 \
    -maxdepth 1 \
    -type d \
    -mmin +7200 \
    -print \
    -exec rm -rf -- {} +

echo ""
echo "===================================="
echo "MENTÉS KÉSZ"
echo "$BACKUPDIR"
echo "===================================="
