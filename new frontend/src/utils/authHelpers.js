import { storage } from "./storageUtils";
import { toast } from "react-hot-toast";

/**
 * Thoroughly clears authentication data from storage while preserving avatar data
 * This helps ensure a complete sign-out without losing user's avatar settings
 */
export const clearAuthData = () => {
  try {
    // Clear localStorage except persistent keys (avatar data, settings)
    storage.clearExceptPersistent();

    // Specifically target Supabase auth tokens in sessionStorage
    window.sessionStorage.removeItem("supabase.auth.token");

    // Clear any auth-related cookies
    document.cookie.split(";").forEach(function (c) {
      document.cookie = c
        .replace(/^ +/, "")
        .replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/");
    });

    console.log("Auth data cleared successfully (avatar data preserved)");
    return true;
  } catch (error) {
    console.error("Error clearing auth data:", error);
    return false;
  }
};

/**
 * Checks if the current user's account has been marked as deleted
 * and signs them out if it has.
 *
 * @returns {Promise<boolean>} True if the user is deleted and was signed out, false otherwise
 */
export const checkAndHandleDeletedAccount = async () => {
  // With Supabase, account deletion is managed via Admin API; skip client check
  return false;
};

/**
 * Checks if a user's email matches a deleted account pattern
 *
 * @param {string} email The email to check
 * @returns {boolean} True if the email matches a deleted account pattern
 */
export const isDeletedAccountEmail = (email) => {
  if (!email) return false;

  // Check if the email matches our deleted account pattern
  return email.startsWith("deleted-") && email.includes("@deleted-account.com");
};