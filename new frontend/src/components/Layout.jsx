import React, { useState, useEffect } from "react";
import { useLocation } from "react-router-dom";
import Header from "./Header";
import Sidebar from "./Sidebar";
import SideBarAltUse from "./SideBarAltUse";
import MobileBottomNavigation from "./MobileBottomNavigation";
import PageLoader from "./PageLoader";
import { LoaderProvider, useLoader } from "../context/LoaderContext";
import { VideoProvider, useVideo } from "../context/VideoContext";
import { useTimeTracking } from "../hooks/useTimeTracking";
import { useAvatarPersistence } from "../hooks/useAvatarPersistence";
import SessionTracker from "./SessionTracker";
import GlobalPinnedAvatar from "./GlobalPinnedAvatar";

import { saveCurrentPath } from "../utils/routeUtils";

function LayoutContent({ children }) {
  const { show } = useLoader();
  const { handleTimeUpdate } = useTimeTracking();
  const { generatedVideo, showVideoInSidebar, hideVideo } = useVideo();
  const location = useLocation();
  const isHome = location.pathname === "/" || location.pathname === "/home";
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  // Initialize avatar persistence for global state management
  useAvatarPersistence();

  // Save the current path whenever the location changes
  useEffect(() => {
    saveCurrentPath();
  }, [location.pathname]);

  // Collapse sidebar on small screens and expand on larger screens
  // On mobile, we'll use the bottom navigation instead
  useEffect(() => {
    const handleResize = () => {
      const isSmall = window.innerWidth < 768; // md breakpoint
      setSidebarCollapsed(isSmall);
    };
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return (
    <>
      {show && <PageLoader />}

      {/* Main Layout Container with PNG background */}
      <div
        className="min-h-screen flex flex-col overflow-x-hidden relative"
        style={{
          backgroundImage: 'url(/bg/bg.png)',
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundRepeat: 'no-repeat',
          backgroundAttachment: 'scroll'
        }}
      >
        {/* Session Tracker - Always active when user is logged in */}
        <SessionTracker onTimeUpdate={handleTimeUpdate} />

        {/* Content wrapper with proper z-index */}
        <div className="relative z-10 flex flex-col h-full">
          <Header
            onToggleSidebar={() => setSidebarCollapsed(!sidebarCollapsed)}
            sidebarCollapsed={sidebarCollapsed}
          />

          {/* Main area with sidebar and content */}
          <div
            className={`flex flex-1 ${
              isHome ? "h-auto md:h-full" : "h-auto md:h-[calc(100dvh-70px)]"
            } md:overflow-hidden overflow-y-auto p-2`}
          >
            {/* Desktop Sidebar - toggleable width (hidden on home and mobile) */}
            {!isHome && !sidebarCollapsed && (
              <div className="hidden md:block transition-all duration-300 ease-in-out flex-shrink-0 w-[240px] h-auto">
                {showVideoInSidebar ? (
                  <SideBarAltUse
                    generatedVideo={generatedVideo}
                    isVisible={showVideoInSidebar}
                    onClose={hideVideo}
                  />
                ) : (
                  <Sidebar
                    collapsed={false}
                    onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
                  />
                )}
              </div>
            )}
            {/* Main Content Area */}
            <div
              className={`flex-1 md:overflow-hidden overflow-y-auto ${
                sidebarCollapsed ? "w-full px-0 py-2" : "md:p-2 p-0"
              }`}
              style={{ paddingTop: isHome ? "0px" : "90px" }}
            >
              <div className="w-full h-full main-content">{children}</div>
            </div>
          </div>
        </div>

        {/* Global Pinned Avatar - Floats across all authenticated pages */}
        <GlobalPinnedAvatar />

        {/* Mobile Bottom Navigation - Only show on mobile when not on home */}
        {!isHome && (
          <MobileBottomNavigation />
        )}


      </div>
    </>
  );
}

export default function Layout({ children }) {
  return (
    <LoaderProvider>
      <VideoProvider>
        <LayoutContent>{children}</LayoutContent>
      </VideoProvider>
    </LoaderProvider>
  );
}
