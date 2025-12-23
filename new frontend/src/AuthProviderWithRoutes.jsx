import React from "react";
import { useNavigate } from "react-router-dom";

export function AuthProviderWithRoutes({ children }) {
  const navigate = useNavigate();
  
  // Simple wrapper that just returns children since we're using our own AuthContext
  return <>{children}</>;
}