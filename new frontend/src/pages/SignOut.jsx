import React, { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { supabase } from "../supabaseClient";
import { useDispatch } from "react-redux";
import { clearUser } from "../store/authSlice";

export default function SignOut() {
  const navigate = useNavigate();
  const dispatch = useDispatch();

  useEffect(() => {
    const signOutUser = async () => {
      try {
        // Sign out from Supabase
        await supabase.auth.signOut();
        
        // Clear user from Redux store
        dispatch(clearUser());
        
        // Redirect to sign in page
        navigate("/signin");
      } catch (error) {
        console.error("Error signing out:", error);
        // Even if there's an error, still redirect to sign in
        navigate("/signin");
      }
    };

    signOutUser();
  }, [navigate, dispatch]);

  return (
    <div className="min-h-screen w-full flex items-center justify-center">
      <div className="text-white text-xl">Signing out...</div>
    </div>
  );
}