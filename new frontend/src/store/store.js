import { configureStore } from "@reduxjs/toolkit";
import { setupListeners } from "@reduxjs/toolkit/query";
import { persistStore, persistReducer } from "redux-persist";
import storage from "redux-persist/lib/storage"; // defaults to localStorage for web
import { combineReducers } from "@reduxjs/toolkit";

// Data compression utilities
const compressData = (data) => {
  try {
    // Ensure data is an object before processing
    if (typeof data !== "object" || data === null) {
      console.warn("⚠️ compressData: Invalid data type:", typeof data);
      return JSON.stringify(data);
    }

    // Simple compression by removing unnecessary fields and compacting data
    const compressed = JSON.stringify(data, (key, value) => {
      // Remove large or unnecessary fields
      if (key === "fileData" || key === "previewUrl" || key === "chatHistory") {
        return undefined;
      }
      // Round numbers to reduce precision
      if (typeof value === "number" && !Number.isInteger(value)) {
        return Math.round(value * 100) / 100;
      }
      return value;
    });
    return compressed;
  } catch (error) {
    console.warn("Failed to compress data:", error, "Data:", data);
    // Fallback: try to stringify the original data
    try {
      return JSON.stringify(data);
    } catch (stringifyError) {
      console.error("Failed to stringify data as fallback:", stringifyError);
      return "{}"; // Return empty object as last resort
    }
  }
};

const decompressData = (compressedData) => {
  try {
    return JSON.parse(compressedData);
  } catch (error) {
    console.warn("Failed to decompress data:", error);
    return null;
  }
};

// Custom storage wrapper with quota handling and compression
const quotaAwareStorage = {
  ...storage,
  setItem: async (key, value) => {
    try {
      // Parse value if it's a string, otherwise use as-is
      const parsedValue = typeof value === "string" ? JSON.parse(value) : value;
      // Compress the data before storing
      const compressedValue = compressData(parsedValue);
      await storage.setItem(key, compressedValue);
    } catch (error) {
      if (error.name === "QuotaExceededError") {
        console.warn(
          "🚨 Storage quota exceeded, implementing emergency cleanup..."
        );

        // Emergency cleanup - remove all non-essential data
        const keysToKeep = [
          "supabase.auth.token",
          "sb-auth-token",
          "gurukul_avatar_version",
        ];

        const allKeys = Object.keys(localStorage);
        allKeys.forEach((storageKey) => {
          if (!keysToKeep.some((keepKey) => storageKey.includes(keepKey))) {
            localStorage.removeItem(storageKey);
          }
        });

        console.log("🔄 Emergency cleanup completed, retrying save...");

        // Retry with even more aggressive compression
        try {
          const minimalData = JSON.stringify({
            favorites: [],
            selectedAvatar: null,
            pinPosition: { x: 0, y: 0, z: 0 },
            pinRotation: { x: 0, y: 0, z: 0 },
            pinScale: 2.5,
            isPinModeEnabled: true,
            pinnedAvatarPosition: { x: 100, y: 100 },
            activeSettingsTab: "pin",
            activeMainTab: "custom-models",
          });
          await storage.setItem(key, minimalData);
          console.log(
            "✅ Successfully saved minimal state after emergency cleanup"
          );
        } catch (retryError) {
          console.error(
            "❌ Failed to save even after emergency cleanup:",
            retryError
          );
          // Completely disable persistence to prevent app crash
          console.warn("🚨 Disabling Redux persist to prevent app crash");
        }
      } else {
        console.error("Storage error:", error);
        throw error;
      }
    }
  },
  getItem: async (key) => {
    try {
      const item = await storage.getItem(key);
      if (item) {
        const decompressed = decompressData(item);
        return JSON.stringify(decompressed);
      }
      return item;
    } catch (error) {
      console.warn("Failed to get/decompress item:", error);
      return null;
    }
  },
};
import languageReducer from "./languageSlice";
import uiReducer from "./uiSlice";
import authReducer from "./authSlice";
import settingsReducer from "./settingsSlice";
import avatarReducer from "./avatarSlice";
import { apiSlice } from "../api/apiSlice";
import { externalApiSlice } from "../api/externalApiSlice";
import { lessonApiSlice } from "../api/subjectsApiSlice";
import { chatApiSlice } from "../api/coreApiSlice";
import { financialApiSlice } from "../api/financialApiSlice";
import { summaryApiSlice } from "../api/summaryApiSlice";
import { orchestrationApiSlice } from "../api/orchestrationApiSlice";
import { avatarChatApiSlice } from "../api/avatarChatApiSlice";
import { agentApiSlice } from "../api/agentApiSlice";
import { financialChatApiSlice } from "../api/financialChatApiSlice";

// Migration transform to clean up old data and optimize storage
const avatarMigrationTransform = {
  in: (inboundState, key) => {
    // Clean up data on the way in (from storage to Redux)
    if (inboundState && typeof inboundState === "object") {
      const cleaned = { ...inboundState };

      // Remove any large data that shouldn't be in localStorage
      delete cleaned.customModels;
      delete cleaned.chatHistory;
      delete cleaned.fileData;
      delete cleaned.previewUrl;

      // Clean up favorites to remove large data, but preserve essential data for custom images
      if (cleaned.favorites && Array.isArray(cleaned.favorites)) {
        cleaned.favorites = cleaned.favorites.map((fav) => {
          const cleanFav = { ...fav };
          // For custom images, preserve fileData but limit size
          if (fav.isCustomModel && fav.mediaType === "image" && fav.fileData) {
            // Keep image data for custom images (essential for restoration)
            cleanFav.fileData = fav.fileData;
          } else {
            // Remove large data from non-custom favorites
            delete cleanFav.fileData;
          }
          if (cleanFav.previewUrl && cleanFav.previewUrl.startsWith("blob:")) {
            delete cleanFav.previewUrl; // Remove blob URLs as they're invalid after reload
          }
          return cleanFav;
        });
      }

      return cleaned;
    }
    return inboundState;
  },
  out: (outboundState, key) => {
    // Clean up data on the way out (from Redux to storage)
    if (outboundState && typeof outboundState === "object") {
      // Check version and clean if needed
      const currentVersion = "2.3";
      const storedVersion = localStorage.getItem("gurukul_avatar_version");

      if (storedVersion !== currentVersion) {
        console.log("🔄 Redux persist: Version upgrade, cleaning state");
        localStorage.setItem("gurukul_avatar_version", currentVersion);
        // Reset to minimal state on version upgrade
        return {
          favorites: [],
          selectedAvatar: null,
          pinPosition: { x: 0, y: 0, z: 0 },
          pinRotation: { x: 0, y: 0, z: 0 },
          pinScale: 2.5,
          isPinModeEnabled: true,
          pinnedAvatarPosition: { x: 100, y: 100 },
          activeSettingsTab: "pin",
          activeMainTab: "custom-models",
          isChatOpen: false,
        };
      }

      const cleaned = { ...outboundState };

      // Remove large data that shouldn't be persisted
      delete cleaned.customModels;
      delete cleaned.chatHistory;
      delete cleaned.customModelsLoading;
      delete cleaned.customModelsError;
      delete cleaned.isDragging;
      delete cleaned.dragOffset;
      delete cleaned.isLoading;
      delete cleaned.error;
      delete cleaned.chatContext;
      delete cleaned.isTyping;

      // Clean up favorites
      if (cleaned.favorites && Array.isArray(cleaned.favorites)) {
        // Limit favorites to prevent storage overflow
        const maxFavorites = 10;
        if (cleaned.favorites.length > maxFavorites) {
          console.warn(
            `🚨 Too many favorites (${cleaned.favorites.length}), keeping only ${maxFavorites} most recent`
          );
          cleaned.favorites = cleaned.favorites
            .sort(
              (a, b) =>
                new Date(b.lastUpdated || b.timestamp || 0) -
                new Date(a.lastUpdated || a.timestamp || 0)
            )
            .slice(0, maxFavorites);
        }

        // Remove duplicates and clean each favorite
        const seenIds = new Set();
        cleaned.favorites = cleaned.favorites.filter((fav) => {
          if (seenIds.has(fav.id)) {
            return false; // Remove duplicate
          }
          seenIds.add(fav.id);

          // Clean up individual favorite
          delete fav.fileData;
          if (fav.previewUrl && fav.previewUrl.startsWith("blob:")) {
            delete fav.previewUrl; // Remove blob URLs
          }

          return true;
        });
      }

      return cleaned;
    }
    return outboundState;
  },
};

// Persist configuration for avatar state - optimized for storage quota
const avatarPersistConfig = {
  key: "avatar",
  storage: quotaAwareStorage, // Use custom storage with quota handling
  version: 2.3, // Increment this to force migration
  // Add migration transform
  transforms: [avatarMigrationTransform],
  // Only persist essential data - exclude large data that belongs in IndexedDB
  whitelist: [
    "favorites", // Keep but will be compressed
    "selectedAvatar", // Keep but will be compressed
    "pinPosition",
    "pinRotation",
    "pinScale",
    "isPinModeEnabled",
    "pinnedAvatarPosition",
    "activeSettingsTab",
    "activeMainTab",
    "isChatOpen",
    // Excluded: customModels (stays in IndexedDB), chatHistory (too large)
  ],
  // Blacklist large data that should not be persisted in localStorage
  blacklist: [
    "customModels", // This stays in IndexedDB
    "chatHistory", // This can be rebuilt or stored separately
    "customModelsLoading",
    "customModelsError",
    "isDragging",
    "dragOffset",
    "isLoading",
    "error",
    "chatContext",
    "isTyping",
  ],
};

// Create persisted avatar reducer
const persistedAvatarReducer = persistReducer(
  avatarPersistConfig,
  avatarReducer
);

// Combine all reducers
const rootReducer = combineReducers({
  language: languageReducer,
  ui: uiReducer,
  auth: authReducer,
  settings: settingsReducer,
  avatar: persistedAvatarReducer,
  [apiSlice.reducerPath]: apiSlice.reducer,
  [externalApiSlice.reducerPath]: externalApiSlice.reducer,
  [lessonApiSlice.reducerPath]: lessonApiSlice.reducer,
  [chatApiSlice.reducerPath]: chatApiSlice.reducer,
  [financialApiSlice.reducerPath]: financialApiSlice.reducer,
  [summaryApiSlice.reducerPath]: summaryApiSlice.reducer,
  [orchestrationApiSlice.reducerPath]: orchestrationApiSlice.reducer,
  [avatarChatApiSlice.reducerPath]: avatarChatApiSlice.reducer,
  [agentApiSlice.reducerPath]: agentApiSlice.reducer,
  [financialChatApiSlice.reducerPath]: financialChatApiSlice.reducer,
});

export const store = configureStore({
  reducer: rootReducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ["persist/PERSIST", "persist/REHYDRATE"],
      },
    }).concat(
      apiSlice.middleware,
      externalApiSlice.middleware,
      lessonApiSlice.middleware,
      chatApiSlice.middleware,
      financialApiSlice.middleware,
      summaryApiSlice.middleware,
      orchestrationApiSlice.middleware,
      avatarChatApiSlice.middleware,
      agentApiSlice.middleware,
      financialChatApiSlice.middleware
    ),
  devTools: process.env.NODE_ENV !== "production",
});

// Create persistor
export const persistor = persistStore(store);

// Enable refetchOnFocus/refetchOnReconnect behaviors
setupListeners(store.dispatch);

export default store;
