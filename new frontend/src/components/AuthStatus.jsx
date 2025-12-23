import React from "react";
import { useAuth } from "../context/AuthContext";

export default function AuthStatus() {
  const { user, loading } = useAuth();

  // Only show in development
  if (import.meta.env.PROD) return null;

  return (
    <div className="fixed bottom-4 left-4 bg-black/80 text-white p-3 rounded-lg text-xs max-w-xs z-50">
      <div className="font-semibold mb-2">Auth Debug Info:</div>
      <div>Loading: {loading ? "Yes" : "No"}</div>
      <div>Is Authenticated: {user ? "Yes" : "No"}</div>
      <div>User ID: {user?.id || "None"}</div>
      <div>User Email: {user?.email || "None"}</div>
    </div>
  );
}