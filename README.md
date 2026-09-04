# FamilyCollection

Self-hosted collection management for books, board games, video games, and other personal or household collections.

FamilyCollection provides a flexible category-based system for organizing physical and digital collections without depending on a hosted service. It combines customizable fields, hierarchical storage locations, metadata lookup, images, barcode support, and household-based access in a mobile-friendly web interface.

> **Project status:** Active development. FamilyCollection is usable for testing and personal deployments, but is not yet considered production-ready for unrestricted public Internet exposure.

## Features

- Flexible collection categories
- Custom fields for category-specific metadata
- Hierarchical storage locations
- Category-specific storage rules
- Item image management
- Barcode and identifier support
- Book metadata lookup
- User authentication
- Household-based data separation
- Mobile-friendly web interface
- PostgreSQL storage
- Alembic database migrations
- Self-hosted deployment
- Root-domain and reverse-proxy subpath deployment

## Collection Types

FamilyCollection is designed around a generic item model rather than a single hard-coded collection type.

Examples include:

- Books
- Board games
- Video games
- Other user-defined collection types

Books currently have the most mature specialized workflow, including ISBN-based metadata lookup and barcode scanning.

## Quick Start

The supported installation target is currently Ubuntu 24.04.

Clone the repository:

    cd /opt
    sudo git clone https://github.com/rigzoltan83/familycollection.git familycollection
    sudo chown -R "$USER":"$(id -gn)" /opt/familycollection
    cd /opt/familycollection

Run the installer:

    sudo ./install.sh

Then create the first administrator:

    cd /opt/familycollection/api
    venv/bin/python scripts/bootstrap_admin.py

For complete installation, HTTPS, subpath deployment, service management, migrations, testing, and backup instructions, see [docs/INSTALL.md](docs/INSTALL.md).

## Deployment

The standard deployment uses:

- Ubuntu 24.04
- Python / FastAPI / Uvicorn
- PostgreSQL 16
- Docker Compose for the PostgreSQL service
- systemd for the FamilyCollection API

FamilyCollection can run directly at the root of a host or behind a reverse proxy under a URL prefix such as `/familycollection`.

HTTPS is strongly recommended outside a trusted local network.

## Technology

### Backend

- Python
- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL

### Frontend

- HTML
- CSS
- JavaScript
- QuaggaJS for browser-based barcode scanning

## Repository Structure

    familycollection/
    ├── api/                 Backend application and migrations
    ├── docs/                Project documentation
    ├── scripts/             Import and maintenance helpers
    ├── ui/                  Web frontend
    ├── backup.sh            Backup helper
    ├── docker-compose.yml   PostgreSQL service
    ├── install.sh           Ubuntu installation helper
    └── README.md

Runtime data, local configuration, database dumps, imports, backups, and uploaded images are intentionally excluded from Git.

## Configuration

Local configuration is stored in `api/.env` and is never intended to be committed.

Use `api/.env.example` as the configuration reference.

The installer generates database and session secrets automatically for a fresh installation.

## Data and Privacy

The public repository does not contain a production collection database or personal collection data.

Fresh installations start with their own database. Local runtime data, database dumps, imports, uploaded images, and environment files are excluded through `.gitignore`.

Never commit real passwords, API keys, database dumps, or personal collection exports.

## Documentation

- [Installation and operations](docs/INSTALL.md)
- [Third-party notices](THIRD_PARTY_NOTICES.md)
- [License](LICENSE)

Additional architecture and migration documentation is being reviewed and updated as the project evolves.

## Development and Tests

The test suite uses a dedicated PostgreSQL test database configured by `TEST_DATABASE_NAME`.

Install development dependencies and run the tests from the API directory:

    cd /opt/familycollection/api
    venv/bin/pip install -r requirements-dev.in
    venv/bin/python -m pytest -q

Tests must never be pointed at a production database.

## Support

FamilyCollection is free and open-source software developed in my spare time.

If you find the project useful and would like to support continued development, you can support my open-source work on Patreon:

[Support my open-source work on Patreon](https://www.patreon.com/ZoltanRigo)

Support is entirely optional. FamilyCollection remains freely available under the GNU General Public License.

## License

Copyright (C) 2026 Zoltán Rigó

FamilyCollection is licensed under the GNU General Public License, version 3 or any later version.

See [LICENSE](LICENSE) for the complete license text.

Third-party components remain subject to their respective licenses. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for details.
