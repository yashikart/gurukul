import { useSelector, useDispatch } from "react-redux";
import { useCallback } from "react";
import {
  selectUser,
  selectAuthStatus,
  selectAuthError,
  selectIsAuthenticated,
  signIn as reduxSignIn,
  signOut as reduxSignOut,
  fetchCurrentUser,
} from "../store/authSlice";
import { toast } from "react-hot-toast";
import { supabase } from "../supabaseClient";

/**
 * Custom hook for authentication
 * Provides access to auth state and methods
 */
export const useAuth = () => {
  const dispatch = useDispatch();
  const user = useSelector(selectUser);
  const status = useSelector(selectAuthStatus);
  const error = useSelector(selectAuthError);
  const isAuthenticated = useSelector(selectIsAuthenticated);

  /**
   * Sign in with email and password
   */
  const login = useCallback(
    async (email, password) => {
      try {
        const { data, error } = await supabase.auth.signInWithPassword({
          email,
          password,
        });

        if (error) throw error;

        // Update Redux store with user data
        dispatch(
          reduxSignIn({
            id: data.user.id,
            email: data.user.email,
            user_metadata: {
              avatar_url: data.user.user_metadata?.avatar_url || null,
              full_name: data.user.user_metadata?.full_name || data.user.email || null,
            },
          })
        );

        toast.success("Signed in successfully", { id: "auth-success" });
        return { success: true };
      } catch (error) {
        const msg = error.message || "Failed to sign in";
        toast.error(msg);
        return { success: false, error: msg };
      }
    },
    [dispatch]
  );

  /**
   * Sign out the current user
   */
  const logout = useCallback(async () => {
    try {
      const { error } = await supabase.auth.signOut();
      
      if (error) throw error;
      
      dispatch(reduxSignOut());
      toast.success("Signed out successfully");
      return { success: true };
    } catch (error) {
      const msg = error.message || "Failed to sign out";
      toast.error(msg);
      return { success: false, error: msg };
    }
  }, [dispatch]);

  /**
   * Sign up with email and password
   */
  const signup = useCallback(async (email, password) => {
    try {
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          emailRedirectTo: window.location.origin + "/verify-email",
        },
      });

      if (error) throw error;

      toast.success("Signed up successfully! Check your email for verification.");
      return { success: true };
    } catch (error) {
      const msg = error.message || "Sign up failed";
      toast.error(msg);
      return { success: false, error: msg };
    }
  }, []);

  /**
   * Reset password
   */
  const resetPassword = useCallback(async (email) => {
    try {
      const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: window.location.origin + "/update-password",
      });

      if (error) throw error;

      toast.success("Password reset email sent! Check your inbox.");
      return { success: true };
    } catch (error) {
      const msg = error.message || "Failed to send reset email";
      toast.error(msg);
      return { success: false, error: msg };
    }
  }, []);

  /**
   * Refresh the current user
   */
  const refreshUser = useCallback(async () => {
    try {
      const { data: { session } } = await supabase.auth.getSession();
      
      if (session?.user) {
        dispatch(
          reduxSignIn({
            id: session.user.id,
            email: session.user.email,
            user_metadata: {
              avatar_url: session.user.user_metadata?.avatar_url || null,
              full_name: session.user.user_metadata?.full_name || session.user.email || null,
            },
          })
        );
      }
      
      return { success: true };
    } catch (error) {
      const msg = error.message || "Failed to refresh user";
      return { success: false, error: msg };
    }
  }, [dispatch]);

  return {
    user,
    status,
    error,
    isAuthenticated,
    isLoading: status === "loading",
    login,
    logout,
    signup,
    resetPassword,
    refreshUser,
  };
};