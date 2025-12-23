  import React, {
  useState,
  useEffect,
  useRef,
  useMemo,
  useCallback,
} from "react";
import { useSelector, useDispatch } from "react-redux";
import GlassContainer from "../components/GlassContainer";

import AvatarSettingsTabs from "../components/AvatarSettingsTabs";
import { toast } from "react-hot-toast";
import gsap from "gsap";
import { useTranslation } from "react-i18next";
// Note: storage utils now handled by individual components
import { User, Heart, Upload } from "lucide-react";

import {
  selectFavorites,
  selectSelectedAvatar,
  selectPinPosition,
  selectPinRotation,
  selectPinScale,
  selectIsPinModeEnabled,
  selectPinnedAvatarPosition,
  selectActiveSettingsTab,
  selectActiveMainTab,
  selectHasUnsavedChanges,
  resetPinSettings,
  autoSaveAvatarSettings,
  setActiveMainTab,
} from "../store/avatarSlice";
import { useAvatarPersistence } from "../hooks/useAvatarPersistence";
import { testPersistence } from "../utils/testPersistence";

// Performance optimizations and loading states
import FavoritesTab from "../components/FavoritesTab";
import CustomModelsTab from "../components/CustomModelsTab";
import {
  LoadingOverlay,
} from "../components/LoadingSkeletons";
import { usePerformanceMonitor } from "../hooks/usePerformanceMonitor";



export default function AvatarSelection() {
  const { t } = useTranslation();
  const dispatch = useDispatch();
  const containerRef = useRef(null);

  // Performance monitoring
  usePerformanceMonitor("AvatarSelection", {
    enableLogging: true,
    logThreshold: 20,
  });

  // Redux state selectors with performance tracking
  const favorites = useSelector(selectFavorites);
  const selectedAvatar = useSelector(selectSelectedAvatar);
  const pinPosition = useSelector(selectPinPosition);
  const pinRotation = useSelector(selectPinRotation);
  const pinScale = useSelector(selectPinScale);
  const isPinModeEnabled = useSelector(selectIsPinModeEnabled);
  const pinnedAvatarPosition = useSelector(selectPinnedAvatarPosition);
  const activeSettingsTab = useSelector(selectActiveSettingsTab);
  const activeMainTab = useSelector(selectActiveMainTab);
  const hasUnsavedChanges = useSelector(selectHasUnsavedChanges);

  // Initialize avatar persistence
  useAvatarPersistence();

  // Emergency storage cleanup on mount
  useEffect(() => {
    const checkStorageQuota = async () => {
      try {
        if ("storage" in navigator && "estimate" in navigator.storage) {
          const estimate = await navigator.storage.estimate();
          const usagePercentage = (estimate.usage / estimate.quota) * 100;

          if (usagePercentage > 90) {
            console.warn("🚨 Storage quota nearly exceeded, clearing old data");
            // Clear old localStorage data
            Object.keys(localStorage).forEach((key) => {
              if (key.includes("redux-persist") || key.includes("gurukul")) {
                try {
                  localStorage.removeItem(key);
                } catch (e) {
                  console.error("Failed to clear storage item:", key, e);
                }
              }
            });

            // Force page reload to reset state
            window.location.reload();
          }
        }
      } catch (error) {
        console.error("Storage quota check failed:", error);
      }
    };

    checkStorageQuota();
  }, []);

  // Loading states for performance optimization
  const [isInitialLoading, setIsInitialLoading] = useState(true);

  // Debug favorites state (development only)
  useEffect(() => {
    if (import.meta.env.DEV) {
      console.log("🎯 AvatarSelection - Favorites state:", favorites);
      console.log("🎯 AvatarSelection - Selected avatar:", selectedAvatar);
    }
  }, [favorites, selectedAvatar]);

  // Test persistence on mount (development only)
  useEffect(() => {
    if (import.meta.env.DEV) {
      testPersistence();
    }
  }, []);

  // Handle initial loading state
  useEffect(() => {
    const timer = setTimeout(() => {
      setIsInitialLoading(false);
    }, 500);
    return () => clearTimeout(timer);
  }, []);

  // Local state removed - no generation features needed

  // Animation effects
  useEffect(() => {
    if (containerRef.current) {
      gsap.fromTo(
        containerRef.current.children,
        { opacity: 0, y: 20 },
        { opacity: 1, y: 0, duration: 0.6, stagger: 0.1, ease: "power2.out" }
      );
    }
  }, []);

  // Note: Favorites and avatar state initialization is now handled by useAvatarPersistence hook

  // Note: Pin Avatar drag functionality is now handled by GlobalPinnedAvatar component

  // Optimized event handlers with useCallback to prevent unnecessary re-renders
  const resetPinnedAvatar = useCallback(() => {
    dispatch(resetPinSettings());
    toast.success(t("Avatar reset to default position"));
  }, [dispatch, t]);

  // Tab switching handler
  const handleTabChange = useCallback((tabId) => {
    dispatch(setActiveMainTab(tabId));
  }, [dispatch]);

  // Save current avatar position and settings
  const handleSavePosition = useCallback(() => {
    if (!selectedAvatar) {
      toast.error(t("No avatar selected"));
      return;
    }

    try {
      dispatch(autoSaveAvatarSettings());
      toast.success(t("Position saved for") + ` "${selectedAvatar.name}"!`);
    } catch (error) {
      console.error("Error saving avatar position:", error);
      toast.error(t("Failed to save position"));
    }
  }, [selectedAvatar, dispatch, t]);

  // Note: Auto-save is now handled by the useAvatarPersistence hook and Redux

  // Generation handlers removed - no longer needed



  // Removed manual save function - now only using heart icon save

  // Note: handleLoadFavorite is now handled by FavoritesTab component

  // Note: handleDeleteFavorite is now handled by FavoritesTab component

  // Emergency storage clear function
  const handleEmergencyStorageClear = useCallback(() => {
    try {
      console.log("🚨 Emergency storage clear initiated");
      localStorage.clear();
      sessionStorage.clear();

      // Clear IndexedDB if available
      if ("indexedDB" in window) {
        indexedDB.deleteDatabase("gurukul-avatars");
      }

      toast.success(t("Storage cleared! Reloading page..."));
      setTimeout(() => window.location.reload(), 1000);
    } catch (error) {
      console.error("Emergency storage clear failed:", error);
      toast.error(t("Failed to clear storage"));
    }
  }, [t]);

  // Removed old save avatar function - now using favorites only

  return (
    <div className="h-full">
      <GlassContainer>
        <div ref={containerRef} className="flex flex-col h-full">
          {/* Simple Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-white mb-2">
              {t("Avatar Management")}
            </h1>
            <p className="text-white/60">
              {t("Manage your favorite avatars")}
            </p>
          </div>

          <div className="flex-1 flex flex-col">
            {/* Tab Navigation */}
            <div className="flex justify-center space-x-4 mb-6 relative z-10">
              <button
                onClick={() => handleTabChange("favorites")}
                className={`flex items-center justify-center space-x-2 px-4 py-3 rounded-lg transition-all w-32 border ${
                  activeMainTab === "favorites"
                    ? 'bg-orange-500/30 text-orange-300 border-orange-400/60 shadow-lg shadow-orange-500/20'
                    : 'text-white/90 hover:text-white hover:bg-white/20 bg-white/10 border-white/20 hover:border-white/40'
                }`}
              >
                <Heart className="w-4 h-4" />
                <span className="font-medium">{t("Favorites")}</span>
              </button>
              <button
                onClick={() => handleTabChange("custom-models")}
                className={`flex items-center justify-center space-x-2 px-4 py-3 rounded-lg transition-all w-32 border ${
                  activeMainTab === "custom-models"
                    ? 'bg-orange-500/30 text-orange-300 border-orange-400/60 shadow-lg shadow-orange-500/20'
                    : 'text-white/90 hover:text-white hover:bg-white/20 bg-white/10 border-white/20 hover:border-white/40'
                }`}
              >
                <Upload className="w-4 h-4" />
                <span className="font-medium text-sm">{t("Upload")}</span>
              </button>
            </div>

            {/* Content Area - Two Column Layout */}
            <div className="flex-1 grid grid-cols-1 lg:grid-cols-5 gap-6 min-h-0">
              {/* Left Column - Tab Content */}
              <div className="lg:col-span-4">
                <div className="bg-white/5 backdrop-blur-sm rounded-xl border border-white/10 p-6 h-full relative flex flex-col min-h-0 z-0">
                  {activeMainTab === "favorites" ? (
                    <FavoritesTab />
                  ) : (
                    <CustomModelsTab />
                  )}
                </div>
              </div>

              {/* Right Column - Avatar Settings Only */}
              <div className="lg:col-span-1 flex flex-col min-h-0">
                {selectedAvatar ? (
                  <AvatarSettingsTabs
                    selectedAvatar={selectedAvatar}
                    // Pin Mode Settings
                    pinPosition={pinPosition}
                    pinRotation={pinRotation}
                    pinScale={pinScale}
                    // Pin Mode State
                    isPinModeEnabled={isPinModeEnabled}
                    pinnedAvatarPosition={pinnedAvatarPosition}
                    // Settings Tab State
                    activeSettingsTab={activeSettingsTab}
                    // Actions
                    handleSavePosition={handleSavePosition}
                    resetPinnedAvatar={resetPinnedAvatar}
                    hasUnsavedChanges={hasUnsavedChanges}
                    // Redux dispatch for state updates
                    dispatch={dispatch}
                  />
                ) : (
                  <div className="bg-white/5 backdrop-blur-sm rounded-xl border border-white/10 p-6 h-full flex flex-col items-center justify-center">
                    <div className="text-white/50 text-center">
                      <User className="w-16 h-16 mx-auto mb-3 opacity-50" />
                      <p className="text-lg mb-2">{t("Select an Avatar")}</p>
                      <p className="text-sm mb-6">
                        {t("Choose an avatar from your favorites to customize it")}
                      </p>

                      {/* Emergency Storage Clear Button */}
                      <button
                        onClick={handleEmergencyStorageClear}
                        className="px-4 py-2 bg-red-500/20 text-red-400 text-xs rounded hover:bg-red-500/30 transition-colors border border-red-500/30"
                        title={t("Clear all storage data if experiencing issues")}
                      >
                        🚨 {t("Emergency Clear Storage")}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </GlassContainer>

      {/* Note: Pinned Avatar is now handled globally by GlobalPinnedAvatar component in Layout */}
    </div>
  );
}
