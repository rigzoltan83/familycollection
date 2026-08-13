# FamilyCollection installation

This document describes a fresh FamilyCollection installation on Ubuntu 24.04.

> FamilyCollection is currently under active development and is not yet considered production-ready for public Internet deployment.

## Requirements

- Ubuntu 24.04
- sudo/root access
- Internet access during installation
- Git
- Docker and Docker Compose
- Python 3

The installation script installs the required operating-system packages.

## 1. Clone the repository

Clone FamilyCollection directly to `/opt/familycollection`:

```bash
cd /opt

sudo git clone \
    https://github.com/rigzoltan83/familycollection.git \
    familycollection
```

Change ownership to the user that will run the application:

```bash
sudo chown -R \
    "$USER":"$(id -gn)" \
    /opt/familycollection
```

Enter the project directory:

```bash
cd /opt/familycollection
```

## 2. Select the branch

During active development, use the development branch:

```bash
git switch feature/platform-foundation
```

For a stable release, use the branch or tag documented for that release.

## 3. Run the installer

```bash
cd /opt/familycollection

sudo ./install.sh
```

The installer:

- installs required Ubuntu packages;
- enables Docker;
- generates a random PostgreSQL password;
- generates a random session secret;
- creates `api/.env`;
- creates a root `.env` symlink for Docker Compose;
- starts PostgreSQL 16;
- creates the Python virtual environment;
- installs Python dependencies;
- applies all Alembic migrations;
- installs and starts `family-api.service`;
- verifies that the login page is reachable.

Generated secrets are not printed to the terminal.

The installer is intended only for a fresh installation. It refuses to continue if an existing application configuration is detected.

## 4. Create the first administrator

After installation:

```bash
cd /opt/familycollection/api

venv/bin/python \
    scripts/bootstrap_admin.py
```

The script interactively asks for:

- email address;
- username;
- display name;
- password.

The first account is created as a platform administrator and as the owner of the default household.

## 5. Open FamilyCollection

By default:

```text
http://SERVER_IP:8000/ui/login.html
```

Log in with the administrator account created in the previous step.

## 6. HTTPS and session cookies

A fresh installation initially uses:

```text
SESSION_COOKIE_SECURE=false
```

This allows login over plain HTTP during initial local testing.

For an HTTPS deployment, change this in:

```text
/opt/familycollection/api/.env
```

to:

```text
SESSION_COOKIE_SECURE=true
```

Then restart the API:

```bash
sudo systemctl restart \
    family-api.service
```

Do not expose a production installation directly to the public Internet over plain HTTP.

## 7. Application configuration

The local configuration is stored in:

```text
/opt/familycollection/api/.env
```

This file is intentionally excluded from Git.

The project-root `.env` is a symlink to the same file so that Docker Compose and the API always use the same database credentials.

An example configuration is available at:

```text
/opt/familycollection/api/.env.example
```

## 8. Service management

Check the API:

```bash
sudo systemctl status \
    family-api.service
```

Restart it:

```bash
sudo systemctl restart \
    family-api.service
```

Follow its log:

```bash
sudo journalctl \
    -u family-api.service \
    -f
```

Check PostgreSQL:

```bash
cd /opt/familycollection

sudo docker compose ps
```

## 9. Database migrations

The installer applies all migrations automatically.

For later manual migration:

```bash
cd /opt/familycollection/api

venv/bin/alembic upgrade head
```

Check the current migration:

```bash
venv/bin/alembic current
```

## 10. Tests

Development dependencies are required for the test suite.

Install them with:

```bash
cd /opt/familycollection/api

venv/bin/pip install \
    -r requirements-dev.in
```

The tests use a separate PostgreSQL database named by:

```text
TEST_DATABASE_NAME
```

The default is:

```text
familycollection_test
```

Run the tests with:

```bash
cd /opt/familycollection/api

venv/bin/python -m pytest -q
```

## 11. Backup

The repository contains:

```text
/opt/familycollection/backup.sh
```

The backup script uses the database settings from `api/.env`.

Review `BACKUPROOT` in the script before enabling scheduled backups, because the default backup destination is:

```text
/backup/familycoll
```

## Security notes

Never commit any of the following files:

```text
.env
api/.env
```

Never put real passwords or API keys into `.env.example`.

Use a reverse proxy with HTTPS before exposing FamilyCollection outside a trusted network.

Keep regular backups of both:

- PostgreSQL;
- `/opt/familycollection/data`.
