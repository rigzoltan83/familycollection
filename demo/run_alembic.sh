#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="${PROJECT_DIR:-/opt/familycollection}"
API_DIR="$PROJECT_DIR/api"
DEMO_ENV="$PROJECT_DIR/demo/.env"

if [[ ! -f "$DEMO_ENV" ]]; then
    echo "ERROR: demo/.env does not exist."
    echo "Run demo/create_demo_db.sh first."
    exit 1
fi

set -a
source "$DEMO_ENV"
set +a

if [[ "${DB_NAME:-}" != "familycollection_demo" ]]; then
    echo "REFUSED: migrations may only run against familycollection_demo"
    exit 1
fi

cd "$API_DIR"

venv/bin/alembic upgrade head

echo
echo "Demo database migrated successfully."
