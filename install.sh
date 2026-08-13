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

if [ "$(id -u)" -ne 0 ]; then
    echo "HIBA: a telepítőt sudo-val kell futtatni."
    exit 1
fi

if [ ! -d "$PROJECT_DIR/.git" ]; then
    echo "HIBA: nem található Git repository:"
    echo "$PROJECT_DIR"
    exit 1
fi

if [ -e "$ENV_FILE" ]; then
    echo "HIBA: az api/.env már létezik."
    echo
    echo "Ez a script csak új telepítéshez használható."
    exit 1
fi

if [ -e "$ROOT_ENV" ] || [ -L "$ROOT_ENV" ]; then
    echo "HIBA: a projekt gyökér .env már létezik."
    exit 1
fi

echo "======================================"
echo " FamilyCollection telepítés"
echo "======================================"
echo
echo "Alkalmazás-felhasználó: $APP_USER"
echo "Projekt: $PROJECT_DIR"
echo

echo "===== 1. RENDSZERCSOMAGOK ====="

apt-get update

apt-get install -y \
    python3 \
    python3-venv \
    python3-pip \
    postgresql-client \
    docker.io \
    docker-compose-v2 \
    curl \
    git

systemctl enable --now docker

echo
echo "===== 2. TITKOK GENERÁLÁSA ====="

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
    echo "HIBA: DB-jelszó generálási hiba."
    exit 1
fi

if [ "${#SESSION_SECRET}" -ne 96 ]; then
    echo "HIBA: session secret generálási hiba."
    exit 1
fi

echo "OK: titkok elkészültek."
echo "Az értékeket nem írjuk ki."

echo
echo "===== 3. API .ENV ====="

cat > "$ENV_FILE" <<EOF
# PostgreSQL kapcsolat
DB_HOST=localhost
DB_PORT=5432
DB_NAME=familycollection
DB_USER=familyuser
DB_PASS=$DB_PASS

# Külső metadata-szolgáltatások
ISBNDB_KEY=

# Metadata-szolgáltatók
USE_ISBNDB=false
USE_OPENLIBRARY=true
USE_ISBNSEARCH=true

# Alkalmazási környezet
APP_ENV=production

# Pytest adatbázis
TEST_DATABASE_NAME=familycollection_test

# Bejelentkezási session
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

echo "OK: api/.env + gyökér .env symlink."

echo
echo "===== 4. POSTGRESQL ====="

cd "$PROJECT_DIR"

docker compose up -d db

echo "Várakozás a PostgreSQL indulására..."

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
        echo "HIBA: PostgreSQL nem indult el."
        exit 1
    fi

    sleep 2
done

echo "OK: PostgreSQL elérhető."

echo
echo "===== 5. PYTHON VENV ====="

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

echo
echo "===== 6. ADATBÁZIS MIGRÁCIÓ ====="

cd "$API_DIR"

sudo -u "$APP_USER" \
    "$API_DIR/venv/bin/alembic" \
    upgrade head

echo
echo "===== 7. SYSTEMD SERVICE ====="

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
    echo "HIBA: family-api.service nem indult el."
    systemctl \
        --no-pager \
        --full \
        status family-api.service
    exit 1
fi

echo "OK: FamilyCollection API fut."

echo
echo "===== 8. HTTP TESZT ====="

HTTP_CODE="$(
    curl \
        -s \
        -o /dev/null \
        -w '%{http_code}' \
        http://127.0.0.1:8000/ui/login.html
)"

if [ "$HTTP_CODE" != "200" ]; then
    echo "HIBA: login oldal HTTP $HTTP_CODE"
    exit 1
fi

echo "OK: login oldal HTTP 200."

echo
echo "======================================"
echo " ALAPTELEPÍTÉS KÉSZ"
echo "======================================"
echo
echo "Következő lépés:"
echo
echo "cd $API_DIR"
echo "venv/bin/python scripts/bootstrap_admin.py"
echo
echo "Ez interaktívan létrehozza az első admint."
echo
echo "Web:"
echo "http://<szerver-ip>:8000/ui/login.html"
echo
echo "FONTOS:"
echo "Ha HTTPS nélkül tesztelsz, a"
echo "SESSION_COOKIE_SECURE=false beállítás szükséges."
echo "Éles HTTPS használatakor állítsd true-ra."
