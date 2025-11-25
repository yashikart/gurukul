import React from "react";
import { useAuth } from "../hooks/useAuth";
import { useUser } from "@clerk/clerk-react";

export default function AuthStatus() {
  const { user, isAuthenticated, isClerkEnabled } = useAuth();
  const { user: clerkUser, isLoaded, isSignedIn } = useUser();

  // Only show in development
  if (import.meta.env.PROD) return null;

  return (
    <div className="fixed bottom-4 left-4 bg-black/80 text-white p-3 rounded-lg text-xs max-w-xs z-50">
      <div className="font-semibold mb-2">Auth Debug Info:</div>
      <div>Clerk Enabled: {isClerkEnabled ? "Yes" : "No"}</div>
      <div>Is Loaded: {isLoaded ? "Yes" : "No"}</div>
      <div>Is Signed In: {isSignedIn ? "Yes" : "No"}</div>
      <div>Is Authenticated: {isAuthenticated ? "Yes" : "No"}</div>
      <div>User ID: {user?.id || "None"}</div>
      <div>User Email: {user?.email || clerkUser?.primaryEmailAddress?.emailAddress || "None"}</div>
    </div>
  );
}