"""
FamilyCollection konfigurációs mintafájl.

Használat:
    cp api/config.example.py api/config.py

Ezután az api/config.py fájlban kell megadni a helyi adatbázis-
és külső szolgáltatási adatokat.

Az api/config.py nincs Gitben, mert titkos adatokat tartalmazhat.
"""

DB_HOST = "localhost"
DB_PORT = 5432

DB_NAME = "familycollection"
DB_USER = "familyuser"
DB_PASS = "CHANGE_ME"

# Külső metadata-szolgáltatások
ISBNDB_KEY = ""

# Metadata-szolgáltatók használati sorrendje
USE_ISBNDB = False
USE_OPENLIBRARY = True
USE_ISBNSEARCH = True
