#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="${PROJECT_DIR:-/opt/familycollection}"
DEMO_ENV="$PROJECT_DIR/demo/.env"
API_DIR="$PROJECT_DIR/api"

if [[ ! -f "$DEMO_ENV" ]]; then
    echo "ERROR: demo/.env does not exist."
    exit 1
fi

set -a
source "$DEMO_ENV"
set +a

if [[ "${DB_NAME:-}" != "familycollection_demo" ]]; then
    echo "REFUSED: demo seed may only run against familycollection_demo"
    exit 1
fi

cd "$PROJECT_DIR"

"$API_DIR/venv/bin/python" demo/seed_demo.py
