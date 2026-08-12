"use strict";

(function () {
    const STORAGE_KEY = "familycollection_language";
    const DEFAULT_LANGUAGE = "en";
    const SUPPORTED_LANGUAGES = ["en", "hu"];

    const translations = {
        en: {
"books.list.images.close_preview":
    "Close image",

"books.list.permissions_load_failed":
    "❌ Failed to load permission data.",

"books.list.edit.save_error":
    "❌ Save error: {message}",

"books.list.edit.isbn_required":
    "❌ ISBN cannot be empty.",

"books.list.edit.title_required":
    "❌ Title cannot be empty.",

"books.list.edit.storage_required":
    "❌ Select a storage location.",

"books.list.edit.borrower_required":
    "❌ Enter who has the book.",

"books.list.images.default_caption":
    "Image",

"books.list.images.primary_badge":
    "Primary",

"books.list.images.move_left_button":
    "← Left",

"books.list.images.move_right_button":
    "Right →",

"books.list.images.current_primary":
    "⭐ Current cover image",

"books.list.images.make_primary":
    "⭐ Set as cover image",

"books.list.images.delete_button":
    "🗑 Delete",

"books.list.images.delete_confirm":
    "Are you sure you want to delete this image?",

"books.list.images.deleting":
    "Deleting image...",

"books.list.images.deleted":
    "✅ Image deleted.",

"books.list.images.delete_error":
    "❌ Image deletion error: {message}",

"books.list.images.count":
    "{count} images",

"books.list.images.invalid_list":
    "The image list format is invalid.",

"books.list.images.invalid_move_direction":
    "Invalid move direction.",

"books.list.images.move_not_found":
    "The image to move could not be found.",

"books.list.images.primary_move_forbidden":
    "The cover image position cannot be changed.",

"books.list.images.order_saving":
    "Saving image order...",

"books.list.images.order_saved":
    "✅ Image order saved.",

"books.list.images.order_error":
    "❌ Image order save error: {message}",

"books.list.images.load_failed":
    "Images could not be loaded.",

"books.list.images.missing_item_id":
    "The collection item identifier is missing.",

"books.list.images.upload_progress":
    "Uploading: {current} / {total}",

"books.list.images.upload_success_one":
    "✅ Image uploaded.",

"books.list.images.upload_success_many":
    "✅ {count} images uploaded.",

"books.list.images.upload_error":
    "❌ Image upload error: {message}",

"books.list.images.missing_image_id":
    "The image identifier is missing.",

"books.list.images.setting_primary":
    "Setting cover image...",

"books.list.images.primary_set":
    "✅ Cover image set.",

"books.list.images.primary_error":
    "❌ Cover image error: {message}",

"books.list.edit.permission_required":
    "Editor permission is required for this action.",

"books.list.edit.invalid_id":
    "Invalid book index.",

"books.list.edit.not_found":
    "The book could not be found.",

"books.list.edit.missing_public_id":
    "The book does not have a modern collection identifier.",

"books.list.images.loading":
    "Loading images...",

"books.list.edit.storage_missing":
    "The book's current storage location is not available in the active storage tree.",

"books.list.edit.error":
    "Edit error: {message}",

"books.list.storage.inactive":
    "{name} — inactive",

"books.list.storage.invalid_response":
    "The server returned an invalid storage tree response.",

"books.list.delete.unknown_error":
    "Unknown deletion error.",

"books.list.delete.not_found":
    "The book is no longer in the database.",

"books.list.delete.error":
    "Deletion error: {message}",

"books.list.page_info":
    "{current} / {total} page",

"books.list.delete.permission_required":
    "Editor permission is required for this action.",

"books.list.delete.invalid_id":
    "Invalid book index.",

"books.list.delete.confirm":
    "Are you sure you want to delete book copy #{id}?",
"books.list.field.publisher":
    "Publisher:",

"books.list.field.publish_year":
    "Publication year:",

"books.list.field.added":
    "Added:",

"books.list.field.location":
    "Location:",
"books.list.summary.search":
    "{total} results – records {first}–{last}",

"books.list.summary.all":
    "{total} book copies – records {first}–{last}",

"books.list.empty":
    "No books match the search.",

"books.list.no_cover":
    "No cover image",

"books.list.edit_button":
    "✏️ Edit",

"books.list.delete_button":
    "🗑️ Delete",
"books.list.status.borrowed_by":
    "📤 Loaned to: {borrower}",

"books.list.status.borrowed":
    "📤 Loaned",

"books.list.status.removed":
    "📦 Removed from shelf",

"books.list.status.on_shelf":
    "📚 On shelf",

"books.list.loading":
    "Loading books...",

"books.list.invalid_response":
    "The server returned an invalid book list response.",

"books.list.load_failed":
    "Failed to load books: {message}",

"books.list.edit.title":
    "Edit book",

"books.list.images.count_zero":
    "0 images",

"books.list.images.empty":
    "No images for this book yet.",

"books.list.images.help":
    "On mobile, you can take a photo directly or select multiple existing images.",

"books.list.field.unique_index":
    "Unique index",

"books.list.storage_search":
    "Search storage",

"books.list.storage_search_placeholder":
    "Room, shelf or storage location...",

"books.list.borrower":
    "Who has it?",
"common.previous": "← Previous",
"common.next": "Next →",

"books.list.page_title": "Library",
"books.list.add": "➕ Add book",
"books.list.search_placeholder":
    "Search by title, ISBN, author, publisher, location or borrower...",
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
"books.list.images.close_preview":
    "Kép bezárása",

"books.list.permissions_load_failed":
    "❌ Nem sikerült betölteni a jogosultsági adatokat.",

"books.list.edit.save_error":
    "❌ Mentési hiba: {message}",

"books.list.edit.isbn_required":
    "❌ Az ISBN nem lehet üres.",

"books.list.edit.title_required":
    "❌ A cím nem lehet üres.",

"books.list.edit.storage_required":
    "❌ Válassz tárhelyet.",

"books.list.edit.borrower_required":
    "❌ Add meg, kinél van a könyv.",

"books.list.images.default_caption":
    "Kép",

"books.list.images.primary_badge":
    "Elsődleges",

"books.list.images.move_left_button":
    "← Balra",

"books.list.images.move_right_button":
    "Jobbra →",

"books.list.images.current_primary":
    "⭐ Jelenlegi borítókép",

"books.list.images.make_primary":
    "⭐ Legyen borítókép",

"books.list.images.delete_button":
    "🗑 Törlés",

"books.list.images.delete_confirm":
    "Biztosan törlöd ezt a képet?",

"books.list.images.deleting":
    "Kép törlése...",

"books.list.images.deleted":
    "✅ A kép törölve.",

"books.list.images.delete_error":
    "❌ Képtörlési hiba: {message}",

"books.list.images.count":
    "{count} kép",

"books.list.images.invalid_list":
    "A képlista formátuma hibás.",

"books.list.images.invalid_move_direction":
    "Érvénytelen mozgatási irány.",

"books.list.images.move_not_found":
    "A mozgatandó kép nem található.",

"books.list.images.primary_move_forbidden":
    "A borítókép helye nem módosítható.",

"books.list.images.order_saving":
    "Képsorrend mentése...",

"books.list.images.order_saved":
    "✅ Képsorrend elmentve.",

"books.list.images.order_error":
    "❌ Képsorrend-mentési hiba: {message}",

"books.list.images.load_failed":
    "A képek nem tölthetők be.",

"books.list.images.missing_item_id":
    "Hiányzik a gyűjteményi elem azonosítója.",

"books.list.images.upload_progress":
    "Feltöltés: {current} / {total}",

"books.list.images.upload_success_one":
    "✅ A kép feltöltve.",

"books.list.images.upload_success_many":
    "✅ {count} kép feltöltve.",

"books.list.images.upload_error":
    "❌ Képfeltöltési hiba: {message}",

"books.list.images.missing_image_id":
    "Hiányzik a kép azonosítója.",

"books.list.images.setting_primary":
    "Borítókép beállítása...",

"books.list.images.primary_set":
    "✅ Borítókép beállítva.",

"books.list.images.primary_error":
    "❌ Borítókép-beállítási hiba: {message}",

"books.list.edit.permission_required":
    "Ehhez a művelethez szerkesztői jogosultság szükséges.",

"books.list.edit.invalid_id":
    "Hibás könyvindex.",

"books.list.edit.not_found":
    "A könyv nem található.",

"books.list.edit.missing_public_id":
    "A könyvhöz nem tartozik modern gyűjteményi azonosító.",

"books.list.images.loading":
    "Képek betöltése...",

"books.list.edit.storage_missing":
    "A könyv jelenlegi tárhelye nem található az aktív tárhelyfában.",

"books.list.edit.error":
    "Szerkesztési hiba: {message}",

"books.list.storage.inactive":
    "{name} — inaktív",

"books.list.storage.invalid_response":
    "A szerver hibás tárhelyfa-választ adott.",

"books.list.delete.unknown_error":
    "Ismeretlen törlési hiba.",

"books.list.delete.not_found":
    "A könyv már nem található az adatbázisban.",

"books.list.delete.error":
    "Törlési hiba: {message}",

"books.list.page_info":
    "{current} / {total}. oldal",

"books.list.delete.permission_required":
    "Ehhez a művelethez szerkesztői jogosultság szükséges.",

"books.list.delete.invalid_id":
    "Hibás könyvindex.",

"books.list.delete.confirm":
    "Biztosan törlöd a(z) {id}. indexű könyvpéldányt?",
"books.list.field.publisher":
    "Kiadó:",

"books.list.field.publish_year":
    "Kiadás éve:",

"books.list.field.added":
    "Felvéve:",

"books.list.field.location":
    "Hely:",
"books.list.summary.search":
    "{total} találat – {first}–{last}. rekord",

"books.list.summary.all":
    "{total} könyvpéldány – {first}–{last}. rekord",

"books.list.empty":
    "Nincs a keresésnek megfelelő könyv.",

"books.list.no_cover":
    "Nincs borítókép",

"books.list.edit_button":
    "✏️ Szerkesztés",

"books.list.delete_button":
    "🗑️ Törlés",
"books.list.status.borrowed_by":
    "📤 Kölcsönadva: {borrower}",

"books.list.status.borrowed":
    "📤 Kölcsönadva",

"books.list.status.removed":
    "📦 Polcról levéve",

"books.list.status.on_shelf":
    "📚 Polcon",

"books.list.loading":
    "Könyvek betöltése...",

"books.list.invalid_response":
    "A szerver hibás könyvlista-választ adott.",

"books.list.load_failed":
    "Nem sikerült betölteni a könyveket: {message}",

"books.list.edit.title":
    "Könyv szerkesztése",

"books.list.images.count_zero":
    "0 kép",

"books.list.images.empty":
    "Még nincs kép ehhez a könyvhöz.",

"books.list.images.help":
    "Telefonon közvetlenül fotózhatsz, vagy több meglévő képet is kiválaszthatsz.",

"books.list.field.unique_index":
    "Egyedi index",

"books.list.storage_search":
    "Tárhely keresése",

"books.list.storage_search_placeholder":
    "Helyiség, polc vagy tárhely...",

"books.list.borrower":
    "Kinél van?",
"common.previous": "← Előző",
"common.next": "Következő →",

"books.list.page_title": "Könyvtár",
"books.list.add": "➕ Felvitel",
"books.list.search_placeholder":
    "Keresés cím, ISBN, szerző, kiadó, hely vagy kölcsönző alapján...",
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
