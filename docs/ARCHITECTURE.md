# FamilyCollection platformarchitektúra

## 1. A projekt célja

A FamilyCollection egy többfelhasználós, több háztartást kezelő
gyűjtemény- és otthoni leltárplatform.

A rendszer hosszú távú célja, hogy különféle tárgytípusokat kezeljen,
például:

- könyvek;
- társasjátékok;
- videojátékok;
- filmek és zenei kiadványok;
- elektronikai eszközök;
- szerszámok;
- egyéb otthoni tárgyak és gyűjtemények.

A könyv nem különálló rendszer lesz, hanem egy támogatott kategória az
általános tárgymodellen belül.

## 2. Fejlesztési alapelvek

### 2.1. Adatvesztés nélküli fejlesztés

A jelenlegi adatbázis és a meglévő könyvállomány megmarad.

Meglévő táblát vagy oszlopot csak akkor távolítunk el, ha:

1. az adatokat már biztonságosan átmigráltuk;
2. az új rendszer működését ellenőriztük;
3. megfelelő adatbázis-mentés készült;
4. a változtatás külön Git-commitban szerepel.

### 2.2. Kis lépések

Minden logikai fejlesztési lépés után:

1. ellenőrizzük a program működését;
2. ellenőrizzük az adatokat;
3. készítünk egy Git-commitot;
4. csak ezután lépünk tovább.

### 2.3. Visszafelé kompatibilitás

Az átalakítás alatt a jelenlegi API-végpontokat és felhasználói
funkciókat lehetőség szerint működőképesen tartjuk.

Az új rendszer fokozatosan veszi át a régi modulok feladatait.

### 2.4. Bővíthetőség

Az új kategóriák, metadata-szolgáltatók, tárhelytípusok és
jogosultságok lehetőleg adminfelületen vagy moduláris szolgáltatásokkal
legyenek bővíthetők.

Kerüljük az olyan megoldásokat, amelyek minden új kategóriához a teljes
alkalmazás átírását igénylik.

## 3. Jelenlegi technológiai alap

A jelenlegi rendszer fő elemei:

- FastAPI backend;
- Uvicorn alkalmazásszerver;
- PostgreSQL adatbázis;
- psycopg2 kapcsolatkezelés;
- ThreadedConnectionPool;
- statikus HTML, CSS és JavaScript felület;
- külső könyv-metadata szolgáltatók;
- Docker Compose alatt futó PostgreSQL.

Ezeket nem cseréljük le egyetlen nagy átalakításban.

## 4. Tervezett technológiai irány

### 4.1. Backend

A FastAPI marad a backend keretrendszer.

A jelenlegi nagyobb Python-fájlokat fokozatosan külön modulokra bontjuk:

- API route-ok;
- adatbázis-kezelés;
- sémák;
- üzleti szolgáltatások;
- metadata-szolgáltatók;
- autentikáció;
- adminisztráció.

### 4.2. Adatbázis

A PostgreSQL marad az elsődleges adatbázis.

A jelenlegi közvetlen psycopg2 SQL-lekérdezéseket nem töröljük azonnal.

A migrációs rendszert Alembic biztosítja majd.

Az új platformmodelleknél fokozatosan bevezetjük:

- SQLAlchemy 2;
- deklaratív modelleket;
- verziózott adatbázis-migrációkat;
- adatbázis-kapcsolatok és tranzakciók egységes kezelését.

### 4.3. Felhasználói felület

A jelenlegi HTML, CSS és JavaScript felület az átalakítás alatt megmarad.

Később a felület PWA-ként is használható lesz:

- asztali böngészőben;
- Android-eszközön;
- iPhone-on;
- táblagépen.

Natív mobilalkalmazás csak akkor készül, ha valódi igény indokolja.

## 5. Központi adatmodell

A rendszer központi fogalmai:

### Household

Egy család, háztartás vagy közösen kezelt gyűjtemény.

Minden felhasználói adat egy háztartáshoz kapcsolódik.

### User

Bejelentkezésre képes személy.

Egy felhasználó több háztartásnak is tagja lehet.

### HouseholdMember

A felhasználó és a háztartás közötti kapcsolat.

A tagsághoz szerepkör és jogosultság tartozik.

### Category

Egy tárgy típusa vagy kategóriája.

Példák:

- könyv;
- társasjáték;
- videojáték;
- elektronikai eszköz;
- egyéb tárgy.

A kategória meghatározhatja:

- az elérhető mezőket;
- a használható metadata-szolgáltatókat;
- a vonalkód-keresési viselkedést;
- a megjelenítési szabályokat.

### Item

A rendszer által nyilvántartott általános tárgy.

Minden könyv, társasjáték vagy más nyilvántartott objektum egy Item.

### Room

Helyiség egy háztartáson belül.

Példák:

- nappali;
- dolgozószoba;
- garázs;
- pince.

### StorageUnit

Egy helyiségen belüli tárolóegység.

Példák:

- könyvespolc;
- szekrény;
- fiókos szekrény;
- tárolódoboz.

### StorageLocation

Egy konkrét tárhely a tárolóegységen belül.

Példák:

- első polc;
- felső fiók;
- második rekesz;
- doboz belső pozíciója.

### MetadataProvider

Külső vagy belső szolgáltatás, amely vonalkód vagy más azonosító alapján
adatokat keres.

Példák:

- ISBNdb;
- Open Library;
- későbbi társasjáték-adatforrás;
- helyi vagy közösségi metadata-adatbázis.

## 6. Tervezett jogosultsági modell

Az első változat szerepkörei:

### Owner

- háztartás kezelése;
- tagok meghívása és eltávolítása;
- jogosultságok módosítása;
- teljes adminisztráció;
- adatok exportálása és törlése.

### Admin

- kategóriák kezelése;
- helyiségek és tárhelyek kezelése;
- tárgyak létrehozása és módosítása;
- tagok megtekintése;
- rendszerbeállítások kezelése a háztartáson belül.

### Editor

- tárgyak létrehozása;
- tárgyak szerkesztése;
- kölcsönadások kezelése;
- vonalkódos adatbevitel.

### Viewer

- gyűjtemény megtekintése;
- keresés;
- adatok módosítása nélkül.

A platformszintű rendszergazda külön szerepkör lesz, és nem azonos a
háztartás adminisztrátorával.

## 7. Metadata-keresési elv

A metadata-szolgáltatók egységes interfészt követnek.

Egy szolgáltató feladata:

1. eldönteni, hogy támogatja-e az adott kategóriát és azonosítót;
2. lekérdezni a külső adatforrást;
3. egységes formátumra alakítani a választ;
4. jelezni, ha nincs használható találat.

A szolgáltatók prioritási sorrendje konfigurálható lesz.

A metadata-találat csak adatbeviteli segítség.

A rendszernek akkor is használhatónak kell maradnia, ha egyik külső
szolgáltató sem talál adatot.

## 8. Adatbiztonsági alapelvek

Minden háztartáshoz tartozó lekérdezésnek kötelezően szűrnie kell a
háztartás azonosítójára.

Egy felhasználó soha nem férhet hozzá olyan háztartás adataihoz,
amelynek nem tagja.

A jelszavak és API-kulcsok:

- nem kerülhetnek Gitbe;
- nem lehetnek a forráskódba írva;
- környezeti változókból vagy helyi konfigurációból töltődnek be.

## 9. Mentési alapelvek

A fizetős vagy többfelhasználós rendszer bevezetése előtt szükséges:

- napi PostgreSQL-mentés;
- feltöltött fájlok mentése;
- külső fizikai helyen tárolt mentési példány;
- több verzió megőrzése;
- rendszeres visszaállítási próba;
- sikertelen mentés esetén riasztás.

A mentés akkor tekinthető működőnek, ha azt tesztelten vissza lehet
állítani.

## 10. Fejlesztési szakaszok

### 0. szakasz – Stabil kiindulópont

- Git-verziókezelés;
- titkos fájlok kizárása;
- jelenlegi függőségek rögzítése;
- jelenlegi adatbázis mentése;
- működő régi verzió megjelölése.

### 1. szakasz – Fejlesztői alapok

- környezeti változók;
- egységes konfiguráció;
- Python-csomagstruktúra;
- Alembic;
- SQLAlchemy alapok;
- automatikus alapellenőrzések.

### 2. szakasz – Többfelhasználós alap

- households;
- users;
- household_members;
- szerepkörök;
- bejelentkezés;
- munkamenet-kezelés.

### 3. szakasz – Adminisztráció

- platformadmin;
- háztartási admin;
- felhasználók kezelése;
- meghívások;
- jogosultságok.

### 4. szakasz – Helystruktúra

- rooms;
- storage_units;
- storage_locations;
- adminfelület;
- a meglévő locations adatok migrációja.

### 5. szakasz – Kategóriák

- categories;
- adminfelületi bővíthetőség;
- kategóriánkénti metadata-beállítás;
- könyv alapértelmezett kategóriaként.

### 6. szakasz – Általános Item modell

- items;
- meglévő books adatok migrációja;
- kategóriaspecifikus adatok;
- a régi API-k visszafelé kompatibilis kezelése.

### 7. szakasz – Termékesítéshez szükséges funkciók

- előfizetés és csomagok;
- adat-export;
- fióktörlés;
- naplózás;
- monitorozás;
- backup-riasztások;
- adatvédelmi funkciók.

## 11. Nem cél az első szakaszban

Az első platformverzióban nem cél:

- Kubernetes;
- mikroszolgáltatásos architektúra;
- natív Android- és iOS-alkalmazás;
- saját globális termékadatbázis;
- mesterséges intelligencia minden funkcióban;
- idő előtti teljesítményoptimalizálás.

Először egy stabil, egyszerűen üzemeltethető és biztonságosan bővíthető
rendszert építünk.
