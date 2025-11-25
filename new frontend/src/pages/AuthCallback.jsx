import React, { useEffect, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { toast } from "react-hot-toast";
import { getLastVisitedPath } from "../utils/routeUtils";
import { useClerk } from "@clerk/clerk-react";

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
          Completing Sign In...
        </p>

        {/* Subtle animated line */}
        <div className="w-32 h-0.5 mt-4 bg-gradient-to-r from-transparent via-orange-500/50 to-transparent relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent animate-shimmer"></div>
        </div>
      </div>
    </div>
  );
}

export default function AuthCallback() {
  const [status, setStatus] = useState("processing"); // "processing", "success", "error"
  const [redirectPath, setRedirectPath] = useState("/home");
  const navigate = useNavigate();
  const { handleRedirectCallback } = useClerk();

  useEffect(() => {
    // Set a hard timeout to prevent infinite loading
    const hardTimeoutId = setTimeout(() => {
      console.log(
        "Hard timeout reached in AuthCallback, redirecting to sign in"
      );
      setStatus("error");
    }, 8000);

    // Handle the OAuth callback
    const handleAuthCallback = async () => {
      try {
        await handleRedirectCallback();
        const path = getLastVisitedPath();
        setRedirectPath(path);
        setStatus("success");
        toast.success("Logged in successfully!", {
          position: "bottom-right",
          id: "auth-success",
        });
      } catch (err) {
        console.error("Error in auth callback:", err);
        setStatus("error");
        toast.error("Authentication failed. Please try again.", {
          position: "bottom-right",
        });
      } finally {
        clearTimeout(hardTimeoutId);
      }
    };

    // Run the auth callback handler
    handleAuthCallback();

    // Clean up
    return () => {
      clearTimeout(hardTimeoutId);
    };
  }, []);

  // Handle different states
  switch (status) {
    case "processing":
      return <SimpleLoadingScreen />;
    case "success":
      return <Navigate to={redirectPath} replace />;
    case "error":
      return <Navigate to="/signin" replace />;
    default:
      return <Navigate to="/signin" replace />;
  }
}
