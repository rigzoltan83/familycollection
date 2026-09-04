# FamilyCollection Demo Environment

This directory contains tooling for creating an isolated demonstration
environment for FamilyCollection.

The demo environment is intended for:

- screenshots;
- development;
- UI demonstrations;
- testing example collections.

It must never use production collection data.

## Safety

The demo database name is fixed to:

    familycollection_demo

Demo scripts refuse to operate on another database where destructive or
demo-specific operations could affect a real installation.

The demo environment uses:

    demo/.env
    demo/data/

These runtime files are not intended for Git.

## Create the demo database

    ./demo/create_demo_db.sh

## Apply migrations

    ./demo/run_alembic.sh

Synthetic demo data is created separately by the demo seed script.
