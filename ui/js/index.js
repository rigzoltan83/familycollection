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

/*
 * Új tárhelyfa
 */
let storageLocations = [];
let storageByPublicId = new Map();

let borrowedStoragePublicId = null;
let removedStoragePublicId = null;

let pendingBookImages = [];

// --------------------------------------------------
// SEGÉDFÜGGVÉNYEK
// --------------------------------------------------

function normalizeText(value) {
    return String(value ?? "")
        .trim()
        .toLocaleLowerCase("hu-HU");
}

function flattenStorageTree(
    nodes,
    depth = 0,
    result = [],
    rootName = null,
    parentPath = []
) {
    for (const node of nodes) {
        const effectiveRootName =
            rootName || node.name;

        const currentPath = [
            ...parentPath,
            node.name
        ];

        result.push({
            ...node,
            depth,
            root_name: effectiveRootName,
            path_names: currentPath,
            path_label: currentPath
                .filter(
                    part =>
                        part &&
                        part !== "-"
                )
                .join(" / ")
        });

        flattenStorageTree(
            node.children || [],
            depth + 1,
            result,
            effectiveRootName,
            currentPath
        );
    }

    return result;
}

function isBorrowedStorage(location) {
    return (
        normalizeText(location?.root_name) ===
        normalizeText("Kölcsönadva")
    );
}

function isRemovedStorage(location) {
    return (
        normalizeText(location?.root_name) ===
        normalizeText("Polcról levéve")
    );
}

const pendingBookImageCount =
    document.getElementById(
        "pendingBookImageCount"
    );

const pendingBookImagePreview =
    document.getElementById(
        "pendingBookImagePreview"
    );

const pendingBookCameraButton =
    document.getElementById(
        "pendingBookCameraButton"
    );

const pendingBookFilesButton =
    document.getElementById(
        "pendingBookFilesButton"
    );

const pendingBookImagesClearButton =
    document.getElementById(
        "pendingBookImagesClearButton"
    );

const pendingBookCameraInput =
    document.getElementById(
        "pendingBookCameraInput"
    );

const pendingBookFilesInput =
    document.getElementById(
        "pendingBookFilesInput"
    );

function renderPendingBookImages() {
    if (
        !pendingBookImageCount
        || !pendingBookImagePreview
        || !pendingBookImagesClearButton
    ) {
        return;
    }

    pendingBookImageCount.textContent =
        `${pendingBookImages.length} kép kiválasztva`;

    pendingBookImagesClearButton.disabled =
        pendingBookImages.length === 0;

    if (pendingBookImages.length === 0) {
        pendingBookImagePreview.innerHTML = `
            <div
                id="pendingBookImageEmpty"
                class="pending-book-image-empty"
            >
                A könyvhöz még nincs kép kiválasztva.
            </div>
        `;

        return;
    }

    pendingBookImagePreview.innerHTML =
        pendingBookImages
            .map((file, index) => {
                const previewUrl =
                    URL.createObjectURL(file);

                return `

                    <div
                        class="pending-book-image-thumbnail"
                        data-preview-url="${escapeHtml(
                            previewUrl
                        )}"
                    >
                        <img
                            src="${escapeHtml(previewUrl)}"
                            alt="Kiválasztott kép ${
                                index + 1
                            }"
                        >

<div class="pending-book-image-order-actions">
    <button
        type="button"
        class="pending-book-image-order-button"
        data-pending-image-index="${index}"
        data-pending-image-action="left"
        ${index === 0 ? "disabled" : ""}
        title="Mozgatás balra"
    >
        ←
    </button>

    <button
        type="button"
        class="pending-book-image-order-button"
        data-pending-image-index="${index}"
        data-pending-image-action="right"
        ${
            index === pendingBookImages.length - 1
                ? "disabled"
                : ""
        }
        title="Mozgatás jobbra"
    >
        →
    </button>
</div>

                        <button
                            type="button"
                            class="
                                pending-book-image-remove
                            "
                            data-pending-image-index="${index}"
                            aria-label="${
                                index + 1
                            }. kép eltávolítása"
                            title="Kép eltávolítása"
                        >
                            ×
                        </button>

                        <div
                            class="
                                pending-book-image-thumbnail-number
                            "
                        >
                            ${index + 1}.
                        </div>
                    </div>

                `;
            })
            .join("");
}


function revokePendingBookImagePreviewUrls() {
    if (!pendingBookImagePreview) {
        return;
    }

    pendingBookImagePreview
        .querySelectorAll(
            "[data-preview-url]"
        )
        .forEach(element => {
            const previewUrl =
                element.dataset.previewUrl;

            if (previewUrl) {
                URL.revokeObjectURL(
                    previewUrl
                );
            }
        });
}


function clearPendingBookImages() {
    revokePendingBookImagePreviewUrls();

    pendingBookImages = [];

    if (pendingBookCameraInput) {
        pendingBookCameraInput.value = "";
    }

    if (pendingBookFilesInput) {
        pendingBookFilesInput.value = "";
    }

    renderPendingBookImages();
}

function removePendingBookImage(
    imageIndex
) {
    if (
        !Number.isInteger(imageIndex)
        || imageIndex < 0
        || imageIndex >= pendingBookImages.length
    ) {
        return false;
    }

    revokePendingBookImagePreviewUrls();

    pendingBookImages.splice(
        imageIndex,
        1
    );

    renderPendingBookImages();

    return true;
}

function movePendingBookImage(
    imageIndex,
    direction
) {
    if (
        !Number.isInteger(imageIndex)
        || imageIndex < 0
        || imageIndex >= pendingBookImages.length
    ) {
        return false;
    }

    if (
        direction !== "left"
        && direction !== "right"
    ) {
        return false;
    }

    const targetIndex =
        direction === "left"
            ? imageIndex - 1
            : imageIndex + 1;

    if (
        targetIndex < 0
        || targetIndex >= pendingBookImages.length
    ) {
        return false;
    }

    revokePendingBookImagePreviewUrls();

    [
        pendingBookImages[imageIndex],
        pendingBookImages[targetIndex]
    ] = [
        pendingBookImages[targetIndex],
        pendingBookImages[imageIndex]
    ];

    renderPendingBookImages();

    return true;
}

function addPendingBookImages(
    fileList
) {
    const files = Array.from(
        fileList || []
    );

    const imageFiles = files.filter(
        file =>
            file.type
                .toLowerCase()
                .startsWith("image/")
    );

    pendingBookImages.push(
        ...imageFiles
    );

    revokePendingBookImagePreviewUrls();

    renderPendingBookImages();

    return pendingBookImages.length;
}

async function prepareBookImageForUpload(
    file
) {
    const maxDimension = 2000;

    if (
        !file
        || !file.type
            .toLowerCase()
            .startsWith("image/")
    ) {
        return file;
    }

    const imageBitmap =
        await createImageBitmap(file);

    const originalWidth =
        imageBitmap.width;

    const originalHeight =
        imageBitmap.height;

    if (
        originalWidth <= maxDimension
        && originalHeight <= maxDimension
    ) {
        imageBitmap.close();

        return file;
    }

    const scale =
        Math.min(
            maxDimension / originalWidth,
            maxDimension / originalHeight
        );

    const targetWidth =
        Math.max(
            1,
            Math.round(
                originalWidth * scale
            )
        );

    const targetHeight =
        Math.max(
            1,
            Math.round(
                originalHeight * scale
            )
        );

    const canvas =
        document.createElement(
            "canvas"
        );

    canvas.width =
        targetWidth;

    canvas.height =
        targetHeight;

    const context =
        canvas.getContext(
            "2d"
        );

    if (!context) {
        imageBitmap.close();

        throw new Error(
            "A kép átméretezése nem sikerült."
        );
    }

    context.drawImage(
        imageBitmap,
        0,
        0,
        targetWidth,
        targetHeight
    );

    imageBitmap.close();

    const blob =
        await new Promise(
            (resolve, reject) => {
                canvas.toBlob(
                    result => {
                        if (!result) {
                            reject(
                                new Error(
                                    "A kép tömörítése nem sikerült."
                                )
                            );

                            return;
                        }

                        resolve(result);
                    },
                    "image/jpeg",
                    0.85
                );
            }
        );

    const originalName =
        file.name || "photo.jpg";

    const baseName =
        originalName.replace(
            /\.[^.]+$/,
            ""
        );

    return new File(
        [blob],
        `${baseName}.jpg`,
        {
            type: "image/jpeg",
            lastModified:
                Date.now()
        }
    );
}

async function uploadPendingBookImages(
    itemPublicId,
    onProgress = null
) {
    const normalizedItemPublicId =
        String(itemPublicId || "").trim();

    if (!normalizedItemPublicId) {
        throw new Error(
            "Hiányzik a létrehozott gyűjteményi elem azonosítója."
        );
    }

    if (pendingBookImages.length === 0) {
        return {
            uploadedCount: 0,
            totalCount: 0,
            originalBytes: 0,
            uploadedBytes: 0
        };
    }

    /*
     * Pillanatfelvételt készítünk a feltöltendő képekről.
     *
     * Így a pendingBookImages később módosítható anélkül,
     * hogy az aktuális feltöltési ciklus összekeveredne.
     */
    const filesToUpload = [
        ...pendingBookImages
    ];

    const totalCount =
        filesToUpload.length;

    let uploadedCount = 0;
    let originalBytes = 0;
    let uploadedBytes = 0;

    for (
        let index = 0;
        index < filesToUpload.length;
        index += 1
    ) {
        const file =
            filesToUpload[index];

        const uploadFile =
            await prepareBookImageForUpload(
                file
            );

        originalBytes +=
            file.size || 0;

        uploadedBytes +=
            uploadFile.size || 0;

        if (typeof onProgress === "function") {
            onProgress(
                index + 1,
                totalCount,
                file
            );
        }

        const formData =
            new FormData();

        formData.append(
            "file",
            uploadFile,
            uploadFile.name
                || `book-image-${index + 1}.jpg`
        );

        const response =
            await fetch(
                `/items/${normalizedItemPublicId}/images`,
                {
                    method: "POST",
                    body: formData
                }
            );

        let data = null;

        try {
            data =
                await response.json();
        } catch {
            data = null;
        }

        if (!response.ok) {
            /*
             * A már sikeresen feltöltött képeket kivesszük
             * a várakozó listából.
             *
             * Így egy későbbi újrapróbáláskor csak a hibás
             * és a még fel nem töltött képek maradnak.
             */
            revokePendingBookImagePreviewUrls();

            pendingBookImages =
                filesToUpload.slice(
                    uploadedCount
                );

            renderPendingBookImages();

            throw new Error(
                (
                    data?.detail
                    || data?.message
                    || `HTTP ${response.status}`
                )
                + ` Feltöltve: ${uploadedCount}`
                + ` / ${totalCount}.`
                + ` Hátralévő: `
                + `${pendingBookImages.length}.`
            );
        }

        uploadedCount += 1;
    }

    return {
        uploadedCount,
        totalCount,
        originalBytes,
        uploadedBytes
    };
}

async function finishCreatedBookImages(
    data,
    updateStatus
) {
    const itemPublicId =
        String(
            data?.public_id || ""
        ).trim();

    if (!itemPublicId) {
        throw new Error(
            "A könyv létrejött, de a szerver "
            + "nem adott vissza public_id értéket."
        );
    }

    const selectedImageCount =
        pendingBookImages.length;

    let imageUploadResult = {
        uploadedCount: 0,
        totalCount: selectedImageCount,
        originalBytes: 0,
        uploadedBytes: 0
    };

    if (selectedImageCount > 0) {
        if (typeof updateStatus === "function") {
            updateStatus(
                `✅ Könyv felvéve. `
                + `Képek feltöltése: 1`
                + ` / ${selectedImageCount}...`
            );
        }

        imageUploadResult =
            await uploadPendingBookImages(
                itemPublicId,
                (
                    currentIndex,
                    totalCount
                ) => {
                    if (
                        typeof updateStatus
                        === "function"
                    ) {
                        updateStatus(
                            `✅ Könyv felvéve. `
                            + `Képek feltöltése: `
                            + `${currentIndex}`
                            + ` / ${totalCount}...`
                        );
                    }
                }
            );
    }

    const legacyBookId =
        data?.id;

    const finalMessage =
        imageUploadResult.uploadedCount > 0
            ? (
                `✅ Könyv felvéve. `
                + `Egyedi index: ${legacyBookId}. `
                + `${imageUploadResult.uploadedCount} `
                + `kép feltöltve. `
                + `Eredeti méret: `
                + `${formatFileSize(
                    imageUploadResult.originalBytes
                )} → `
                + `feltöltve: `
                + `${formatFileSize(
                    imageUploadResult.uploadedBytes
                )}.`
            )
            : (
                `✅ Könyv felvéve. `
                + `Egyedi index: ${legacyBookId}`
            );

    clearPendingBookImages();

    return {
        itemPublicId,
        legacyBookId,

        uploadedCount:
            imageUploadResult.uploadedCount,

        totalCount:
            imageUploadResult.totalCount,

        originalBytes:
            imageUploadResult.originalBytes,

        uploadedBytes:
            imageUploadResult.uploadedBytes,

        message: finalMessage
    };
}

function formatFileSize(
    sizeInBytes
) {
    const size =
        Number(sizeInBytes || 0);

    if (size < 1024) {
        return `${size} B`;
    }

    if (size < 1024 * 1024) {
        return (
            `${(
                size / 1024
            ).toFixed(0)} KB`
        );
    }

    return (
        `${(
            size / 1024 / 1024
        ).toFixed(1)} MB`
    );
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
    return selectedStorage(place);
}

function fillStorageSelect(selectElement) {
    if (!selectElement) {
        return;
    }

    const currentValue =
        selectElement.value;

    selectElement.innerHTML =
        '<option value="">'
        + '-- válassz tárhelyet --'
        + '</option>';

    const locationsByRoot = new Map();

    for (const location of storageLocations) {
        if (!location.is_active) {
            continue;
        }

        const rootName =
            location.root_name || "Egyéb";

        if (!locationsByRoot.has(rootName)) {
            locationsByRoot.set(
                rootName,
                []
            );
        }

        locationsByRoot
            .get(rootName)
            .push(location);
    }

    for (
        const [rootName, locations]
        of locationsByRoot
    ) {
        const group =
            document.createElement(
                "optgroup"
            );

        group.label = rootName;

        for (const location of locations) {
            const option =
                document.createElement(
                    "option"
                );

            option.value =
                location.public_id;

            const relativePath =
                location.path_names
                    .slice(1)
                    .filter(
                        part =>
                            part
                            && part !== "-"
                    )
                    .join(" / ");

            option.textContent =
                relativePath
                || location.name;

            group.appendChild(option);
        }

        selectElement.appendChild(group);
    }

    const lastStoragePublicId =
        localStorage.getItem(
            "lastStoragePublicId"
        );

    if (
        currentValue
        && storageByPublicId.has(
            currentValue
        )
    ) {
        selectElement.value =
            currentValue;

    } else if (
        lastStoragePublicId
        && storageByPublicId.has(
            lastStoragePublicId
        )
    ) {
        selectElement.value =
            lastStoragePublicId;
    }
}

function selectedStorage(
    selectElement = place
) {
    if (!selectElement) {
        return null;
    }

    const publicId =
        selectElement.value.trim();

    if (!publicId) {
        return null;
    }

    return (
        storageByPublicId.get(publicId)
        ?? null
    );
}

function isBorrowedPlace(item) {
    return isBorrowedStorage(item);
}

function isRemovedPlace(item) {
    return isRemovedStorage(item);
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


async function loadStorageTree() {
    const response = await fetch(
        "/storage/tree"
        + "?household_id=1"
        + "&include_inactive=true"
    );

    if (!response.ok) {
        throw new Error(
            `HTTP ${response.status}`
        );
    }

    const data = await response.json();

    if (
        !data ||
        !Array.isArray(data.locations)
    ) {
        throw new Error(
            "A storage/tree hibás választ adott."
        );
    }

    storageLocations =
        flattenStorageTree(
            data.locations
        ).filter(
            location =>
                location.location_type === "slot"
        );

    storageByPublicId = new Map(
        storageLocations.map(
            location => [
                location.public_id,
                location
            ]
        )
    );

const borrowedStorage =
    storageLocations.find(
        location =>
            location.is_active
            && isBorrowedStorage(location)
    );

const removedStorage =
    storageLocations.find(
        location =>
            location.is_active
            && isRemovedStorage(location)
    );

borrowedStoragePublicId =
    borrowedStorage?.public_id || null;

removedStoragePublicId =
    removedStorage?.public_id || null;

fillStorageSelect(place);
fillStorageSelect(manualLocation);
fillStorageSelect(missingMetadataLocation);
syncSpecialControlsFromPlace();
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
    "lastStoragePublicId",
    selected.public_id
);
    }
}

function restoreLastNormalLocation() {
    if (!place) {
        return;
    }

    const lastStoragePublicId =
        localStorage.getItem(
            "lastStoragePublicId"
        );

    if (
        lastStoragePublicId
        && storageByPublicId.has(
            lastStoragePublicId
        )
    ) {
        place.value =
            lastStoragePublicId;
    } else {
        place.value = "";
    }

    syncSpecialControlsFromPlace();
}

if (place) {
    place.addEventListener(
        "change",
        syncSpecialControlsFromPlace
    );
}


if (borrowed) {
    borrowed.addEventListener(
        "change",
        () => {
            if (borrowed.checked) {
                if (removed) {
                    removed.checked = false;
                }

                if (
                    borrowedStoragePublicId
                    && place
                ) {
                    place.value =
                        borrowedStoragePublicId;
                }

                syncSpecialControlsFromPlace();

                if (borrower) {
                    borrower.focus();
                }

                return;
            }

            if (
                isBorrowedPlace(
                    selectedPlace()
                )
            ) {
                restoreLastNormalLocation();
            } else {
                syncSpecialControlsFromPlace();
            }
        }
    );
}


if (removed) {
    removed.addEventListener(
        "change",
        () => {
            if (removed.checked) {
                if (borrowed) {
                    borrowed.checked = false;
                }

                if (borrower) {
                    borrower.value = "";
                }

                if (
                    removedStoragePublicId
                    && place
                ) {
                    place.value =
                        removedStoragePublicId;
                }

                syncSpecialControlsFromPlace();

                return;
            }

            if (
                isRemovedPlace(
                    selectedPlace()
                )
            ) {
                restoreLastNormalLocation();
            } else {
                syncSpecialControlsFromPlace();
            }
        }
    );
}

if (
    pendingBookCameraButton
    && pendingBookCameraInput
) {
    pendingBookCameraButton.addEventListener(
        "click",
        () => {
            pendingBookCameraInput.click();
        }
    );
}


if (
    pendingBookFilesButton
    && pendingBookFilesInput
) {
    pendingBookFilesButton.addEventListener(
        "click",
        () => {
            pendingBookFilesInput.click();
        }
    );
}


if (pendingBookCameraInput) {
    pendingBookCameraInput.addEventListener(
        "change",
        () => {
            addPendingBookImages(
                pendingBookCameraInput.files
            );

            pendingBookCameraInput.value = "";
        }
    );
}


if (pendingBookFilesInput) {
    pendingBookFilesInput.addEventListener(
        "change",
        () => {
            addPendingBookImages(
                pendingBookFilesInput.files
            );

            pendingBookFilesInput.value = "";
        }
    );
}


if (pendingBookImagesClearButton) {
    pendingBookImagesClearButton.addEventListener(
        "click",
        () => {
            clearPendingBookImages();
        }
    );
}

if (pendingBookImagePreview) {
    pendingBookImagePreview.addEventListener(
        "click",
        event => {
            const orderButton =
                event.target.closest(
                    "[data-pending-image-action]"
                );

            if (orderButton) {
                const imageIndex =
                    Number(
                        orderButton.dataset
                            .pendingImageIndex
                    );

                const direction =
                    orderButton.dataset
                        .pendingImageAction;

                movePendingBookImage(
                    imageIndex,
                    direction
                );

                return;
            }

            const removeButton =
                event.target.closest(
                    "[data-pending-image-index]"
                );

            if (!removeButton) {
                return;
            }

            /*
             * A mozgatógombok is rendelkeznek
             * data-pending-image-index attribútummal,
             * de azokat fent már kezeltük.
             */
            const imageIndex =
                Number(
                    removeButton.dataset
                        .pendingImageIndex
                );

            removePendingBookImage(
                imageIndex
            );
        }
    );
}

renderPendingBookImages();

// --------------------------------------------------
// ISBN-ES KÖNYV MENTÉSE
// --------------------------------------------------

async function send() {
    const cleanIsbn =
        normalizeIsbn(isbn?.value);

const storagePublicId =
    place?.value?.trim() || "";

const selected =
    selectedStorage(place);

if (!storagePublicId || !selected) {
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

    storage_public_id:
        storagePublicId,

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

    storagePublicId:
        data.storage_public_id
        || storagePublicId,

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

        const creationResult =
            await finishCreatedBookImages(
                data,
                message => {
                    showStatus(
                        message,
                        "success"
                    );
                }
            );

        showStatus(
            creationResult.message,
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
    `${book.slot}. hely`
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

const lastStoragePublicId =
    localStorage.getItem(
        "lastStoragePublicId"
    );

if (
    lastStoragePublicId
    && storageByPublicId.has(
        lastStoragePublicId
    )
    && manualLocation
) {
    manualLocation.value =
        lastStoragePublicId;
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

const storagePublicId =
    manualLocation.value.trim();

const selected =
    selectedStorage(manualLocation);

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

if (!storagePublicId || !selected) {
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

storage_public_id:
    storagePublicId
                })
            });

        const data =
            await response.json();

        if (
            !response.ok
            || data.status === "error"
        ) {
            throw new Error(
                data.message
                || `HTTP ${response.status}`
            );
        }

        const creationResult =
            await finishCreatedBookImages(
                data,
                message => {
                    manualStatus.textContent =
                        message;
                }
            );

        localStorage.setItem(
            "lastStoragePublicId",
            storagePublicId
        );

        if (place) {
            place.value =
                storagePublicId;

            syncSpecialControlsFromPlace();
        }

        closeManualModal();

        showStatus(
            creationResult.message,
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
    storagePublicId,
    borrower
}) {
    missingMetadataIsbn.value =
        isbn || "";

    missingMetadataTitle.value = "";
    missingMetadataAuthor.value = "";
    missingMetadataPublisher.value = "";
    missingMetadataYear.value = "";

missingMetadataLocation.value =
    storagePublicId || "";

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

const storagePublicId =
    missingMetadataLocation.value.trim();

const selected =
    selectedStorage(
        missingMetadataLocation
    );

    if (!title) {
        missingMetadataStatus.textContent =
            "❌ Add meg a könyv címét.";

        missingMetadataTitle.focus();
        return;
    }

if (!storagePublicId || !selected) {
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

storage_public_id:
    storagePublicId,

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
    !response.ok
    || data.status === "error"
) {
    throw new Error(
        data.message
        || `HTTP ${response.status}`
    );
}

        const creationResult =
            await finishCreatedBookImages(
                data,
                message => {
                    missingMetadataStatus
                        .textContent =
                            message;
                }
            );

        localStorage.setItem(
            "lastStoragePublicId",
            storagePublicId
        );

        if (place) {
            place.value =
                storagePublicId;

            syncSpecialControlsFromPlace();
        }

        missingMetadataModal.style.display =
            "none";

        document.body.style.overflow = "";

        isbn.value = "";

        showStatus(
            creationResult.message,
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
    await loadStorageTree();
    await loadLatest();

    if (place?.value) {
        isbn?.focus();
    } else {
        place?.focus();
    }
}

initialize();
