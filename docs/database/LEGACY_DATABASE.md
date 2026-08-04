# FamilyCollection – örökölt adatbázis

Ez a dokumentum a platformos átalakítás előtti működő adatbázis
kiinduló állapotát rögzíti.

## Alapelvek

- A meglévő `books` és `locations` táblák adatai megmaradnak.
- A baseline migráció nem hozza létre újra ezeket a táblákat.
- A későbbi migrációk csak bővítik vagy biztonságosan alakítják át a sémát.
- Oszlopot vagy táblát csak ellenőrzött adatmigráció után távolítunk el.
- Minden adatbázis-módosítás előtt külön mentés készül.

## Meglévő táblák

### `locations`

A jelenlegi fizikai helyek lapos szerkezetben:

- `room`
- `shelf`
- `slot`

Később ebből készül a hierarchikus szerkezet:

- `rooms`
- `storage_units`
- `storage_locations`

A régi `locations` tábla az átállás alatt megmarad.

### `books`

A jelenlegi könyvállomány fő mezői:

- `isbn`
- `title`
- `author`
- `publisher`
- `publish_year`
- `location_id`
- `borrowed_to`
- `created`
- `updated`

Az általános `items` modell bevezetéséig ez marad az elsődleges könyvtábla.

A tervezett átmeneti bővítések:

- `household_id`
- később `category_id`
- kapcsolat az új tárhelystruktúrához

## Baseline migráció

Az első Alembic revision nem hoz létre és nem töröl adatbázis-objektumot.

Feladata kizárólag az, hogy az Alembic a jelenlegi működő adatbázist
hivatalos kiindulópontként kezelje.
