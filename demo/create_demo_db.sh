#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="${PROJECT_DIR:-/opt/familycollection}"
API_DIR="$PROJECT_DIR/api"
DEMO_DB_NAME="familycollection_demo"
DEMO_ENV="$PROJECT_DIR/demo/.env"

cd "$PROJECT_DIR"

if [[ ! -f "$API_DIR/.env" ]]; then
    echo "ERROR: $API_DIR/.env not found."
    exit 1
fi

set -a
source "$API_DIR/.env"
set +a

for variable in DB_HOST DB_PORT DB_USER DB_PASS; do
    if [[ -z "${!variable:-}" ]]; then
        echo "ERROR: $variable is missing."
        exit 1
    fi
done

if [[ "${DB_NAME:-}" == "$DEMO_DB_NAME" ]]; then
    echo "ERROR: production configuration already points to demo DB."
    exit 1
fi

export PGPASSWORD="$DB_PASS"

if psql \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d postgres \
    -tAc "SELECT 1 FROM pg_database WHERE datname='$DEMO_DB_NAME'" \
    | grep -qx 1
then
    echo "Demo database already exists: $DEMO_DB_NAME"
else
    createdb \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        "$DEMO_DB_NAME"

    echo "Created demo database: $DEMO_DB_NAME"
fi

umask 077

SESSION_SECRET="$(
    python3 - <<'PY2'
import secrets
print(secrets.token_urlsafe(48))
PY2
)"

cat > "$DEMO_ENV" <<ENV
DB_HOST=$DB_HOST
DB_PORT=$DB_PORT
DB_NAME=$DEMO_DB_NAME
DB_USER=$DB_USER
DB_PASS=$DB_PASS

APP_ENV=development

SESSION_SECRET_KEY=$SESSION_SECRET
SESSION_COOKIE_SECURE=false
SESSION_MAX_AGE_SECONDS=2592000

APP_BASE_PATH=
SESSION_COOKIE_PATH=/

ITEM_IMAGE_ROOT=$PROJECT_DIR/demo/data/images/items
ENV

chmod 600 "$DEMO_ENV"

echo
echo "Demo environment created:"
echo "  database: $DEMO_DB_NAME"
echo "  env:      $DEMO_ENV"
echo
echo "Production database was not modified."
