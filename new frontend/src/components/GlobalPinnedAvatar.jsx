import React, { useCallback, useEffect } from "react";
import { useSelector, useDispatch } from "react-redux";
import { useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { createPortal } from "react-dom";

import MediaViewer from "./MediaViewer";
import AvatarChatInterface from "./AvatarChatInterface";
import { storage } from "../utils/storageUtils";
import {
  selectSelectedAvatar,
  selectFavorites,
  selectIsPinModeEnabled,
  selectPinnedAvatarPosition,
  selectIsDragging,
  selectDragOffset,
  selectPinPosition,
  selectPinRotation,
  selectPinScale,
  selectActiveSettingsTab,
  selectActiveMainTab,
  selectIsChatOpen,
  selectIsSpeaking,
  setPinnedAvatarPosition,
  setIsDragging,
  setDragOffset,
  setIsChatOpen,
  setSelectedAvatar,
  loadAvatarSettings,
  updateFavorite,
  autoSaveAvatarSettings,
} from "../store/avatarSlice";
import { selectIsAuthenticated } from "../store/authSlice";

/**
 * GlobalPinnedAvatar - Renders the pinned avatar that floats across all authenticated pages
 * Only visible when pin mode is enabled and user is authenticated
 */
export default function GlobalPinnedAvatar() {
  const { t } = useTranslation();
  const dispatch = useDispatch();
  const location = useLocation();

  // Redux state
  const isAuthenticated = useSelector(selectIsAuthenticated);
  const selectedAvatar = useSelector(selectSelectedAvatar);
  const favorites = useSelector(selectFavorites);
  const isPinModeEnabled = useSelector(selectIsPinModeEnabled);
  const pinnedAvatarPosition = useSelector(selectPinnedAvatarPosition);
  const isDragging = useSelector(selectIsDragging);
  const dragOffset = useSelector(selectDragOffset);
  const pinPosition = useSelector(selectPinPosition);
  const pinRotation = useSelector(selectPinRotation);
  const pinScale = useSelector(selectPinScale);
  const activeSettingsTab = useSelector(selectActiveSettingsTab);
  const activeMainTab = useSelector(selectActiveMainTab);
  const isChatOpen = useSelector(selectIsChatOpen);
  const isSpeaking = useSelector(selectIsSpeaking);

  // Check if we're on avatar-selection page
  const isOnAvatarSelectionPage = location.pathname === "/avatar-selection";

  // Check if we're on avatar-selection page with favorites main tab and pin settings tab active
  const isOnAvatarSelectionPinTab =
    isOnAvatarSelectionPage &&
    activeMainTab === "favorites" &&
    activeSettingsTab === "pin";

  // Check if we're on avatar-selection page with favorites main tab and grid settings tab active
  const isOnAvatarSelectionGridTab =
    isOnAvatarSelectionPage &&
    activeMainTab === "favorites" &&
    activeSettingsTab === "grid";

  // Check if we're on mobile (window width <= 767px)
  const isMobile = typeof window !== 'undefined' && window.innerWidth <= 767;

  // Simplified logic: Show floating pinned avatar when:
  // - User is authenticated
  // - Pin mode is enabled
  // - We have an avatar to show (selected or fallback)
  // - We're NOT on the avatar-selection page with pin settings tab (to avoid duplication)
  // - We're NOT on mobile (avatar now shows in mobile navbar)
  const shouldShowPinnedAvatar =
    isAuthenticated &&
    isPinModeEnabled &&
    !isOnAvatarSelectionPinTab && // Only hide when on pin settings tab to avoid duplication
    !isMobile; // Hide on mobile since avatar is now in mobile navbar

  // Show contained avatar when on Pin Mode tab (inside grid card)
  const shouldShowContainedAvatar =
    isAuthenticated &&
    isPinModeEnabled &&
    isOnAvatarSelectionPinTab;

  // Recovery mechanism: if pin mode is enabled but no avatar is selected, try to select the first favorite or use jupiter fallback
  useEffect(() => {
    if (isAuthenticated && isPinModeEnabled && !selectedAvatar) {
      if (favorites.length > 0) {
        // Look for jupiter first, then fallback to first favorite
        const jupiterFavorite = favorites.find(fav => fav.previewUrl?.includes('jupiter.glb'));
        const avatarToSelect = jupiterFavorite || favorites[0];
        dispatch(setSelectedAvatar(avatarToSelect));
        dispatch(loadAvatarSettings(avatarToSelect));
      } else {
        // Create a jupiter fallback avatar object (jupiter.glb as primary default)
        const jupiterFallbackAvatar = {
          id: "jupiter-fallback-avatar",
          name: "Brihaspati",
          isDefault: true,
          isPrimaryDefault: true,
          previewUrl: "/avatar/jupiter.glb",
          mediaType: "3d", // Explicitly set as 3D model
          timestamp: new Date().toISOString(),
          gridPosition: { x: 0, y: 0, z: 0 },
          gridRotation: { x: 0, y: 180, z: 0 },
          gridScale: 1,
          pinPosition: { x: 0, y: 0.5, z: -4.0 }, // Perfect position for jupiter
          pinRotation: { x: 0, y: 180, z: 0 },
          pinScale: 0.6, // Perfect scale for jupiter
          isPinModeEnabled: true,
          pinnedAvatarPosition: { x: 100, y: 100 }
        };
        dispatch(setSelectedAvatar(jupiterFallbackAvatar));
        dispatch(loadAvatarSettings(jupiterFallbackAvatar));
      }
    }
  }, [isAuthenticated, isPinModeEnabled, selectedAvatar, favorites, dispatch]);

  // Double-click handler for chat activation
  const handleDoubleClick = (e) => {
    if (!isPinModeEnabled) return;

    e.preventDefault();
    e.stopPropagation();
    dispatch(setIsChatOpen(!isChatOpen));
  };

  // Enhanced drag functionality with bounds checking
  const handleMouseDown = (e) => {
    if (!isPinModeEnabled) return;
    if (shouldShowContainedAvatar) return;

    const container = e.currentTarget;
    const rect = container.getBoundingClientRect();

    dispatch(setIsDragging(true));
    dispatch(
      setDragOffset({
        x: e.clientX - rect.left,
        y: e.clientY - rect.top,
      })
    );

    // Add grabbing cursor
    container.style.cursor = "grabbing";
    document.body.style.userSelect = "none";

    e.preventDefault();
  };

  const handleMouseMove = useCallback(
    (e) => {
      if (!isDragging || !isPinModeEnabled || shouldShowContainedAvatar) return;

      // Get viewport dimensions
      const viewportWidth = window.innerWidth;
      const viewportHeight = window.innerHeight;

      // Calculate new position with bounds checking
      const newX = Math.max(
        0,
        Math.min(e.clientX - dragOffset.x, viewportWidth - 220)
      );
      const newY = Math.max(
        0,
        Math.min(e.clientY - dragOffset.y, viewportHeight - 220)
      );

      const newPosition = { x: newX, y: newY };
      dispatch(setPinnedAvatarPosition(newPosition));

      // Auto-save position with debouncing
      if (selectedAvatar) {
        const updatedAvatar = {
          ...selectedAvatar,
          pinnedAvatarPosition: newPosition,
          lastUpdated: new Date().toISOString(),
        };

        dispatch(
          updateFavorite({ id: selectedAvatar.id, updates: updatedAvatar })
        );

        // Save to storage
        try {
          const updatedFavorites = favorites.map((fav) =>
            fav.id === selectedAvatar.id ? updatedAvatar : fav
          );
          storage.setItem(
            "gurukul_favorite_avatars",
            JSON.stringify(updatedFavorites)
          );
        } catch (error) {
          console.error("Error saving pin position:", error);
        }
      }
    },
    [
      isDragging,
      isPinModeEnabled,
      shouldShowContainedAvatar,
      dragOffset,
      selectedAvatar,
      favorites,
      dispatch,
    ]
  );

  const handleMouseUp = useCallback(() => {
    dispatch(setIsDragging(false));

    // Reset cursor and user selection
    document.body.style.cursor = "";
    document.body.style.userSelect = "";

    // Snap to nearest valid position if needed
    if (selectedAvatar && pinnedAvatarPosition) {
      const viewportWidth = window.innerWidth;
      const viewportHeight = window.innerHeight;

      const snappedPosition = {
        x: Math.max(0, Math.min(pinnedAvatarPosition.x, viewportWidth - 220)),
        y: Math.max(0, Math.min(pinnedAvatarPosition.y, viewportHeight - 220)),
      };

      if (
        snappedPosition.x !== pinnedAvatarPosition.x ||
        snappedPosition.y !== pinnedAvatarPosition.y
      ) {
        dispatch(setPinnedAvatarPosition(snappedPosition));
      }
    }
  }, [dispatch, selectedAvatar, pinnedAvatarPosition]);

  // Add global mouse event listeners for dragging
  useEffect(() => {
    if (isDragging) {
      document.addEventListener("mousemove", handleMouseMove);
      document.addEventListener("mouseup", handleMouseUp);

      return () => {
        document.removeEventListener("mousemove", handleMouseMove);
        document.removeEventListener("mouseup", handleMouseUp);
      };
    }
  }, [isDragging, handleMouseMove, handleMouseUp]);

  // Add animation styles
  useEffect(() => {
    const style = document.createElement("style");
    style.textContent = `
      @keyframes divine-pulse {
        0% {
          opacity: 0.3;
          transform: scale(1.0);
        }
        50% {
          opacity: 0.6;
          transform: scale(1.1);
        }
        100% {
          opacity: 0.4;
          transform: scale(1.05);
        }
      }

      /* Removed float animation to prevent up/down movement */
    `;
    document.head.appendChild(style);

    return () => {
      document.head.removeChild(style);
    };
  }, []);



  // Don't show anything if pin mode is disabled or user is not authenticated
  if (!isPinModeEnabled || !isAuthenticated) {
    return null;
  }

  // Don't show if neither floating nor contained should show
  if (!shouldShowPinnedAvatar && !shouldShowContainedAvatar) {
    return null;
  }

  // Determine which avatar to render - prioritize selected avatar, then first favorite, then create fallback
  let avatarToRender = selectedAvatar;

  if (!avatarToRender && favorites.length > 0) {
    avatarToRender = favorites[0];
  }

  if (!avatarToRender) {
    // Create a temporary jupiter fallback avatar for rendering
    avatarToRender = {
      id: "temp-jupiter-fallback",
      name: "Brihaspati",
      isDefault: true,
      isPrimaryDefault: true,
      previewUrl: "/avatar/jupiter.glb",
      mediaType: "3d", // Explicitly set as 3D model
      gridPosition: { x: 0, y: 0, z: 0 },
      gridRotation: { x: 0, y: 180, z: 0 },
      gridScale: 1,
      pinPosition: { x: 0, y: 0.5, z: -4.0 }, // Perfect position for jupiter
      pinRotation: { x: 0, y: 180, z: 0 },
      pinScale: 0.6 // Perfect scale for jupiter
    };
  }

  // Determine avatar path - handle all avatar types properly
  let avatarPath = "/avatar/jupiter.glb"; // Default to jupiter



  // Priority order: custom media data > previewUrl > aiModel.url > fallback
  if (avatarToRender.isCustomModel) {
    // Custom media (model or image): use previewUrl or fileData
    if (avatarToRender.previewUrl) {
      avatarPath = avatarToRender.previewUrl;
    } else if (avatarToRender.fileData) {
      // If we have fileData but no previewUrl
      if (avatarToRender.mediaType === 'image') {
        // For images, use the base64 data directly
        avatarPath = avatarToRender.fileData;
      } else {
        // For 3D models, create blob URL
        try {
          const base64Data = avatarToRender.fileData.split(",")[1];
          const binaryString = atob(base64Data);
          const bytes = new Uint8Array(binaryString.length);
          for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
          }
          const blob = new Blob([bytes], { type: "application/octet-stream" });
          avatarPath = URL.createObjectURL(blob);
        } catch (error) {
          console.error("🎭 Error creating blob URL for custom model:", error);
          avatarPath = "/avatar/jupiter.glb";
        }
      }
    }
  } else if (avatarToRender.isDefault ||
             avatarToRender.previewUrl === "/avatar/jupiter.glb") {
    // Default avatar - use the specified default GLB file
    avatarPath = avatarToRender.previewUrl || "/avatar/jupiter.glb";
  } else if (avatarToRender.previewUrl && avatarToRender.previewUrl.endsWith(".glb")) {
    // Generated avatar with direct GLB URL
    avatarPath = avatarToRender.previewUrl;
  } else if (avatarToRender.aiModel?.url && avatarToRender.aiModel.url.endsWith(".glb")) {
    // AI generated model
    avatarPath = avatarToRender.aiModel.url;
  }



  // Find the target container for contained mode (when on Pin Mode tab)
  const targetContainer = shouldShowContainedAvatar
    ? document.querySelector("[data-avatar-selection-pin-preview]")
    : null;



  const avatarElement = (
    <div
      data-avatar-container
      className={
        shouldShowContainedAvatar ? "absolute cursor-move" : "fixed cursor-move"
      }
      style={
        shouldShowContainedAvatar
          ? {
              // Contained mode - fill the container completely
              position: "absolute",
              inset: "0",
              zIndex: 10,
              width: "100%",
              height: "100%",
              pointerEvents: "auto",
            }
          : {
              // Floating mode - with smooth transitions
              left: `${pinnedAvatarPosition.x}px`,
              top: `${pinnedAvatarPosition.y}px`,
              zIndex: 9999,
              width: "220px",
              height: "220px",
              transition: isDragging ? "none" : "all 0.3s ease-out",
              willChange: "transform, left, top",
              filter: "drop-shadow(0 4px 8px rgba(0,0,0,0.2))",
            }
      }
      onMouseDown={handleMouseDown}
      onDoubleClick={handleDoubleClick}
      title={
        shouldShowContainedAvatar
          ? t("Avatar contained in Pin Mode")
          : t("Drag to move • Double-click to chat")
      }
    >
      {/* Godlike glow effect behind the avatar */}
      <div
        className="absolute inset-0 rounded-full"
        style={{
          background: `
            radial-gradient(circle at center, 
              rgba(255, 215, 0, 0.4) 0%, 
              rgba(255, 165, 0, 0.3) 20%, 
              rgba(255, 140, 0, 0.2) 40%, 
              rgba(255, 69, 0, 0.1) 60%, 
              transparent 80%
            )
          `,
          filter: "blur(8px)",
          animation: "divine-pulse 3s ease-in-out infinite",
          transform: "scale(0.9)", // Keep glow closer to avatar dimensions
        }}
      />

      {/* Avatar container */}
      <div
        className="relative w-full h-full"
        style={{ backgroundColor: "transparent" }}
      >

        <MediaViewer
          key={`pinned-${avatarToRender?.id || "jupiter"}-${
            isPinModeEnabled ? "enabled" : "disabled"
          }-${avatarPath}`}
          mediaPath={avatarPath}
          mediaType={avatarToRender?.mediaType}
          isFloatingAvatar={true} // This is a floating/pinned avatar
          fallbackPath="/avatar/jupiter.glb"
          enableControls={false}
          autoRotate={avatarPath.includes('jupiter.glb') ? true : !isDragging} // Always rotate jupiter, stop others while dragging
          autoRotateSpeed={avatarPath.includes('jupiter.glb') ? 2.0 : 0.3} // 4x faster for jupiter
          showEnvironment={true}
          environmentPreset="sunset"
          fallbackMessage="Brihaspati"
          className="w-full h-full"
          isSpeaking={isSpeaking}
          position={[
            (pinPosition?.x || 0), // Use pin position X
            (pinPosition?.y || 0), // Use pin position Y
            (pinPosition?.z || 0), // Use pin position Z
          ]}
          onLoadStart={() => {}}
          onLoad={() => {}}
          onError={(error) => {
            console.error("🎭 Pin Mode Avatar: Load error for", avatarPath, error);

            // If this is already the default and it's failing, show a simple error
            if (avatarPath === "/avatar/jupiter.glb") {
              console.error("🎭 Even jupiter.glb failed to load! This indicates a serious issue.");
            }
          }}
          rotation={[
            ((pinRotation?.x || 0) * Math.PI) / 180, // Use pin rotation X
            ((pinRotation?.y || 180) * Math.PI) / 180, // Use pin rotation Y (face forward by default)
            ((pinRotation?.z || 0) * Math.PI) / 180, // Use pin rotation Z
          ]}
          scale={pinScale || 2.5} // Use pin scale setting
          style="realistic"
          enableInteraction={false}
          enableAnimations={avatarPath.includes('jupiter.glb')} // Enable animations for jupiter.glb
          cameraPosition={[0, 0, 1.5]} // Keep the same camera position that was working
          fov={50} // Better field of view for pin mode
          lights={[
            { type: "ambient", intensity: 1.0 },
            { type: "directional", position: [5, 5, 5], intensity: 1.2 },
            { type: "directional", position: [-5, 5, -5], intensity: 0.8 },
            { type: "point", position: [0, 2, 5], intensity: 0.8 },
          ]}
        />
      </div>
    </div>
  );

  return (
    <>
      {/* Render floating avatar when not on avatar-selection page */}
      {shouldShowPinnedAvatar && avatarElement}

      {/* Render contained avatar using portal when on Pin Mode tab */}
      {shouldShowContainedAvatar &&
        targetContainer &&
        createPortal(avatarElement, targetContainer)}

      {/* Avatar Chat Interface - only show when floating (not contained) */}
      {shouldShowPinnedAvatar && (
        <AvatarChatInterface avatarPosition={pinnedAvatarPosition} />
      )}
    </>
  );
}
