"use strict";

// --------------------------------------------------
// DOM ELEMEK
// --------------------------------------------------

const isbn = document.getElementById("isbn");
const place = document.getElementById("place");

const removed = document.getElementById("removed");
const borrowed = document.getElementById("borrowed");
const borrowBox = document.getElementById("borrowBox");
const borrower = document.getElementById("borrower");

const saveButton = document.getElementById("saveButton");
const statusBox = document.getElementById("status");
const latest = document.getElementById("latest");

const liveScannerButton = document.getElementById("liveScannerButton");
const scannerModal = document.getElementById("scannerModal");
const scannerViewport = document.getElementById("scannerViewport");
const scannerStatus = document.getElementById("scannerStatus");
const closeScannerButton = document.getElementById("closeScannerButton");
const stopScannerButton = document.getElementById("stopScannerButton");

const missingMetadataModal = document.getElementById("missingMetadataModal");

const missingMetadataCloseButton =
    document.getElementById(
        "missingMetadataCloseButton"
    );

const missingMetadataCancelButton =
    document.getElementById(
        "missingMetadataCancelButton"
    );

const missingMetadataSaveButton =
    document.getElementById(
        "missingMetadataSaveButton"
    );

const missingMetadataIsbn =
    document.getElementById(
        "missingMetadataIsbn"
    );

const missingMetadataTitle =
    document.getElementById(
        "missingMetadataTitle"
    );

const missingMetadataAuthor =
    document.getElementById(
        "missingMetadataAuthor"
    );

const missingMetadataPublisher =
    document.getElementById(
        "missingMetadataPublisher"
    );

const missingMetadataYear =
    document.getElementById(
        "missingMetadataYear"
    );

const missingMetadataLocation =
    document.getElementById(
        "missingMetadataLocation"
    );

const missingMetadataBorrower =
    document.getElementById(
        "missingMetadataBorrower"
    );

const missingMetadataStatus =
    document.getElementById(
        "missingMetadataStatus"
    );

// Kézi felvitel
const manualBookButton =
    document.getElementById("manualBookButton");

const manualModal =
    document.getElementById("manualModal");

const manualCloseButton =
    document.getElementById("manualCloseButton");

const manualCancelButton =
    document.getElementById("manualCancelButton");

const manualSaveButton =
    document.getElementById("manualSaveButton");

const manualIdentifier =
    document.getElementById("manualIdentifier");

const manualTitle =
    document.getElementById("manualTitle");

const manualAuthor =
    document.getElementById("manualAuthor");

const manualPublisher =
    document.getElementById("manualPublisher");

const manualYear =
    document.getElementById("manualYear");

const manualLocation =
    document.getElementById("manualLocation");

const manualStatus =
    document.getElementById("manualStatus");

let allPlaces = [];
let borrowedLocationId = null;
let removedLocationId = null;


// --------------------------------------------------
// SEGÉDFÜGGVÉNYEK
// --------------------------------------------------

function normalizeText(value) {
    return String(value ?? "")
        .trim()
        .toLocaleLowerCase("hu-HU");
}

function normalizeIsbn(value) {
    return String(value ?? "")
        .replaceAll("-", "")
        .replaceAll(" ", "")
        .trim();
}

function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function showStatus(message, type = "normal") {
    if (!statusBox) {
        return;
    }

    statusBox.textContent = message;

    if (type === "error") {
        statusBox.style.color = "#ff6b6b";
    } else if (type === "success") {
        statusBox.style.color = "#6dff6d";
    } else {
        statusBox.style.color = "";
    }
}

function selectedPlace() {
    if (!place) {
        return null;
    }

    const id = Number(place.value);

    if (!id) {
        return null;
    }

    return allPlaces.find(
        item => Number(item.id) === id
    ) ?? null;
}

function isBorrowedPlace(item) {
    return Boolean(
        item &&
        normalizeText(item.room) ===
            normalizeText("Kölcsönadva")
    );
}

function isRemovedPlace(item) {
    const room = normalizeText(item?.room);

    return (
        room === normalizeText("Polcról levéve") ||
        room === normalizeText("Levéve")
    );
}

function getPlaceLabel(item) {
    if (isBorrowedPlace(item)) {
        return "Kölcsönadva";
    }

    if (isRemovedPlace(item)) {
        return "Polcról levéve";
    }

    return (
        `${item.room} / ${item.shelf} / ` +
        `Tárhely ${item.slot}`
    );
}


// --------------------------------------------------
// TÁRHELYLISTA FELTÖLTÉSE
// --------------------------------------------------

function fillPlaceSelect(selectElement) {
    if (!selectElement) {
        return;
    }

    selectElement.innerHTML =
        '<option value="">-- válassz tárhelyet --</option>';

    allPlaces.forEach(item => {
        const option =
            document.createElement("option");

        option.value = String(item.id);
        option.textContent = getPlaceLabel(item);

        selectElement.appendChild(option);
    });

    const lastLocationId =
        localStorage.getItem("lastLocationId");

    if (
        lastLocationId &&
        [...selectElement.options].some(
            option => option.value === lastLocationId
        )
    ) {
        selectElement.value = lastLocationId;
    }
}


// --------------------------------------------------
// TÁRHELYEK BETÖLTÉSE
// --------------------------------------------------

async function loadPlaces() {
    try {
        const response = await fetch("/places");

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        if (!Array.isArray(data)) {
            throw new Error(
                "A /places végpont nem listát adott vissza."
            );
        }

        allPlaces = data;

        borrowedLocationId = null;
        removedLocationId = null;

        allPlaces.forEach(item => {
            if (isBorrowedPlace(item)) {
                borrowedLocationId =
                    Number(item.id);
            }

            if (isRemovedPlace(item)) {
                removedLocationId =
                    Number(item.id);
            }
        });

        /*
         * Mindkét legördülőt csak azután töltjük fel,
         * hogy az adatok megérkeztek a szervertől.
         */
        fillPlaceSelect(place);
        fillPlaceSelect(manualLocation);
	fillPlaceSelect(missingMetadataLocation);

        syncSpecialControlsFromPlace();

    } catch (error) {
        console.error(
            "Tárhelybetöltési hiba:",
            error
        );

        showStatus(
            `❌ Nem sikerült betölteni a tárhelyeket: ` +
            error.message,
            "error"
        );

        if (manualStatus) {
            manualStatus.textContent =
                "❌ Nem sikerült betölteni a tárhelyeket.";
        }
    }
}


// --------------------------------------------------
// SPECIÁLIS HELYEK KEZELÉSE
// --------------------------------------------------

function syncSpecialControlsFromPlace() {
    const selected = selectedPlace();

    const isBorrowed =
        isBorrowedPlace(selected);

    const isRemoved =
        isRemovedPlace(selected);

    if (borrowed) {
        borrowed.checked = isBorrowed;
    }

    if (removed) {
        removed.checked = isRemoved;
    }

    if (borrowBox) {
        borrowBox.style.display =
            isBorrowed ? "block" : "none";
    }

    if (!isBorrowed && borrower) {
        borrower.value = "";
    }

    /*
     * Csak normál polchelyet jegyzünk meg.
     */
    if (
        selected &&
        !isBorrowed &&
        !isRemoved
    ) {
        localStorage.setItem(
            "lastLocationId",
            String(selected.id)
        );
    }
}

function restoreLastNormalLocation() {
    if (!place) {
        return;
    }

    const lastLocationId =
        localStorage.getItem("lastLocationId");

    if (
        lastLocationId &&
        [...place.options].some(
            option => option.value === lastLocationId
        )
    ) {
        place.value = lastLocationId;
    } else {
        place.value = "";
    }

    syncSpecialControlsFromPlace();
}

if (place) {
    place.addEventListener("change", () => {
        syncSpecialControlsFromPlace();
    });
}

if (borrowed) {
    borrowed.addEventListener("change", () => {
        if (borrowed.checked) {
            if (removed) {
                removed.checked = false;
            }

            if (
                borrowedLocationId !== null &&
                place
            ) {
                place.value =
                    String(borrowedLocationId);
            }

            if (borrowBox) {
                borrowBox.style.display =
                    "block";
            }

            if (borrower) {
                borrower.focus();
            }

        } else {
            if (borrowBox) {
                borrowBox.style.display =
                    "none";
            }

            if (borrower) {
                borrower.value = "";
            }

            if (
                isBorrowedPlace(selectedPlace())
            ) {
                restoreLastNormalLocation();
            }
        }
    });
}

if (removed) {
    removed.addEventListener("change", () => {
        if (removed.checked) {
            if (borrowed) {
                borrowed.checked = false;
            }

            if (borrower) {
                borrower.value = "";
            }

            if (borrowBox) {
                borrowBox.style.display =
                    "none";
            }

            if (
                removedLocationId !== null &&
                place
            ) {
                place.value =
                    String(removedLocationId);
            }

        } else if (
            isRemovedPlace(selectedPlace())
        ) {
            restoreLastNormalLocation();
        }
    });
}


// --------------------------------------------------
// ISBN-ES KÖNYV MENTÉSE
// --------------------------------------------------

async function send() {
    const cleanIsbn =
        normalizeIsbn(isbn?.value);

    const locationId =
        Number(place?.value);

    const selected =
        selectedPlace();

    if (!locationId || !selected) {
        showStatus(
            "❌ Először válassz tárhelyet.",
            "error"
        );

        place?.focus();
        return;
    }

    if (!cleanIsbn) {
        showStatus(
            "❌ Add meg az ISBN-t.",
            "error"
        );

        isbn?.focus();
        return;
    }

    if (!/^\d{10}$|^\d{13}$/.test(cleanIsbn)) {
        showStatus(
            "❌ Az ISBN 10 vagy 13 számjegyből álljon.",
            "error"
        );

        isbn?.focus();
        return;
    }

    if (
        isBorrowedPlace(selected) &&
        !borrower?.value.trim()
    ) {
        showStatus(
            "❌ Add meg, kinél van a könyv.",
            "error"
        );

        borrower?.focus();
        return;
    }

    showStatus("Mentés...");

    if (saveButton) {
        saveButton.disabled = true;
    }

    try {
        const response = await fetch("/scan", {
            method: "POST",

            headers: {
                "Content-Type":
                    "application/json"
            },

            body: JSON.stringify({
                isbn: cleanIsbn,
                location_id: locationId,
                borrower:
                    isBorrowedPlace(selected)
                    ? borrower.value.trim()
                    : null
            })
        });

        const data = await response.json();

        if (data.status === "metadata_missing") {
            openMissingMetadataModal({
                isbn: data.isbn,
                locationId: locationId,
                borrower: (
                    isBorrowedPlace(selected)
                        ? borrower.value.trim()
                        : null
                )
            });

            showStatus(
                "⚠️ Nem találtam könyvadatokat. " +
                "Add meg őket kézzel.",
                "error"
            );

            return;
        }

        if (
            !response.ok ||
            data.status === "error"
        ) {
            throw new Error(
                data.message ||
                `HTTP ${response.status}`
            );
        }

        showStatus(
            `✅ Könyv felvéve. Egyedi index: ${data.id}`,
            "success"
        );

        isbn.value = "";

        if (isBorrowedPlace(selected) && borrower) {
            borrower.value = "";
        }

        isbn.focus();

        await loadLatest();

    } catch (error) {
        console.error(
            "Mentési hiba:",
            error
        );

        showStatus(
            `❌ Mentési hiba: ${error.message}`,
            "error"
        );

    } finally {
        if (saveButton) {
            saveButton.disabled = false;
        }
    }
}

if (saveButton) {
    saveButton.addEventListener(
        "click",
        send
    );
}

if (isbn) {
    isbn.addEventListener(
        "keydown",
        event => {
            if (event.key === "Enter") {
                event.preventDefault();
                send();
            }
        }
    );
}


// --------------------------------------------------
// UTOLSÓ 20 KÖNYV
// --------------------------------------------------

async function loadLatest() {
    if (!latest) {
        return;
    }

    try {
        const response =
            await fetch("/books/latest");

        if (!response.ok) {
            throw new Error(
                `HTTP ${response.status}`
            );
        }

        const books =
            await response.json();

        latest.innerHTML = "";

        if (!books.length) {
            latest.innerHTML =
                '<div class="book">' +
                'Még nincs felvett könyv.' +
                '</div>';

            return;
        }

        books.forEach(book => {
            let locationText =
                "Nincs megadva";

            if (book.borrower) {
                locationText =
                    `Kölcsönadva: ${book.borrower}`;

            } else if (
                normalizeText(book.room) ===
                    normalizeText("Polcról levéve") ||
                normalizeText(book.room) ===
                    normalizeText("Levéve")
            ) {
                locationText =
                    "Polcról levéve";

            } else {
                const parts = [];

                if (book.room) {
                    parts.push(book.room);
                }

                if (book.shelf) {
                    parts.push(book.shelf);
                }

                if (
                    book.slot !== null &&
                    book.slot !== undefined
                ) {
                    parts.push(
                        `Tárhely ${book.slot}`
                    );
                }

                if (parts.length) {
                    locationText =
                        parts.join(" / ");
                }
            }

            latest.innerHTML += `
                <div class="book">

                    <div class="book-title">
                        ${escapeHtml(
                            book.title ||
                            book.isbn ||
                            "Névtelen könyv"
                        )}
                    </div>

                    <div class="book-author">
                        ${escapeHtml(
                            book.author || "-"
                        )}
                    </div>

                    <div class="book-isbn">
                        ISBN:
                        ${escapeHtml(
                            book.isbn || "-"
                        )}
                    </div>

                    <div>
                        📍
                        ${escapeHtml(locationText)}
                    </div>

                    <div class="book-date">
                        Egyedi index:
                        ${escapeHtml(book.id)}
                    </div>

                </div>
            `;
        });

    } catch (error) {
        console.error(
            "Lista betöltési hiba:",
            error
        );

        latest.innerHTML =
            '<div class="book">' +
            '❌ Nem sikerült betölteni a listát.' +
            '</div>';
    }
}


// --------------------------------------------------
// KÉZI, ISBN NÉLKÜLI FELVITEL
// --------------------------------------------------

function openManualModal() {
    if (!manualModal) {
        console.error(
            "A manualModal elem hiányzik az index.html-ből."
        );
        return;
    }

    manualModal.style.display = "block";

    manualIdentifier.value = "";
    manualTitle.value = "";
    manualAuthor.value = "";
    manualPublisher.value = "";
    manualYear.value = "";
    manualStatus.textContent = "";

    const lastLocationId =
        localStorage.getItem("lastLocationId");

    if (
        lastLocationId &&
        manualLocation
    ) {
        manualLocation.value =
            lastLocationId;
    }

    manualIdentifier.focus();
}

function closeManualModal() {
    if (manualModal) {
        manualModal.style.display =
            "none";
    }
}

async function saveManualBook() {
    const identifier =
        manualIdentifier.value.trim();

    const title =
        manualTitle.value.trim();

    const locationId =
        Number(manualLocation.value);

    if (!identifier) {
        manualStatus.textContent =
            "❌ Adj meg azonosítót vagy jelzetet.";

        manualIdentifier.focus();
        return;
    }

    if (!title) {
        manualStatus.textContent =
            "❌ Add meg a könyv címét.";

        manualTitle.focus();
        return;
    }

    if (!locationId) {
        manualStatus.textContent =
            "❌ Válassz tárhelyet.";

        manualLocation.focus();
        return;
    }

    manualStatus.textContent =
        "Mentés...";

    manualSaveButton.disabled =
        true;

    try {
        const response =
            await fetch("/books/manual", {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({
                    identifier: identifier,
                    title: title,

                    author:
                        manualAuthor.value
                            .trim() || null,

                    publisher:
                        manualPublisher.value
                            .trim() || null,

                    publish_year:
                        manualYear.value
                            .trim() || null,

                    location_id:
                        locationId
                })
            });

        const data =
            await response.json();

        if (
            !response.ok ||
            data.status === "error"
        ) {
            throw new Error(
                data.message ||
                `HTTP ${response.status}`
            );
        }

        localStorage.setItem(
            "lastLocationId",
            String(locationId)
        );

        if (place) {
            place.value =
                String(locationId);

            syncSpecialControlsFromPlace();
        }

        closeManualModal();

        showStatus(
            `✅ Könyv felvéve. Egyedi index: ${data.id}`,
            "success"
        );

        await loadLatest();

    } catch (error) {
        console.error(
            "Kézi könyvfelviteli hiba:",
            error
        );

        manualStatus.textContent =
            `❌ ${error.message}`;

    } finally {
        manualSaveButton.disabled =
            false;
    }
}


// --------------------------------------------------
// KÉZI MODAL ESEMÉNYEK
// --------------------------------------------------

if (manualBookButton) {
    manualBookButton.addEventListener(
        "click",
        openManualModal
    );
}

if (manualCloseButton) {
    manualCloseButton.addEventListener(
        "click",
        closeManualModal
    );
}

if (manualCancelButton) {
    manualCancelButton.addEventListener(
        "click",
        closeManualModal
    );
}

if (manualSaveButton) {
    manualSaveButton.addEventListener(
        "click",
        saveManualBook
    );
}

if (manualModal) {
    manualModal.addEventListener(
        "click",
        event => {
            if (
                event.target === manualModal
            ) {
                closeManualModal();
            }
        }
    );
}

if (manualIdentifier) {
    manualIdentifier.addEventListener(
        "keydown",
        event => {
            if (event.key === "Enter") {
                event.preventDefault();
                manualTitle.focus();
            }
        }
    );
}

if (manualTitle) {
    manualTitle.addEventListener(
        "keydown",
        event => {
            if (event.key === "Enter") {
                event.preventDefault();
                saveManualBook();
            }
        }
    );
}

// --------------------------------------------------
// ÉLŐ EAN-13 / ISBN SCANNER QUAGGA2-VEL
// --------------------------------------------------

let scannerRunning = false;
let lastDetectedCode = null;
let repeatedDetectionCount = 0;
let scanAccepted = false;


// EAN-13 ellenőrzőszám vizsgálata.
// Ezzel jelentősen csökkentjük a téves felismerést.
function isValidEan13(code) {
    if (!/^\d{13}$/.test(code)) {
        return false;
    }

    const digits = code
        .split("")
        .map(Number);

    const suppliedCheckDigit =
        digits[12];

    let sum = 0;

    for (let index = 0; index < 12; index++) {
        sum += digits[index] *
            (index % 2 === 0 ? 1 : 3);
    }

    const calculatedCheckDigit =
        (10 - (sum % 10)) % 10;

    return calculatedCheckDigit === suppliedCheckDigit;
}


function isBookIsbn(code) {
    return (
        isValidEan13(code) &&
        (
            code.startsWith("978") ||
            code.startsWith("979")
        )
    );
}

async function configureScannerCamera() {
    try {
        const track =
            Quagga.CameraAccess.getActiveTrack();

        if (!track) {
            console.warn(
                "Nem található aktív kameratrack."
            );
            return;
        }

        const capabilities =
            typeof track.getCapabilities === "function"
                ? track.getCapabilities()
                : {};

        console.log(
            "Kamera képességek:",
            capabilities
        );

        const advancedConstraints = {};

        /*
         * Folyamatos autofókusz, ha a telefon támogatja.
         */
        if (
            Array.isArray(capabilities.focusMode) &&
            capabilities.focusMode.includes("continuous")
        ) {
            advancedConstraints.focusMode =
                "continuous";
        }

        /*
         * Enyhe zoom, ha támogatott.
         * Nem fixen 2×, hanem a kamera tartományához igazítva.
         */
        if (capabilities.zoom) {
            const minZoom =
                capabilities.zoom.min ?? 1;

            const maxZoom =
                capabilities.zoom.max ?? 1;

            advancedConstraints.zoom =
                Math.min(
                    maxZoom,
                    Math.max(minZoom, 1.5)
                );
        }

        if (
            Object.keys(advancedConstraints).length
        ) {
            await track.applyConstraints({
                advanced: [
                    advancedConstraints
                ]
            });
        }

        console.log(
            "Kamera beállítások alkalmazva:",
            advancedConstraints
        );

    } catch (error) {
        /*
         * Nem állítjuk le a scannert, ha a telefon
         * nem támogatja valamelyik extra beállítást.
         */
        console.warn(
            "Kamera finomhangolás nem sikerült:",
            error
        );
    }
}

async function startLiveScanner() {
    if (scannerRunning) {
        return;
    }

    if (!window.Quagga) {
        showStatus(
            "❌ A Quagga2 könyvtár nem töltődött be.",
            "error"
        );

        return;
    }

    scanAccepted = false;
    lastDetectedCode = null;
    repeatedDetectionCount = 0;

/*
 * A modalt biztosan közvetlenül a body alá tesszük,
 * hogy semmilyen szülőelem CSS-e ne befolyásolja.
 */
if (scannerModal.parentElement !== document.body) {
    document.body.appendChild(scannerModal);
}

/*
 * A háttéroldal görgetésének lezárása.
 */
document.body.style.overflow = "hidden";

/*
 * Teljes képernyős fix réteg.
 */
Object.assign(scannerModal.style, {
    display: "flex",
    position: "fixed",
    top: "0",
    right: "0",
    bottom: "0",
    left: "0",
    width: "100vw",
    height: "100dvh",
    zIndex: "999999",
    margin: "0",
    padding: "0",
    overflow: "hidden",
    background: "rgba(0, 0, 0, 0.96)",
    alignItems: "stretch",
    justifyContent: "stretch"
});

scannerModal.scrollTop = 0;

scannerStatus.textContent =
    "Kamera indítása...";

    try {
        await new Promise((resolve, reject) => {
            Quagga.init(
                {
                    inputStream: {
                        name: "Live",
                        type: "LiveStream",
                        target: scannerViewport,

                        constraints: {
                            facingMode: {
                                ideal: "environment"
                            },

                            width: {
                                ideal: 1920
                            },

                            height: {
                                ideal: 1080
                            },

                            aspectRatio: {
                                ideal: 1.777777
                            }
                        },

                        area: {
                            top: "38%",
                            right: "5%",
                            left: "5%",
                            bottom: "38%"
                        }
                    },

                    locator: {
                        patchSize: "large",
                        halfSample: true
                    },

                    numOfWorkers:
                        Math.min(
                            navigator.hardwareConcurrency || 2,
                            4
                        ),

                    frequency: 6,

                    decoder: {
                        readers: [
                            "ean_reader"
                        ],

                        multiple: false
                    },

                    locate: true
                },

                error => {
                    if (error) {
                        reject(error);
                        return;
                    }

                    resolve();
                }
            );
        });

        Quagga.onDetected(handleBarcodeDetected);

        Quagga.start();

        scannerRunning = true;

        scannerStatus.textContent =
            "Kamera beállítása...";

        await configureScannerCamera();

        scannerStatus.textContent =
            "Keresem a könyv ISBN-vonalkódját...";

    } catch (error) {
        console.error(
            "Kameraindítási hiba:",
            error
        );

        scannerStatus.textContent =
            `❌ Kamerahiba: ${error.message || error}`;

        stopLiveScanner(false);
    }
}


function handleBarcodeDetected(result) {
    if (
        scanAccepted ||
        !result ||
        !result.codeResult
    ) {
        return;
    }

    const code = String(
        result.codeResult.code || ""
    )
        .replace(/\D/g, "")
        .trim();

    if (!isBookIsbn(code)) {
        scannerStatus.textContent =
            code
                ? `Nem könyv-ISBN: ${code}`
                : "Keresem a vonalkódot...";

        return;
    }

    /*
     * A Quagga kétszer egymás után ugyanazt az
     * érvényes ISBN-t olvassa be, csak akkor fogadjuk el.
     */
    if (code === lastDetectedCode) {
        repeatedDetectionCount++;
    } else {
        lastDetectedCode = code;
        repeatedDetectionCount = 1;
    }

    scannerStatus.textContent =
        `Felismert ISBN: ${code} ` +
        `(${repeatedDetectionCount}/2)`;

    if (repeatedDetectionCount < 2) {
        return;
    }

    scanAccepted = true;

    isbn.value = code;

    showStatus(
        `✅ Felismert ISBN: ${code}`,
        "success"
    );

    stopLiveScanner();

    isbn.focus();

    /*
     * Egyelőre nem mentjük automatikusan.
     * Ellenőrizheted a számot, majd megnyomhatod
     * a Könyv felvétele gombot.
     *
     * Automatikus mentéshez később:
     *
     * send();
     */
}


function stopLiveScanner(hideModal = true) {
    try {
        Quagga.offDetected(
            handleBarcodeDetected
        );

        if (scannerRunning) {
            Quagga.stop();
        }

    } catch (error) {
        console.warn(
            "Scannerleállítási figyelmeztetés:",
            error
        );
    }

    scannerRunning = false;

    scannerViewport.innerHTML = "";

if (hideModal) {
    scannerModal.style.display = "none";
}

/*
 * A háttéroldal újra görgethető.
 */
document.body.style.overflow = "";
}


liveScannerButton.addEventListener(
    "click",
    startLiveScanner
);

closeScannerButton.addEventListener(
    "click",
    () => stopLiveScanner()
);

stopScannerButton.addEventListener(
    "click",
    () => stopLiveScanner()
);

scannerModal.addEventListener(
    "click",
    event => {
        if (event.target === scannerModal) {
            stopLiveScanner();
        }
    }
);

document.addEventListener(
    "visibilitychange",
    () => {
        if (
            document.hidden &&
            scannerRunning
        ) {
            stopLiveScanner();
        }
    }
);

// --------------------------------------------------
// HIÁNYZÓ ISBN-METAADAT KÉZI MEGADÁSA
// --------------------------------------------------

function openMissingMetadataModal({
    isbn,
    locationId,
    borrower
}) {
    missingMetadataIsbn.value =
        isbn || "";

    missingMetadataTitle.value = "";
    missingMetadataAuthor.value = "";
    missingMetadataPublisher.value = "";
    missingMetadataYear.value = "";

    missingMetadataLocation.value =
        String(locationId || "");

    missingMetadataBorrower.value =
        borrower || "";

    missingMetadataStatus.textContent = "";

    missingMetadataModal.style.display =
        "block";

    document.body.style.overflow =
        "hidden";

    missingMetadataTitle.focus();
}


function closeMissingMetadataModal() {
    missingMetadataModal.style.display =
        "none";

    document.body.style.overflow = "";

    /*
     * Az eredeti ISBN-t nem ürítjük automatikusan,
     * így megszakítás esetén sem vész el.
     */
    isbn.focus();
}


async function saveMissingMetadataBook() {
    const cleanIsbn =
        missingMetadataIsbn.value
            .replaceAll("-", "")
            .replaceAll(" ", "")
            .trim();

    const title =
        missingMetadataTitle.value.trim();

    const locationId =
        Number(
            missingMetadataLocation.value
        );

    if (!title) {
        missingMetadataStatus.textContent =
            "❌ Add meg a könyv címét.";

        missingMetadataTitle.focus();
        return;
    }

    if (!locationId) {
        missingMetadataStatus.textContent =
            "❌ Válassz tárhelyet.";

        missingMetadataLocation.focus();
        return;
    }

    missingMetadataStatus.textContent =
        "Mentés...";

    missingMetadataSaveButton.disabled =
        true;

    try {
        const response =
            await fetch(
                "/books/manual-isbn",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        isbn: cleanIsbn,

                        title: title,

                        author:
                            missingMetadataAuthor
                                .value
                                .trim() || null,

                        publisher:
                            missingMetadataPublisher
                                .value
                                .trim() || null,

                        publish_year:
                            missingMetadataYear
                                .value
                                .trim() || null,

                        location_id:
                            locationId,

                        borrower:
                            missingMetadataBorrower
                                .value
                                .trim() || null
                    })
                }
            );

        const data =
            await response.json();

        if (
            !response.ok ||
            data.status === "error"
        ) {
            throw new Error(
                data.message ||
                `HTTP ${response.status}`
            );
        }

        localStorage.setItem(
            "lastLocationId",
            String(locationId)
        );

        if (place) {
            place.value =
                String(locationId);

            syncSpecialControlsFromPlace();
        }

        missingMetadataModal.style.display =
            "none";

        document.body.style.overflow = "";

        isbn.value = "";

        showStatus(
            `✅ Könyv felvéve. Egyedi index: ${data.id}`,
            "success"
        );

        await loadLatest();

        isbn.focus();

    } catch (error) {
        console.error(
            "Kézi metaadatmentési hiba:",
            error
        );

        missingMetadataStatus.textContent =
            `❌ ${error.message}`;

    } finally {
        missingMetadataSaveButton.disabled =
            false;
    }
}


missingMetadataCloseButton.addEventListener(
    "click",
    closeMissingMetadataModal
);

missingMetadataCancelButton.addEventListener(
    "click",
    closeMissingMetadataModal
);

missingMetadataSaveButton.addEventListener(
    "click",
    saveMissingMetadataBook
);

missingMetadataModal.addEventListener(
    "click",
    event => {
        if (
            event.target ===
            missingMetadataModal
        ) {
            closeMissingMetadataModal();
        }
    }
);

missingMetadataTitle.addEventListener(
    "keydown",
    event => {
        if (event.key === "Enter") {
            event.preventDefault();
            saveMissingMetadataBook();
        }
    }
);

// --------------------------------------------------
// INDULÁS
// --------------------------------------------------

async function initialize() {
    await loadPlaces();
    await loadLatest();

    if (place?.value) {
        isbn?.focus();
    } else {
        place?.focus();
    }
}

initialize();
