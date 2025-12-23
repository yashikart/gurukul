import React, { useEffect, useState } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { toast } from "react-hot-toast";
import { getLastVisitedPath } from "../utils/routeUtils";

// Simple loading component to avoid circular dependencies
function SimpleLoadingScreen() {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Background blur layer */}
      <div className="absolute inset-0 backdrop-blur-xl bg-gradient-to-b from-[#1a1a2e]/70 to-[#16213e]/70"></div>

      {/* Glass card container */}
      <div className="relative z-10 px-10 py-8 rounded-2xl backdrop-blur-md bg-white/10 border border-white/20 shadow-[0_8px_32px_rgba(0,0,0,0.2)] flex flex-col items-center">
        {/* Fancy loader animation */}
        <div className="relative w-16 h-16 mb-5">
          {/* Outer spinning ring */}
          <div className="absolute inset-0 rounded-full border-2 border-transparent border-t-orange-500 border-r-orange-500/50 animate-spin"></div>

          {/* Middle spinning ring (opposite direction) */}
          <div className="absolute inset-1 rounded-full border-2 border-transparent border-b-orange-400 border-l-orange-400/50 animate-[spin_1s_linear_infinite_reverse]"></div>

          {/* Inner pulsing circle */}
          <div className="absolute inset-3 rounded-full bg-gradient-to-tr from-orange-500/20 to-orange-300/20 animate-pulse"></div>

          {/* Center dot */}
          <div className="absolute inset-[40%] rounded-full bg-orange-400"></div>
        </div>

        {/* Message with glow effect */}
        <p className="text-white text-lg font-medium tracking-wide drop-shadow-[0_0_8px_rgba(255,255,255,0.3)]">
          Loading...
        </p>

        {/* Subtle animated line */}
        <div className="w-32 h-0.5 mt-4 bg-gradient-to-r from-transparent via-orange-500/50 to-transparent relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent animate-shimmer"></div>
        </div>
      </div>
    </div>
  );
}

export default function PublicRoute({ children }) {
  const { user, loading } = useAuth();
  const [hasVisited, setHasVisited] = useState(false);
  const location = useLocation();

  useEffect(() => {
    // Check if user has visited before
    const visited = localStorage.getItem("gurukul_visited") === "true";
    setHasVisited(visited);
  }, []);

  // Show loading screen while checking auth status
  if (loading) {
    return <SimpleLoadingScreen />;
  }

  // If user is authenticated, redirect to dashboard
  if (user) {
    return <Navigate to={getLastVisitedPath()} replace />;
  }

  // If user is not authenticated, show children (public pages)
  return (
    <>
      {/* Mark as visited when showing the GetStarted page */}
      {(() => {
        if (!hasVisited) {
          localStorage.setItem("gurukul_visited", "true");
        }
        return children;
      })()}
    </>
  );
}