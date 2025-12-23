import React, { useState, useCallback, useMemo, useEffect } from "react";
// Pin icon import removed - no longer needed
import {
  setPinPosition,
  setPinRotation,
  setPinScale,
  setIsPinModeEnabled,
  setPinnedAvatarPosition,
} from "../store/avatarSlice";
import StorageQuotaManager from "../utils/storageQuotaManager";
import ImageAvatarSettings from "./ImageAvatarSettings";
import { useTranslation } from "react-i18next";


// Inject custom scrollbar styles
const injectScrollbarStyles = () => {
  const styleId = "avatar-settings-scrollbar-styles";
  if (!document.getElementById(styleId)) {
    const style = document.createElement("style");
    style.id = styleId;
    style.textContent = `
      .avatar-settings-scroll {
        scrollbar-width: thin;
        scrollbar-color: rgba(255, 255, 255, 0.3) rgba(255, 255, 255, 0.1);
        scroll-behavior: smooth;
      }

      .avatar-settings-scroll::-webkit-scrollbar {
        width: 8px;
      }

      .avatar-settings-scroll::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 4px;
        margin: 2px;
      }

      .avatar-settings-scroll::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.3);
        border-radius: 4px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: background 0.2s ease;
      }

      .avatar-settings-scroll::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 255, 255, 0.5);
      }

      .avatar-settings-scroll::-webkit-scrollbar-thumb:active {
        background: rgba(255, 255, 255, 0.6);
      }

      /* Ensure scroll wheel works on all browsers */
      .avatar-settings-scroll {
        overflow-y: auto !important;
        overflow-x: hidden;
      }

      .avatar-settings-scroll::-webkit-scrollbar-corner {
        background: transparent;
      }
    `;
    document.head.appendChild(style);
  }
};

/**
 * Tabbed Avatar Settings Component
 * Provides separate controls for Grid View and Pin Mode settings
 */
export default function AvatarSettingsTabs({
  selectedAvatar,
  // Pin Mode Settings
  pinPosition,
  pinRotation,
  pinScale,
  // Pin Mode State
  isPinModeEnabled,
  pinnedAvatarPosition,
  // Settings Tab State (controlled by parent)
  activeSettingsTab,
  // Actions
  handleSavePosition,
  resetPinnedAvatar,
  hasUnsavedChanges,
  // Redux dispatch
  dispatch,
}) {
  const { t } = useTranslation();
  // Inject scrollbar styles on component mount
  useEffect(() => {
    injectScrollbarStyles();
  }, []);

  const handlePinModeToggle = async () => {
    try {
      const newPinModeState = !isPinModeEnabled;
      console.log("🎭 Toggling pin mode:", { from: isPinModeEnabled, to: newPinModeState });

      dispatch(setIsPinModeEnabled(newPinModeState));

      if (newPinModeState) {
        // When enabling pin mode, ensure proper initialization
        console.log("🎭 Initializing pin mode settings");

        // Set initial screen position if not already set
        if (!pinnedAvatarPosition || (pinnedAvatarPosition.x === 0 && pinnedAvatarPosition.y === 0)) {
          dispatch(setPinnedAvatarPosition({ x: 100, y: 100 }));
        }

        // Ensure pin settings are initialized with reasonable defaults
        if (!pinPosition || (pinPosition.x === 0 && pinPosition.y === 0 && pinPosition.z === 0)) {
          dispatch(setPinPosition({ x: 0, y: 0.5, z: -4.0 })); // Better position for jupiter.glb
        }
        if (!pinRotation || (pinRotation.x === 0 && pinRotation.y === 0 && pinRotation.z === 0)) {
          dispatch(setPinRotation({ x: 0, y: 180, z: 0 })); // Face forward by default
        }
        if (!pinScale || pinScale === 0) {
          dispatch(setPinScale(2.5)); // Good default scale for floating avatar
        }

        console.log("🎭 Pin mode enabled with settings:", {
          pinnedAvatarPosition: pinnedAvatarPosition || { x: 100, y: 100 },
          pinPosition: pinPosition || { x: 0, y: 0, z: 0 },
          pinRotation: pinRotation || { x: 0, y: 180, z: 0 },
          pinScale: pinScale || 2.5
        });
      } else {
        console.log("🎭 Pin mode disabled");
      }
    } catch (error) {
      if (error.name === "QuotaExceededError") {
        console.warn("🚨 Storage quota exceeded in pin mode toggle");
        const result = await StorageQuotaManager.handleQuotaExceeded();
        if (result !== "failed") {
          setTimeout(() => window.location.reload(), 1000);
        }
      } else {
        console.error("Error toggling pin mode:", error);
      }
    }
  };

  // Settings tabs removed - only pin mode now

  const renderPositionControls = useCallback(
    (position, positionAction, label) => {
      const handleXChange = (e) => {
        const value = parseFloat(e.target.value);
        // Allow NaN to be converted to 0, but preserve valid numbers including 0
        const finalValue = isNaN(value) ? 0 : value;
        console.log(`🎛️ ${label} X Position changed:`, {
          old: position.x,
          new: finalValue,
        });
        dispatch(positionAction({ ...position, x: finalValue }));
      };

      const handleYChange = (e) => {
        const value = parseFloat(e.target.value);
        const finalValue = isNaN(value) ? 0 : value;
        console.log(`🎛️ ${label} Y Position changed:`, {
          old: position.y,
          new: finalValue,
        });
        dispatch(positionAction({ ...position, y: finalValue }));
      };

      const handleZChange = (e) => {
        const value = parseFloat(e.target.value);
        const finalValue = isNaN(value) ? 0 : value;
        console.log(`🎛️ ${label} Z Position changed:`, {
          old: position.z,
          new: finalValue,
        });
        dispatch(positionAction({ ...position, z: finalValue }));
      };

      return (
        <div className="space-y-3">
          <h3 className="text-white font-medium text-sm">{t(label)} {t("Position")}</h3>

          {/* Compact grid layout for X, Y, Z */}
          <div className="grid grid-cols-3 gap-2">
            {/* X Position */}
            <div>
              <label className="block text-white/70 text-xs mb-1">X</label>
              <input
                type="number"
                min="-5"
                max="5"
                step="0.1"
                value={position.x.toFixed(1)}
                onChange={handleXChange}
                className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded text-white text-sm focus:outline-none number-input"
              />
            </div>

            {/* Y Position */}
            <div>
              <label className="block text-white/70 text-xs mb-1">Y</label>
              <input
                type="number"
                min="-5"
                max="5"
                step="0.1"
                value={position.y.toFixed(1)}
                onChange={handleYChange}
                className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded text-white text-sm focus:outline-none number-input"
              />
            </div>

            {/* Z Position */}
            <div>
              <label className="block text-white/70 text-xs mb-1">Z</label>
              <input
                type="number"
                min="-5"
                max="5"
                step="0.1"
                value={position.z.toFixed(1)}
                onChange={handleZChange}
                className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded text-white text-sm focus:outline-none number-input"
              />
            </div>
          </div>
        </div>
      );
    },
    []
  );

  const renderRotationControls = useCallback(
    (rotation, rotationAction, label) => {
      const handleXChange = (e) => {
        const value = parseInt(e.target.value);
        const finalValue = isNaN(value) ? 0 : value;
        console.log(`🎛️ ${label} X Rotation changed:`, {
          old: rotation.x,
          new: finalValue,
        });
        dispatch(rotationAction({ ...rotation, x: finalValue }));
      };

      const handleYChange = (e) => {
        const value = parseInt(e.target.value);
        const finalValue = isNaN(value) ? 0 : value;
        console.log(`🎛️ ${label} Y Rotation changed:`, {
          old: rotation.y,
          new: finalValue,
        });
        dispatch(rotationAction({ ...rotation, y: finalValue }));
      };

      const handleZChange = (e) => {
        const value = parseInt(e.target.value);
        const finalValue = isNaN(value) ? 0 : value;
        console.log(`🎛️ ${label} Z Rotation changed:`, {
          old: rotation.z,
          new: finalValue,
        });
        dispatch(rotationAction({ ...rotation, z: finalValue }));
      };

      return (
        <div className="space-y-3">
          <h3 className="text-white font-medium text-sm">{t(label)} {t("Rotation")}</h3>

          {/* Compact grid layout for X, Y, Z */}
          <div className="grid grid-cols-3 gap-2">
            {/* X Rotation */}
            <div>
              <label className="block text-white/70 text-xs mb-1">X°</label>
              <input
                type="number"
                min="-180"
                max="180"
                step="1"
                value={rotation.x}
                onChange={handleXChange}
                className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded text-white text-sm focus:outline-none number-input"
              />
            </div>

            {/* Y Rotation */}
            <div>
              <label className="block text-white/70 text-xs mb-1">Y°</label>
              <input
                type="number"
                min="-180"
                max="180"
                step="1"
                value={rotation.y}
                onChange={handleYChange}
                className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded text-white text-sm focus:outline-none number-input"
              />
            </div>

            {/* Z Rotation */}
            <div>
              <label className="block text-white/70 text-xs mb-1">Z°</label>
              <input
                type="number"
                min="-180"
                max="180"
                step="1"
                value={rotation.z}
                onChange={handleZChange}
                className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded text-white text-sm focus:outline-none number-input"
              />
            </div>
          </div>
        </div>
      );
    },
    [t, dispatch]
  );

  const renderScaleControl = useCallback((scale, scaleAction, label) => {
    const isPinMode = label === "Pin";

    const handleScaleChange = (e) => {
      const value = parseFloat(e.target.value);
      // For scale, default to 1 if NaN, and ensure minimum value
      const finalValue = isNaN(value)
        ? isPinMode
          ? 0
          : 1
        : isPinMode
        ? value
        : Math.max(0.1, value);
      console.log(`🎛️ ${label} Scale changed:`, {
        old: scale,
        new: finalValue,
      });
      dispatch(scaleAction(finalValue));
    };

    return (
      <div className="space-y-3">
        <h3 className="text-white font-medium text-sm">{t(label)} {t("Scale")}</h3>
        <div>
          <label className="block text-white/70 text-xs mb-1">{t("Size")}</label>
          <input
            type="number"
            min="0.1"
            max={isPinMode ? "5" : "3"} // Higher max for pin mode
            step="0.1"
            value={scale.toFixed(1)}
            onChange={handleScaleChange}
            className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded text-white text-sm focus:outline-none number-input"
          />
        </div>
      </div>
    );
  }, [t, dispatch]);

  return (
    <div className="h-full flex flex-col min-h-0">
      {/* Settings Card with Scrollbar */}
      <div className="bg-white/5 backdrop-blur-sm rounded-xl border border-white/10 flex-1 flex flex-col min-h-0 overflow-hidden">
        {/* Fixed Header Section */}
        <div className="p-4 pb-0 flex-shrink-0">
          <h2 className="text-lg font-semibold text-white mb-4">
            {t("Avatar Settings")}
          </h2>
        </div>

        {/* Scrollable Content Section */}
        <div className="flex-1 overflow-y-auto px-4 pb-4 space-y-4 avatar-settings-scroll min-h-0">
          {/* Only Pin Mode controls now */}
          <>
              {/* Pin Mode Toggle */}
              <div className="px-4 py-3 bg-black/20 rounded-lg border border-white/10">
                <div className="flex items-center justify-between">
                  <h3 className="text-white font-medium">{t("Pin Mode")}</h3>
                  <button
                    onClick={handlePinModeToggle}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      isPinModeEnabled ? "bg-orange-500" : "bg-white/20"
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        isPinModeEnabled ? "translate-x-6" : "translate-x-1"
                      }`}
                    />
                  </button>
                </div>
              </div>

              {/* Conditional controls based on avatar type */}
              {selectedAvatar?.mediaType === 'image' ? (
                <ImageAvatarSettings
                  pinPosition={pinPosition}
                  pinRotation={pinRotation}
                  pinScale={pinScale}
                  dispatch={dispatch}
                  setPinPosition={setPinPosition}
                  setPinRotation={setPinRotation}
                  setPinScale={setPinScale}
                />
              ) : (
                <>
                  {renderPositionControls(pinPosition, setPinPosition, "Pin")}
                  {renderRotationControls(pinRotation, setPinRotation, "Pin")}
                  {renderScaleControl(pinScale, setPinScale, "Pin")}
                </>
              )}

              {/* Pin Mode Save Button removed - use footer save button instead */}

              {/* Additional Pin Mode Settings Info - only for 3D models */}
              {selectedAvatar?.mediaType !== 'image' && (
                <div className="p-3 bg-black/10 rounded-lg border border-white/5">
                  <h4 className="text-white/80 text-xs font-medium mb-2">
                    {t("3D Avatar Tips")}
                  </h4>
                  <ul className="text-white/60 text-xs space-y-1">
                    <li>• {t("Position: Adjust 3D position in space")}</li>
                    <li>• {t("Rotation: Change avatar orientation")}</li>
                    <li>• {t("Scale: Modify size (added to base scale)")}</li>
                    <li>• {t("Drag avatar to move around screen")}</li>
                    <li>• {t("Use scroll wheel to navigate settings")}</li>
                  </ul>
                </div>
              )}
          </>
        </div>

        {/* Fixed Footer Section */}
        <div className="p-4 pt-0 flex-shrink-0 border-t border-white/5">
          {/* Action Buttons */}
          <div className="space-y-2">
            {/* Manual Save Button */}
            <button
              onClick={handleSavePosition}
              className={`w-full px-3 py-2 rounded-lg border transition-all font-medium text-sm ${
                hasUnsavedChanges
                  ? "bg-orange-500/20 text-orange-400 border-orange-500/30 hover:bg-orange-500/30 hover:text-orange-300 animate-pulse"
                  : "bg-green-500/20 text-green-400 border-green-500/30 hover:bg-green-500/30 hover:text-green-300"
              }`}
            >
              {hasUnsavedChanges ? t("⚠️ Save Now") : t("✅ Saved & Synced")}
            </button>

            {/* Reset Buttons */}
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => {
                  // Reset to appropriate defaults based on avatar type
                  if (selectedAvatar?.mediaType === 'image') {
                    // Image avatar defaults
                    dispatch(setPinPosition({ x: 0, y: 0, z: 0 }));
                    dispatch(setPinRotation({ x: 0, y: 0, z: 0 }));
                    dispatch(setPinScale(2.0));
                  } else {
                    // 3D model defaults
                    dispatch(setPinPosition({ x: 0, y: -4.0, z: 0 }));
                    dispatch(setPinRotation({ x: 0, y: 180, z: 0 }));
                    dispatch(setPinScale(2.5));
                  }
                }}
                className="px-3 py-2 bg-white/10 text-white/70 rounded-lg border border-white/20 hover:bg-white/20 hover:text-white transition-all text-xs"
              >
                {t("Reset")} {selectedAvatar?.mediaType === 'image' ? t('Image') : t('Pin')}
              </button>

              <button
                onClick={resetPinnedAvatar}
                className="px-3 py-2 bg-red-500/20 text-red-400 rounded-lg border border-red-500/30 hover:bg-red-500/30 hover:text-red-300 transition-all text-xs"
              >
                {t("Reset All")}
              </button>
            </div>

            {/* Last Saved Indicator */}
            {selectedAvatar?.lastUpdated && (
              <div className="text-white/40 text-xs pt-2">
                {t("Last saved")}:{" "}
                {new Date(selectedAvatar.lastUpdated).toLocaleString()}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
