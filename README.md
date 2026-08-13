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
