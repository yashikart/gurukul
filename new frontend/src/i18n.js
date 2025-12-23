import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import { translations } from "./store/languageSlice";

// Get initial language from localStorage or default to English
const getInitialLanguage = () => {
  try {
    const settings = localStorage.getItem("gurukul_settings");
    if (settings) {
      const parsed = JSON.parse(settings);
      return parsed.language || "english";
    }
    return "english";
  } catch (error) {
    console.error("Error reading language from storage:", error);
    return "english";
  }
};

// Initialize i18next
i18n.use(initReactI18next).init({
  resources: {
    english: {
      translation: {}, // English is the default, no translations needed
    },
    hindi: {
      translation: translations.hindi,
    },
    marathi: {
      translation: translations.marathi,
    },
    arabic: {
      translation: translations.arabic,
    },
  },
  lng: getInitialLanguage(),
  fallbackLng: "english",
  interpolation: {
    escapeValue: false, // React already safes from XSS
  },
});

export default i18n;
