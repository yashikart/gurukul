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
import { useSignIn, useSignUp, useClerk } from "@clerk/clerk-react";

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
  const { isLoaded: signInLoaded, signIn, setActive } = useSignIn();
  const { signOut: clerkSignOut } = useClerk();

  const login = useCallback(
    async (email, password) => {
      try {
        if (!signInLoaded) return { success: false, error: "Auth not ready" };
        const res = await signIn.create({ identifier: email, password });
        if (res?.status === "complete") {
          await setActive({ session: res.createdSessionId });
          toast.success("Signed in successfully", { id: "auth-success" });
          return { success: true };
        }
        return { success: false, error: "Sign in incomplete" };
      } catch (error) {
        const msg = error.errors?.[0]?.longMessage || error.message || "Failed to sign in";
        toast.error(msg);
        return { success: false, error: msg };
      }
    },
    [signInLoaded, signIn, setActive]
  );

  /**
   * Sign out the current user
   */
  const logout = useCallback(async () => {
    try {
      await clerkSignOut();
      toast.success("Signed out successfully");
      return { success: true };
    } catch (error) {
      const msg = error.message || "Failed to sign out";
      toast.error(msg);
      return { success: false, error: msg };
    }
  }, [clerkSignOut]);

  /**
   * Sign up with email and password
   */
  const { isLoaded: signUpLoaded, signUp } = useSignUp();
  const signup = useCallback(async (email, password) => {
    try {
      if (!signUpLoaded) return { success: false, error: "Auth not ready" };
      await signUp.create({ emailAddress: email, password });
      await signUp.prepareEmailAddressVerification({ strategy: "email_code" });
      toast.success("Signed up successfully! Check your email for the code.");
      return { success: true };
    } catch (error) {
      const msg = error.errors?.[0]?.longMessage || error.message || "Sign up failed";
      toast.error(msg);
      return { success: false, error: msg };
    }
  }, [signUpLoaded, signUp]);

  /**
   * Reset password
   */
  const { client } = useClerk();
  const resetPassword = useCallback(async (email) => {
    try {
      await client.sendPasswordResetEmail({ emailAddress: email });
      toast.success("Password reset email sent! Check your inbox.");
      return { success: true };
    } catch (error) {
      const msg = error.errors?.[0]?.longMessage || error.message || "Failed to send reset email";
      toast.error(msg);
      return { success: false, error: msg };
    }
  }, [client]);

  /**
   * Refresh the current user
   */
  const refreshUser = useCallback(async () => {
    // With Clerk, user state updates via hooks; no manual refresh needed
    return { success: true };
  }, []);

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
