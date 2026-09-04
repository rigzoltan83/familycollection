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

## 2. Select the version

For the latest development version, use the `main` branch:

    git switch main
    git pull --ff-only

For a stable release, check out the release tag documented on the GitHub Releases page.

For example:

    git checkout v0.2.0

Release tags are recommended for installations where reproducibility is more important than receiving the newest development changes immediately.

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

## 6. HTTPS, session cookies, and URL subpaths

A fresh installation initially uses:

    SESSION_COOKIE_SECURE=false

This allows login over plain HTTP during initial local testing.

For an HTTPS deployment, change this in:

    /opt/familycollection/api/.env

to:

    SESSION_COOKIE_SECURE=true

Then restart the API:

    sudo systemctl restart family-api.service

Do not expose a production installation directly to the public Internet over plain HTTP.

### Deploying at the domain root

For a normal root deployment, use:

    APP_BASE_PATH=
    SESSION_COOKIE_PATH=/

The application is then available directly below the host name, for example:

    https://example.com/ui/login.html

### Deploying under a URL subpath

FamilyCollection can also be published below a URL prefix when a reverse proxy strips that prefix before forwarding requests to the application.

For example, to publish it below `/familycollection`, use:

    APP_BASE_PATH=/familycollection
    SESSION_COOKIE_PATH=/familycollection

The browser-facing login URL is then:

    https://example.com/familycollection/ui/login.html

`SESSION_COOKIE_PATH` should normally match the application subpath. This keeps the FamilyCollection session cookie scoped to the application instead of the entire domain.

After changing these settings, restart the API:

    sudo systemctl restart family-api.service

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

The repository includes `backup.sh` for application backups.

By default, backups are written below:

    /backup/familycollection

Run a backup with:

    cd /opt/familycollection
    sudo ./backup.sh

Each backup contains:

- a PostgreSQL custom-format dump;
- a gzip-compressed plain SQL dump;
- the complete runtime `data/` directory;
- the local `api/.env` configuration;
- the systemd service definition when available;
- deployment metadata including the Git commit and software versions.

The Python virtual environment and Git working tree are intentionally not copied. They can be recreated from the repository and dependency files.

### Backup destination

Override the default destination with `BACKUP_ROOT`:

    sudo BACKUP_ROOT=/mnt/backups/familycollection ./backup.sh

### Retention

The default retention period is 5 days.

Override it with:

    sudo BACKUP_RETENTION_DAYS=14 ./backup.sh

Set the value to `0` to disable automatic deletion:

    sudo BACKUP_RETENTION_DAYS=0 ./backup.sh

### Backup security

Backups contain the local `api/.env` file and therefore include database credentials, the session secret, and any configured metadata-provider API keys.

Backup directories are created with restrictive permissions, but they must still be treated as sensitive data. Do not publish them or commit them to Git.

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
