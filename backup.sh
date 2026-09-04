#!/usr/bin/env bash

set -Eeuo pipefail

PROJECT_DIR="${PROJECT_DIR:-/opt/familycollection}"
ENV_FILE="$PROJECT_DIR/api/.env"
DATA_DIR="$PROJECT_DIR/data"
SERVICE_FILE="/etc/systemd/system/family-api.service"

BACKUP_ROOT="${BACKUP_ROOT:-/backup/familycollection}"
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-5}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_DIR="$BACKUP_ROOT/$TIMESTAMP"

fail() {
    echo "ERROR: $*" >&2
    exit 1
}

require_command() {
    command -v "$1" >/dev/null 2>&1 || fail "Required command not found: $1"
}

require_command pg_dump
require_command gzip
require_command git
require_command python3
require_command psql

[[ -d "$PROJECT_DIR" ]] || fail "Project directory not found: $PROJECT_DIR"
[[ -f "$ENV_FILE" ]] || fail "Environment file not found: $ENV_FILE"
[[ -d "$DATA_DIR" ]] || fail "Runtime data directory not found: $DATA_DIR"

if ! [[ "$BACKUP_RETENTION_DAYS" =~ ^[0-9]+$ ]]; then
    fail "BACKUP_RETENTION_DAYS must be a non-negative integer."
fi

set -a
source "$ENV_FILE"
set +a

for variable in DB_HOST DB_PORT DB_NAME DB_USER DB_PASS; do
    [[ -n "${!variable:-}" ]] || fail "$variable is not configured."
done

umask 077
mkdir -p "$BACKUP_ROOT"
chmod 700 "$BACKUP_ROOT"

if [[ -e "$BACKUP_DIR" ]]; then
    fail "Backup directory already exists: $BACKUP_DIR"
fi

mkdir "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"

echo "========================================"
echo "FamilyCollection backup"
echo "Started: $(date --iso-8601=seconds)"
echo "Destination: $BACKUP_DIR"
echo "========================================"

echo "== Configuration =="
install -m 600 "$ENV_FILE" "$BACKUP_DIR/api.env"

if [[ -f "$SERVICE_FILE" ]]; then
    install -m 600 "$SERVICE_FILE" "$BACKUP_DIR/family-api.service"
fi

echo "== Runtime data =="
cp -a "$DATA_DIR" "$BACKUP_DIR/data"

echo "== PostgreSQL custom dump =="
PGPASSWORD="$DB_PASS" pg_dump \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    -Fc \
    -f "$BACKUP_DIR/familycollection.dump"

echo "== PostgreSQL plain SQL dump =="
PGPASSWORD="$DB_PASS" pg_dump \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --no-owner \
    --no-privileges \
    | gzip -9 > "$BACKUP_DIR/familycollection.sql.gz"

echo "== Deployment metadata =="
{
    echo "backup_created=$(date --iso-8601=seconds)"
    echo "project_dir=$PROJECT_DIR"
    echo "python=$(python3 --version 2>&1)"
    echo "psql=$(psql --version 2>&1)"
    echo "pg_dump=$(pg_dump --version 2>&1)"
    if git -C "$PROJECT_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        echo "git_commit=$(git -C "$PROJECT_DIR" rev-parse HEAD)"
        echo "git_branch=$(git -C "$PROJECT_DIR" branch --show-current)"
        echo "git_describe=$(git -C "$PROJECT_DIR" describe --tags --always --dirty)"
    fi
} > "$BACKUP_DIR/deployment.txt"

echo "== Verification =="
[[ -s "$BACKUP_DIR/familycollection.dump" ]] || fail "Custom database dump is empty."
[[ -s "$BACKUP_DIR/familycollection.sql.gz" ]] || fail "SQL database dump is empty."
gzip -t "$BACKUP_DIR/familycollection.sql.gz" || fail "Compressed SQL dump verification failed."
[[ -s "$BACKUP_DIR/api.env" ]] || fail "Environment backup is empty."
[[ -d "$BACKUP_DIR/data" ]] || fail "Runtime data backup is missing."

echo "== Retention =="
if (( BACKUP_RETENTION_DAYS > 0 )); then
    find "$BACKUP_ROOT" \
        -mindepth 1 \
        -maxdepth 1 \
        -type d \
        -mtime "+$BACKUP_RETENTION_DAYS" \
        -print \
        -exec rm -rf -- {} +
else
    echo "Automatic deletion disabled."
fi

echo
echo "========================================"
echo "Backup completed successfully."
echo "$BACKUP_DIR"
echo "========================================"
