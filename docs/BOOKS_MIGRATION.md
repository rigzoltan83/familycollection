# FamilyCollection – régi könyvek migrációs terve

## 1. Cél

A jelenlegi `books` tábla teljes adatállományát veszteség nélkül
átvezetjük az új, általános gyűjteményi modellbe.

Kiinduló állapot:

- régi könyvek száma: 1046;
- forrástábla: `books`;
- régi tárhelytábla: `locations`;
- új központi tábla: `collection_items`;
- új dinamikus mezők: `item_field_values`;
- új azonosítók: `item_identifiers`.

A migráció során a régi `books` és `locations` táblákat nem töröljük,
és nem módosítjuk destruktívan.

## 2. Biztonsági alapelvek

A migráció előtt:

- külön PostgreSQL mentés készül;
- ellenőrizzük a `books` és `locations` rekordszámát;
- ellenőrizzük az Alembic revisiont;
- a migráció külön tranzakcióban fut;
- hiba esetén teljes rollback történik.

A régi táblák az átállás után is megmaradnak visszaállási forrásként.

## 3. Forrásmezők

A jelenlegi `books` tábla mezői:

- `id`
- `isbn`
- `title`
- `author`
- `publisher`
- `publish_year`
- `location_id`
- `borrowed_to`
- `created`
- `updated`

## 4. Célmező-térkép

### `collection_items`

| Régi mező | Új mező | Megjegyzés |
|---|---|---|
| `books.id` | külön migrációs hivatkozás | Nem lesz új elsődleges kulcs |
| `title` | `collection_items.title` | Üres cím esetén külön hibajegyzék |
| nincs | `collection_items.household_id` | Alapértelmezett háztartás |
| nincs | `collection_items.category_id` | `book` rendszerkategória |
| nincs | `collection_items.status` | Alapérték: `active` |
| nincs | `collection_items.is_active` | Alapérték: `true` |
| `created` | `collection_items.created_at` | Eredeti időpont megőrzése |
| `updated` | `collection_items.updated_at` | Eredeti időpont megőrzése |

### `item_identifiers`

| Régi mező | Új mező |
|---|---|
| `isbn` | `identifier_value` |
| normalizálás eredménye | `identifier_type` |
| nincs | `is_primary = true` |
| nincs | `provider_code = NULL` |

Az ISBN normalizálása után:

- 10 számjegy → `isbn10`;
- 13 számjegy → `isbn13`;
- más érték → `custom`;
- üres érték → nem készül azonosítórekord.

### `item_field_values`

| Régi mező | Kategóriamező |
|---|---|
| `author` | `author` |
| `publisher` | `publisher` |
| `publish_year` | `publish_year` |

Az értékek céloszlopa:

- `author` → `value_text`;
- `publisher` → `value_text`;
- `publish_year` → első körben `value_integer`, ha szabályos év;
- szabálytalan `publish_year` → külön hibajegyzék vagy szöveges megőrzés.

### Tárhely

A régi `location_id` első migrációs körben nem kerül közvetlenül
az új `collection_items` táblába, mert az új tárhelymodell még nincs kész.

Addig külön migrációs térképben megőrizzük:

- régi `book_id`;
- régi `location_id`;
- helyiség;
- polc;
- pozíció.

### Kölcsönzés

A régi `borrowed_to` mezőt nem veszítjük el.

Első körben:

- külön migrációs hivatkozásban megőrizzük;
- később az új `loans` modellbe kerül;
- az átállásig a régi adat visszakereshető marad.

## 5. Migrációs hivatkozás

A migrált rekordokhoz egy külön technikai tábla készülhet:

`legacy_book_migrations`

Tervezett mezők:

- `id`
- `legacy_book_id`
- `collection_item_id`
- `legacy_location_id`
- `legacy_borrowed_to`
- `migration_status`
- `migration_notes`
- `created_at`

Egyedi kulcs:

- `legacy_book_id`

Ez biztosítja:

- az idempotens újrafuttatást;
- a régi és új rekordok összekapcsolását;
- a hibás rekordok listázását;
- az ellenőrizhető visszagörgetést.

## 6. Migrációs sorrend

1. mentés készítése;
2. forrásrekordok ellenőrzése;
3. `legacy_book_migrations` tábla létrehozása;
4. könyvenként `collection_items` rekord;
5. ISBN-ek migrálása;
6. dinamikus mezőértékek migrálása;
7. tárhelyhivatkozások megőrzése;
8. kölcsönzési adatok megőrzése;
9. darabszám-ellenőrzés;
10. hibajegyzék;
11. véletlenszerű rekordellenőrzés;
12. alkalmazás olvasási rétegének átállítása;
13. régi táblák csak olvasható állapotba helyezése.

## 7. Kötelező ellenőrzések

A migráció után:

- `books` rekordszám = migrációs hivatkozások száma;
- minden migrációs hivatkozás pontosan egy új Itemhez tartozik;
- nincs duplikált `legacy_book_id`;
- nincs árva `collection_item`;
- minden nem üres ISBN visszakereshető;
- az `author`, `publisher`, `publish_year` értékek összevethetők;
- a régi és új címek egyeznek;
- az eredeti dátumok megmaradtak.

## 8. Hibakezelés

A migráció nem hallgathatja el a hibás adatokat.

Külön listázandó:

- üres cím;
- érvénytelen ISBN;
- hibás év;
- hiányzó tárhely;
- nem létező `location_id`;
- duplikált régi rekord;
- váratlan adatbázishiba.

A hibás rekordok nem vesznek el, hanem `migration_status = error`
állapottal megmaradnak a migrációs naplóban.

## 9. Átállás

Az alkalmazás csak akkor vált át az új modellre, ha:

- minden rekord migrációs állapota ismert;
- a darabszámok egyeznek;
- a hibák átnézésre kerültek;
- a régi rendszerből történő visszaállás kipróbálható;
- az új listázás és keresés működik.

A régi `books` tábla törlése nem része az első átállásnak.
