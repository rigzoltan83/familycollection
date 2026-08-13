# FamilyCollection

FamilyCollection is a self-hosted collection management application for organizing books, board games, video games, and other personal or household collections.

The project is designed to provide a flexible, category-based system with custom fields, storage locations, metadata providers, image support, and a mobile-friendly web interface.

> **Project status:** Active development.  
> FamilyCollection is not yet considered production-ready for public deployment.

## Features

- Flexible collection categories
- Custom fields per category
- Storage locations and category-specific storage rules
- Item images
- Barcode and identifier support
- Book metadata support
- User authentication
- Household-based data model
- Mobile-friendly web interface
- PostgreSQL database
- FastAPI backend
- Database migrations with Alembic
- Self-hosted deployment

## Current Categories

FamilyCollection is designed to support multiple types of collections.

Current and planned examples include:

- Books
- Board games
- Video games
- Other customizable collection types

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

### Deployment

- Ubuntu Linux
- PostgreSQL 16
- Docker / Docker Compose for database services

## Repository Structure

```text
familycollection/
├── api/              Backend application
├── ui/               Web frontend
├── docs/             Project documentation
├── data/             Runtime data (not stored in Git)
├── backup.sh         Backup helper
├── docker-compose.yml
└── README.md
```

## Support

FamilyCollection is free and open-source software and is developed in my spare time.

If you find the project useful and would like to support its continued development, you can support my open-source work on Patreon:

**[Support me on Patreon](https://www.patreon.com/ZoltanRigo)**

Support is completely optional. FamilyCollection remains freely available under the GNU General Public License.

Think of it as buying me a coffee — or, if you really like the project, helping with a bottle of whiskey. 🥃

## License

Copyright (C) 2026 Zoltán Rigó

FamilyCollection is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

FamilyCollection is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

See the [LICENSE](LICENSE) file for the full license text.

Third-party components remain subject to their respective licenses.
See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for details.
