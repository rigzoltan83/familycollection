"use strict";

(function () {
    const STORAGE_KEY = "familycollection_language";
    const DEFAULT_LANGUAGE = "en";
    const SUPPORTED_LANGUAGES = ["en", "hu"];

    const translations = {
        en: {
"common.back_dashboard": "Dashboard",

"books.metadata.save_error":
    "❌ Failed to save book metadata: {message}",

"books.scanner.configuring":
    "Configuring camera...",

"books.scanner.searching_isbn":
    "Searching for the book's ISBN barcode...",

"books.scanner.camera_error":
    "❌ Camera error: {message}",

"books.scanner.not_book_isbn":
    "Not a book ISBN: {code}",

"books.scanner.searching_barcode":
    "Searching for barcode...",

"books.scanner.detected_progress":
    "Detected ISBN: {code} ({count}/2)",

"books.scanner.detected":
    "✅ Detected ISBN: {code}",
"books.scanner.library_missing":
    "❌ The Quagga2 library failed to load.",

"books.manual.save_error":
    "❌ Failed to add book: {message}",

"books.latest.slot":
    "Slot {slot}",

"books.latest.untitled":
    "Untitled book",

"books.latest.unique_index":
    "Unique index: {id}",

"books.latest.load_failed":
    "❌ Failed to load the list.",

"books.manual.identifier_required":
    "❌ Enter an identifier or call number.",

"books.manual.title_required":
    "❌ Enter the book title.",

"books.manual.storage_required":
    "❌ Select a storage location.",
"books.save.error":
    "❌ Save error: {message}",

"books.latest.empty":
    "No books have been added yet.",

"books.latest.cover_alt":
    "{title} cover image",

"books.common.book":
    "Book",

"books.latest.location_missing":
    "Not specified",

"books.latest.borrowed_by":
    "Loaned to: {borrower}",

"common.other":
    "Other",

"common.saving":
    "Saving...",

"books.storage.location_label":
    "{room} / {shelf} / Storage {slot}",

"books.storage.invalid_response":
    "The storage/tree endpoint returned an invalid response.",

"books.validation.select_storage_first":
    "❌ Select a storage location first.",

"books.validation.isbn_required":
    "❌ Enter the ISBN.",

"books.validation.isbn_length":
    "❌ The ISBN must contain 10 or 13 digits.",

"books.validation.borrower_required":
    "❌ Enter who has the book.",

"books.metadata.not_found":
    "⚠️ No book metadata was found. Enter the details manually.",
"books.create.success_with_images":
    "✅ Book added. Unique index: {id}. {count} images uploaded. Original size: {originalSize} → uploaded: {uploadedSize}.",

"books.create.success":
    "✅ Book added. Unique index: {id}.",
"books.images.upload_failed":
    "{message} Uploaded: {uploaded} / {total}. Remaining: {remaining}.",

"books.create.missing_public_id":
    "The book was created, but the server did not return a public_id value.",

"books.create.upload_progress":
    "✅ Book added. Uploading images: {current} / {total}...",
"books.images.count":
    "{count} images selected",

"books.images.selected_alt":
    "Selected image {number}",

"books.images.move_left":
    "Move left",

"books.images.move_right":
    "Move right",

"books.images.remove":
    "Remove image",

"books.images.remove_number":
    "Remove image {number}",

"books.images.resize_failed":
    "Image resizing failed.",

"books.images.compress_failed":
    "Image compression failed.",

"books.images.missing_item_id":
    "The identifier of the created collection item is missing.",
"books.images.help":
    "Images are uploaded automatically after the book is saved successfully.",

"books.scanner.live":
    "📷 Live ISBN scanning",

"books.main.save_book":
    "💾 Add book",

"books.manual.open":
    "📕 Add book without ISBN",

"books.latest.title":
    "Last 20 books",
"books.images.title": "Images",
"books.images.count_zero": "0 images selected",
"books.images.empty":
    "No images selected for this book yet.",
"books.images.take_photo":
    "📷 Take photo",
"books.images.select":
    "🖼️ Select images",
"books.images.clear":
    "🧹 Clear images",
"books.main.title":
    "📚 FamilyCollection Library",

"books.main.book_list":
    "📖 Book list",

"books.main.export_csv":
    "⬇️ Download complete database as CSV",

"books.main.storage":
    "1. Book storage location",

"books.status.removed":
    "Removed from shelf",

"books.status.borrowed":
    "Loaned",

"books.main.borrower_question":
    "Who has the book?",

"books.placeholder.borrower_name":
    "Name...",

"books.field.notes":
    "Notes",

"books.placeholder.notes":
    "Optional notes...",

"books.main.isbn":
    "2. ISBN",

"books.placeholder.isbn":
    "Enter or scan the ISBN...",
"books.manual.title":
    "Add book without ISBN",

"books.field.identifier":
    "Identifier / call number",

"books.placeholder.identifier":
    "e.g. MSZ 1234, inventory number...",

"books.placeholder.year":
    "e.g. 1956",
"books.scanner.title": "📷 Scan ISBN",
"books.scanner.close": "Close camera",
"books.scanner.guide":
    "Hold the book's EAN-13 barcode horizontally in the center of the red frame.",
"books.scanner.starting":
    "Starting camera...",
"books.page_title":
    "FamilyCollection – Books",

"books.metadata.title":
    "Enter book details",

"books.metadata.description":
    "No usable book metadata was found for this ISBN. Enter the details manually:",

"books.field.title": "Title",
"books.field.author": "Author",
"books.field.publisher": "Publisher",
"books.field.publish_year": "Publication year",
"books.field.storage": "Storage location",
"books.field.borrower": "Borrower",

"books.placeholder.title": "Book title",
"books.placeholder.author": "Author name",
"books.placeholder.publisher": "Publisher",
"books.placeholder.borrower":
    "Only when the book is loaned",

"books.storage.select":
    "-- select storage location --",
            "common.loading": "Loading...",
            "common.save": "Save",
            "common.saving": "Saving...",
            "common.cancel": "Cancel",
            "common.create": "Create",
            "common.creating": "Creating...",
            "common.delete": "Delete",
            "common.edit": "Edit",
            "common.close": "Close",
            "common.refresh": "Refresh",
            "common.active": "Active",
            "common.inactive": "Inactive",
            "common.yes": "Yes",
            "common.no": "No",

"dashboard.load_failed":
    "Failed to load: {message}",
"dashboard.books.title": "Books",
"dashboard.books.description":
    "Add books and view the most recently recorded items.",

"dashboard.booklist.title": "Book list",
"dashboard.booklist.description":
    "Search and browse the complete book collection.",

"dashboard.custom_collection.description":
    "Custom collection.",

"dashboard.no_household":
    "No active household membership.",

"dashboard.categories_load_failed":
    "Failed to load collections: HTTP {status}",

"dashboard.permission":
    "Permission: {role}",
"dashboard.admin.title": "Administration",
"dashboard.admin.description":
    "Users, collections and storage locations.",

"role.owner": "Owner",
"role.admin": "Administrator",
"role.editor": "Editor",
"role.viewer": "Viewer",

            "nav.logout": "Log out",

            "language.english": "English",
            "language.hungarian": "Magyar",

            "login.error.invalid_credentials":
                "Invalid email address, username, or password.",
"login.error.generic": "Login failed.",
"login.error.http": "Login failed (HTTP {status}).",
"login.title": "FamilyCollection – Login",
"login.subtitle": "Sign in to manage your collections.",
"login.username": "Email address or username",
"login.password": "Password",
"login.submit": "Sign in",
"login.identifier_placeholder": "e.g. admin or name@example.com"
        },

        hu: {
"common.back_dashboard": "Vissza a főoldalra",

"books.metadata.save_error":
    "❌ Kézi metaadatmentési hiba: {message}",

"books.scanner.configuring":
    "Kamera beállítása...",

"books.scanner.searching_isbn":
    "Keresem a könyv ISBN-vonalkódját...",

"books.scanner.camera_error":
    "❌ Kamerahiba: {message}",

"books.scanner.not_book_isbn":
    "Nem könyv-ISBN: {code}",

"books.scanner.searching_barcode":
    "Keresem a vonalkódot...",

"books.scanner.detected_progress":
    "Felismert ISBN: {code} ({count}/2)",

"books.scanner.detected":
    "✅ Felismert ISBN: {code}",
"books.scanner.library_missing":
    "❌ A Quagga2 könyvtár nem töltődött be.",

"books.manual.save_error":
    "❌ Kézi könyvfelviteli hiba: {message}",

"books.latest.slot":
    "{slot}. hely",

"books.latest.untitled":
    "Névtelen könyv",

"books.latest.unique_index":
    "Egyedi index: {id}",

"books.latest.load_failed":
    "❌ Nem sikerült betölteni a listát.",

"books.manual.identifier_required":
    "❌ Adj meg azonosítót vagy jelzetet.",

"books.manual.title_required":
    "❌ Add meg a könyv címét.",

"books.manual.storage_required":
    "❌ Válassz tárhelyet.",
"books.save.error":
    "❌ Mentési hiba: {message}",

"books.latest.empty":
    "Még nincs felvett könyv.",

"books.latest.cover_alt":
    "{title} borítóképe",

"books.common.book":
    "Könyv",

"books.latest.location_missing":
    "Nincs megadva",

"books.latest.borrowed_by":
    "Kölcsönadva: {borrower}",

"common.other":
    "Egyéb",

"common.saving":
    "Mentés...",

"books.storage.location_label":
    "{room} / {shelf} / Tárhely {slot}",

"books.storage.invalid_response":
    "A storage/tree hibás választ adott.",

"books.validation.select_storage_first":
    "❌ Először válassz tárhelyet.",

"books.validation.isbn_required":
    "❌ Add meg az ISBN-t.",

"books.validation.isbn_length":
    "❌ Az ISBN 10 vagy 13 számjegyből álljon.",

"books.validation.borrower_required":
    "❌ Add meg, kinél van a könyv.",

"books.metadata.not_found":
    "⚠️ Nem találtam könyvadatokat. Add meg őket kézzel.",
"books.create.success_with_images":
    "✅ Könyv felvéve. Egyedi index: {id}. {count} kép feltöltve. Eredeti méret: {originalSize} → feltöltve: {uploadedSize}.",

"books.create.success":
    "✅ Könyv felvéve. Egyedi index: {id}.",
"books.images.upload_failed":
    "{message} Feltöltve: {uploaded} / {total}. Hátralévő: {remaining}.",

"books.create.missing_public_id":
    "A könyv létrejött, de a szerver nem adott vissza public_id értéket.",

"books.create.upload_progress":
    "✅ Könyv felvéve. Képek feltöltése: {current} / {total}...",
"books.images.count":
    "{count} kép kiválasztva",

"books.images.selected_alt":
    "Kiválasztott kép {number}",

"books.images.move_left":
    "Mozgatás balra",

"books.images.move_right":
    "Mozgatás jobbra",

"books.images.remove":
    "Kép eltávolítása",

"books.images.remove_number":
    "{number}. kép eltávolítása",

"books.images.resize_failed":
    "A kép átméretezése nem sikerült.",

"books.images.compress_failed":
    "A kép tömörítése nem sikerült.",

"books.images.missing_item_id":
    "Hiányzik a létrehozott gyűjteményi elem azonosítója.",
"books.images.help":
    "A képek a könyv sikeres mentése után automatikusan feltöltődnek.",

"books.scanner.live":
    "📷 Élő ISBN-beolvasás",

"books.main.save_book":
    "💾 Könyv felvétele",

"books.manual.open":
    "📕 ISBN nélküli könyv felvitele",

"books.latest.title":
    "Utolsó 20 könyv",
"books.images.title": "Képek",
"books.images.count_zero": "0 kép kiválasztva",
"books.images.empty":
    "A könyvhöz még nincs kép kiválasztva.",
"books.images.take_photo":
    "📷 Fotó készítése",
"books.images.select":
    "🖼️ Képek kiválasztása",
"books.images.clear":
    "🧹 Képek törlése",
"books.main.title":
    "📚 A Rigó család könyvtára",

"books.main.book_list":
    "📖 Könyvek listája",

"books.main.export_csv":
    "⬇️ Teljes adatbázis letöltése CSV-ben",

"books.main.storage":
    "1. Könyv tárhelye",

"books.status.removed":
    "Polcról levéve",

"books.status.borrowed":
    "Kölcsönadva",

"books.main.borrower_question":
    "Kinek van kölcsönadva?",

"books.placeholder.borrower_name":
    "Név...",

"books.field.notes":
    "Megjegyzés",

"books.placeholder.notes":
    "Opcionális megjegyzés...",

"books.main.isbn":
    "2. ISBN",

"books.placeholder.isbn":
    "Írd be vagy olvasd be az ISBN-t...",
"books.manual.title":
    "ISBN nélküli könyv felvitele",

"books.field.identifier":
    "Azonosító / jelzet",

"books.placeholder.identifier":
    "Pl. MSZ 1234, leltári szám...",

"books.placeholder.year":
    "Pl. 1956",
"books.scanner.title": "📷 ISBN beolvasása",
"books.scanner.close": "Kamera bezárása",
"books.scanner.guide":
    "Tartsd a könyv EAN-13 vonalkódját vízszintesen a piros keret közepére.",
"books.scanner.starting":
    "Kamera indítása...",
"books.page_title":
    "A Rigó család könyvtára",

"books.metadata.title":
    "Könyvadatok megadása",

"books.metadata.description":
    "Ehhez az ISBN-hez nem találtam használható könyvadatokat. Add meg kézzel:",

"books.field.title": "Cím",
"books.field.author": "Szerző",
"books.field.publisher": "Kiadó",
"books.field.publish_year": "Kiadás éve",
"books.field.storage": "Tárhely",
"books.field.borrower": "Kölcsönző neve",

"books.placeholder.title": "Könyv címe",
"books.placeholder.author": "Szerző neve",
"books.placeholder.publisher": "Kiadó",
"books.placeholder.borrower":
    "Csak kölcsönadás esetén",

"books.storage.select":
    "-- válassz tárhelyet --",
            "common.loading": "Betöltés...",
            "common.save": "Mentés",
            "common.saving": "Mentés...",
            "common.cancel": "Mégse",
            "common.create": "Létrehozás",
            "common.creating": "Létrehozás...",
            "common.delete": "Törlés",
            "common.edit": "Szerkesztés",
            "common.close": "Bezárás",
            "common.refresh": "Frissítés",
            "common.active": "Aktív",
            "common.inactive": "Inaktív",
            "common.yes": "Igen",
            "common.no": "Nem",

"dashboard.load_failed":
    "Nem sikerült betölteni: {message}",
"dashboard.books.title": "Könyvek",
"dashboard.books.description":
    "Könyvek felvitele és a legutóbb rögzített példányok.",

"dashboard.booklist.title": "Könyvlista",
"dashboard.booklist.description":
    "A teljes könyvgyűjtemény keresése és megtekintése.",

"dashboard.custom_collection.description":
    "Saját gyűjtemény.",

"dashboard.no_household":
    "Nincs aktív háztartási tagság.",

"dashboard.categories_load_failed":
    "A gyűjtemények betöltése sikertelen: HTTP {status}",

"dashboard.permission":
    "Jogosultság: {role}",
"dashboard.admin.title": "Adminisztráció",
"dashboard.admin.description":
    "Felhasználók, gyűjtemények és tárhelyek.",

"role.owner": "Tulajdonos",
"role.admin": "Adminisztrátor",
"role.editor": "Szerkesztő",
"role.viewer": "Megtekintő",

            "nav.logout": "Kilépés",

            "language.english": "English",
            "language.hungarian": "Magyar",

            "login.error.invalid_credentials":
                "Hibás e-mail cím, felhasználónév vagy jelszó.",
            "login.error.generic": "A bejelentkezés nem sikerült.",
            "login.error.http": "A bejelentkezés nem sikerült (HTTP {status}).",
            "login.title": "FamilyCollection – Belépés",
            "login.subtitle": "Jelentkezz be a gyűjtemények kezeléséhez.",
            "login.username": "E-mail cím vagy felhasználónév",
            "login.password": "Jelszó",
            "login.submit": "Belépés",
            "login.identifier_placeholder": "pl. admin vagy nev@example.com"
        }
    };

    function normalizeLanguage(language) {
        if (!language) {
            return DEFAULT_LANGUAGE;
        }

        const normalized = String(language)
            .trim()
            .toLowerCase()
            .split("-")[0];

        if (SUPPORTED_LANGUAGES.includes(normalized)) {
            return normalized;
        }

        return DEFAULT_LANGUAGE;
    }

    function getLanguage() {
        const stored = localStorage.getItem(STORAGE_KEY);

        if (stored) {
            return normalizeLanguage(stored);
        }

        return DEFAULT_LANGUAGE;
    }

    function translate(key, replacements = {}) {
        const language = getLanguage();

        let text =
            translations[language]?.[key]
            ?? translations[DEFAULT_LANGUAGE]?.[key]
            ?? key;

        Object.entries(replacements).forEach(
            ([name, value]) => {
                text = text.replaceAll(
                    `{${name}}`,
                    String(value)
                );
            }
        );

        return text;
    }

    function applyTranslations(root = document) {
        root
            .querySelectorAll("[data-i18n]")
            .forEach(element => {
                const key = element.dataset.i18n;
                element.textContent = translate(key);
            });

        root
            .querySelectorAll("[data-i18n-placeholder]")
            .forEach(element => {
                const key =
                    element.dataset.i18nPlaceholder;

                element.placeholder = translate(key);
            });

        root
            .querySelectorAll("[data-i18n-title]")
            .forEach(element => {
                const key =
                    element.dataset.i18nTitle;

                element.title = translate(key);
            });

root
    .querySelectorAll("[data-i18n-aria-label]")
    .forEach(element => {
        const key =
            element.dataset.i18nAriaLabel;

        element.setAttribute(
            "aria-label",
            translate(key)
        );
    });

        document.documentElement.lang =
            getLanguage();
    }

    function setLanguage(language) {
        const normalized =
            normalizeLanguage(language);

        localStorage.setItem(
            STORAGE_KEY,
            normalized
        );

        applyTranslations();

        document.dispatchEvent(
            new CustomEvent(
                "familycollection:languagechange",
                {
                    detail: {
                        language: normalized
                    }
                }
            )
        );
    }

    function init() {
        applyTranslations();
    }

    window.FamilyCollectionI18n = {
        t: translate,
        getLanguage,
        setLanguage,
        applyTranslations,
        supportedLanguages:
            [...SUPPORTED_LANGUAGES]
    };

    if (document.readyState === "loading") {
        document.addEventListener(
            "DOMContentLoaded",
            init
        );
    } else {
        init();
    }
})();
