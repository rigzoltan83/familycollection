# FamilyCollection – metadata provider rendszer

## 1. Cél

A metadata provider rendszer feladata, hogy külső vagy belső
adatforrásokból tárgyadatokat keressen és egységes formátumban adjon
vissza.

A rendszernek támogatnia kell:

- több providert ugyanahhoz a kategóriához;
- kategóriánkénti prioritási sorrendet;
- provider engedélyezést és tiltást;
- rendszer- és háztartásszintű provider beállításokat;
- kézi adatbevitelt provider nélkül;
- új provider hozzáadását a kategóriák és az Item modell módosítása nélkül.

## 2. Példák providerekre

### Könyv

- Google Books
- Open Library
- ISBNdb
- ISBN Search
- Manual

### Társasjáték

- BoardGameGeek
- általános vonalkód-adatforrás
- Manual

### Film

- TMDB
- Manual

### Zene

- Discogs
- MusicBrainz
- Manual

### Videojáték

- IGDB
- RAWG
- Steam
- Manual

### Általános vagy saját kategória

- Generic Barcode
- CSV Import
- Manual
- később saját REST API

## 3. Provider és kategória különválasztása

A kategória azt mondja meg, hogy milyen tárgyat kezelünk.

A provider azt mondja meg, honnan próbálunk adatot szerezni.

Példa:

```text
Kategória: Könyv

Provider-sorrend:
1. Google Books
2. Open Library
3. ISBNdb
4. Manual
