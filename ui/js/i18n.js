"use strict";

(function () {
    const STORAGE_KEY = "familycollection_language";
    const DEFAULT_LANGUAGE = "en";
    const SUPPORTED_LANGUAGES = ["en", "hu"];

    const translations = {
        en: {
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
