# FamilyCollection – dinamikus kategória- és mezőrendszer

## 1. Cél

A FamilyCollection ne csak előre beépített tárgytípusokat kezeljen.

A rendszernek támogatnia kell:

- előre definiált rendszerkategóriákat;
- háztartásonként létrehozható saját kategóriákat;
- kategóriánként definiálható egyedi mezőket;
- új kategóriák és mezők létrehozását adatbázis-migráció nélkül.

Példák:

- könyv;
- társasjáték;
- videojáték;
- film;
- zenei kiadvány;
- bélyeg;
- bankjegy;
- érme;
- kőzet;
- szerszám;
- elektronikai eszköz;
- növény;
- tetszőleges saját kategória.

## 2. Központi elv

Minden nyilvántartott tárgy egy általános `Item`.

Az `Item` tartalmazza a minden kategóriánál közös adatokat.

A kategóriaspecifikus adatok külön dinamikus mezőrendszerben tárolódnak.

Példa:

```text
Item
├── title
├── barcode
├── category_id
├── household_id
├── storage_location_id
├── notes
└── category-specific values
