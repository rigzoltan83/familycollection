#!/bin/bash

set -e

DATE=$(date +%Y%m%d_%H%M%S)

BACKUPDIR="/backup/familycoll/$DATE"

echo "Backup mappa:"
echo "$BACKUPDIR"

mkdir -p "$BACKUPDIR"

echo "== API =="
cp -a /opt/familycollection/api "$BACKUPDIR/"

echo "== UI =="
cp -a /opt/familycollection/ui "$BACKUPDIR/"

echo "== Systemd =="
cp /etc/systemd/system/family-api.service "$BACKUPDIR/"

echo "== SQL dump =="

PGPASSWORD=REMOVED_DB_PASSWORD pg_dump \
    -h localhost \
    -U familyuser \
    -d familycollection \
    > "$BACKUPDIR/familycollection.sql"

echo "== Custom dump =="

PGPASSWORD=REMOVED_DB_PASSWORD pg_dump \
    -Fc \
    -h localhost \
    -U familyuser \
    -d familycollection \
    -f "$BACKUPDIR/familycollection.dump"

echo "== Könyvtárlista =="

tree /opt/familycollection > "$BACKUPDIR/tree.txt" || true

echo "== Verziók =="

python3 --version > "$BACKUPDIR/versions.txt"

psql --version >> "$BACKUPDIR/versions.txt"

echo ""
echo "===================================="
echo "MENTÉS KÉSZ"
echo "$BACKUPDIR"
echo "===================================="
