#!/usr/bin/env bash

set -Eeuo pipefail

PROJECT_DIR="/opt/familycollection"
API_DIR="$PROJECT_DIR/api"
ENV_FILE="$API_DIR/.env"
ROOT_ENV="$PROJECT_DIR/.env"

SERVICE_FILE="/etc/systemd/system/family-api.service"

APP_USER="${SUDO_USER:-$USER}"
APP_GROUP="$(
    id -gn "$APP_USER"
)"

echo "======================================"
echo " FamilyCollection installer"
echo " FamilyCollection telepítő"
echo "======================================"
echo
echo "Select language / Válassz nyelvet:"
echo
echo "1) English"
echo "2) Magyar"
echo

read -r -p "Choice / Választás [1]: " LANGUAGE_CHOICE

case "${LANGUAGE_CHOICE:-1}" in
    2|hu|HU)
        LANGUAGE="hu"
        ;;
    *)
        LANGUAGE="en"
        ;;
esac

message() {
    local english="$1"
    local hungarian="$2"

    if [ "$LANGUAGE" = "hu" ]; then
        echo "$hungarian"
    else
        echo "$english"
    fi
}

section() {
    echo
    message \
        "===== $1 =====" \
        "===== $2 ====="
}

if [ "$(id -u)" -ne 0 ]; then
    message \
        "ERROR: run the installer with sudo." \
        "HIBA: a telepítőt sudo-val kell futtatni."
    exit 1
fi

if [ ! -d "$PROJECT_DIR/.git" ]; then
    message \
        "ERROR: Git repository not found:" \
        "HIBA: nem található Git repository:"
    echo "$PROJECT_DIR"
    exit 1
fi

if [ -e "$ENV_FILE" ]; then
    message \
        "ERROR: api/.env already exists." \
        "HIBA: az api/.env már létezik."
    echo
    message \
        "This script is intended for fresh installations only." \
        "Ez a script csak új telepítéshez használható."
    exit 1
fi

if [ -e "$ROOT_ENV" ] || [ -L "$ROOT_ENV" ]; then
    message \
        "ERROR: the project root .env already exists." \
        "HIBA: a projekt gyökér .env már létezik."
    exit 1
fi

echo
echo "======================================"
message \
    " FamilyCollection installation" \
    " FamilyCollection telepítés"
echo "======================================"
echo

message \
    "Application user: $APP_USER" \
    "Alkalmazás-felhasználó: $APP_USER"

message \
    "Project: $PROJECT_DIR" \
    "Projekt: $PROJECT_DIR"

section \
    "1. SYSTEM PACKAGES" \
    "1. RENDSZERCSOMAGOK"

apt-get update

apt-get install -y \
    python3 \
    python3-venv \
    python3-pip \
    postgresql-client \
    docker.io \
    docker-compose-v2 \
    curl \
    git \
    iproute2

systemctl enable --now docker

section \
    "2. POSTGRESQL HOST PORT" \
    "2. POSTGRESQL HOST PORT"

DB_PORT=5432

while ss -ltn \
    | awk '{print $4}' \
    | grep -Eq "(^|:)$DB_PORT$"
do
    DB_PORT=$((DB_PORT + 1))
done

message \
    "OK: PostgreSQL host port: $DB_PORT" \
    "OK: PostgreSQL host port: $DB_PORT"

section \
    "3. GENERATING SECRETS" \
    "3. TITKOK GENERÁLÁSA"

DB_PASS="$(
    python3 - <<'PY'
import secrets
print(secrets.token_hex(32))
PY
)"

SESSION_SECRET="$(
    python3 - <<'PY'
import secrets
print(secrets.token_hex(48))
PY
)"

if [ "${#DB_PASS}" -ne 64 ]; then
    message \
        "ERROR: database password generation failed." \
        "HIBA: DB-jelszó generálási hiba."
    exit 1
fi

if [ "${#SESSION_SECRET}" -ne 96 ]; then
    message \
        "ERROR: session secret generation failed." \
        "HIBA: session secret generálási hiba."
    exit 1
fi

message \
    "OK: secrets generated." \
    "OK: titkok elkészültek."

message \
    "Secret values are not printed." \
    "Az értékeket nem írjuk ki."

section \
    "4. API .ENV" \
    "4. API .ENV"

cat > "$ENV_FILE" <<EOF
# PostgreSQL connection
DB_HOST=localhost
DB_PORT=$DB_PORT
DB_NAME=familycollection
DB_USER=familyuser
DB_PASS=$DB_PASS

# External metadata services
ISBNDB_KEY=

# Metadata providers
USE_ISBNDB=false
USE_OPENLIBRARY=true
USE_ISBNSEARCH=true

# Application environment
APP_ENV=production

# Pytest database
TEST_DATABASE_NAME=familycollection_test

# Login session
SESSION_SECRET_KEY=$SESSION_SECRET
SESSION_COOKIE_SECURE=false
SESSION_MAX_AGE_SECONDS=2592000
EOF

chown "$APP_USER":"$APP_GROUP" \
    "$ENV_FILE"

chmod 600 \
    "$ENV_FILE"

ln -s \
    "api/.env" \
    "$ROOT_ENV"

message \
    "OK: api/.env and root .env symlink created." \
    "OK: api/.env + gyökér .env symlink."

section \
    "5. POSTGRESQL" \
    "5. POSTGRESQL"

cd "$PROJECT_DIR"

docker compose up -d db

message \
    "Waiting for PostgreSQL to start..." \
    "Várakozás a PostgreSQL indulására..."

for attempt in $(seq 1 30)
do
    if docker exec family-db \
        pg_isready \
        -U familyuser \
        -d familycollection \
        >/dev/null 2>&1
    then
        break
    fi

    if [ "$attempt" -eq 30 ]; then
        message \
            "ERROR: PostgreSQL failed to start." \
            "HIBA: PostgreSQL nem indult el."
        exit 1
    fi

    sleep 2
done

message \
    "OK: PostgreSQL is available." \
    "OK: PostgreSQL elérhető."

section \
    "6. PYTHON VENV" \
    "6. PYTHON VENV"

sudo -u "$APP_USER" \
    python3 -m venv \
    "$API_DIR/venv"

sudo -u "$APP_USER" \
    "$API_DIR/venv/bin/python" \
    -m pip install \
    --upgrade pip

sudo -u "$APP_USER" \
    "$API_DIR/venv/bin/pip" \
    install \
    -r "$API_DIR/requirements.txt"

section \
    "7. DATABASE MIGRATIONS" \
    "7. ADATBÁZIS MIGRÁCIÓ"

cd "$API_DIR"

sudo -u "$APP_USER" \
    "$API_DIR/venv/bin/alembic" \
    upgrade head

section \
    "8. SYSTEMD SERVICE" \
    "8. SYSTEMD SERVICE"

cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=FamilyCollection API (FastAPI)
After=network.target docker.service
Requires=docker.service

[Service]
User=$APP_USER
WorkingDirectory=$API_DIR
ExecStart=$API_DIR/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000

Restart=always
RestartSec=3

Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload

systemctl enable \
    family-api.service

systemctl restart \
    family-api.service

sleep 3

if ! systemctl is-active \
    --quiet \
    family-api.service
then
    message \
        "ERROR: family-api.service failed to start." \
        "HIBA: family-api.service nem indult el."

    systemctl \
        --no-pager \
        --full \
        status family-api.service

    exit 1
fi

message \
    "OK: FamilyCollection API is running." \
    "OK: FamilyCollection API fut."

section \
    "9. HTTP TEST" \
    "9. HTTP TESZT"

HTTP_CODE="$(
    curl \
        -s \
        -o /dev/null \
        -w '%{http_code}' \
        http://127.0.0.1:8000/ui/login.html
)"

if [ "$HTTP_CODE" != "200" ]; then
    message \
        "ERROR: login page returned HTTP $HTTP_CODE." \
        "HIBA: login oldal HTTP $HTTP_CODE"
    exit 1
fi

message \
    "OK: login page returned HTTP 200." \
    "OK: login oldal HTTP 200."

echo
echo "======================================"

message \
    " BASE INSTALLATION COMPLETE" \
    " ALAPTELEPÍTÉS KÉSZ"

echo "======================================"
echo

message \
    "Next step:" \
    "Következő lépés:"

echo
echo "cd $API_DIR"
echo "venv/bin/python scripts/bootstrap_admin.py"
echo

message \
    "This interactively creates the first administrator." \
    "Ez interaktívan létrehozza az első admint."

echo
message \
    "Web:" \
    "Web:"

echo "http://<server-ip>:8000/ui/login.html"
echo

message \
    "IMPORTANT:" \
    "FONTOS:"

message \
    "For testing without HTTPS, SESSION_COOKIE_SECURE=false is required." \
    "Ha HTTPS nélkül tesztelsz, a SESSION_COOKIE_SECURE=false beállítás szükséges."

message \
    "When using HTTPS in production, set it to true." \
    "Éles HTTPS használatakor állítsd true-ra."
