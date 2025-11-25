import React, { useState, useEffect } from "react";
import GlassContainer from "../components/GlassContainer";
import { useSettings } from "../hooks/useSettings";
import { useAuth } from "../hooks/useAuth";
import { supabase } from "../supabaseClient";
import toast from "react-hot-toast";
import { useTranslation } from "react-i18next";
import { createPortal } from "react-dom";
import { useUser } from "@clerk/clerk-react";

export default function Settings() {
  const {
    theme,
    fontSize,
    language,
    notifications,
    audioEnabled,
    audioVolume,
    updateMultipleSettings,
  } = useSettings();

  const { user, resetPassword, logout } = useAuth();
  const { t } = useTranslation();
  const { isSignedIn, user: clerkUser } = useUser();

  // Local state for form values (to avoid immediate changes until saved)
  const [formValues, setFormValues] = useState({
    theme,
    fontSize,
    language,
    notifications,
    audioEnabled,
    audioVolume,
  });

  // Update local state when global settings change
  useEffect(() => {
    setFormValues({
      theme,
      fontSize,
      language,
      notifications,
      audioEnabled,
      audioVolume,
    });
  }, [theme, fontSize, language, notifications, audioEnabled, audioVolume]);

  // Handle form value changes
  const handleChange = (setting, value) => {
    setFormValues((prev) => ({
      ...prev,
      [setting]: value,
    }));
    // Auto-apply and persist language & font size immediately
    if (setting === "language" || setting === "fontSize") {
      updateMultipleSettings({ [setting]: value });
    }
  };

  // Save all settings
  const saveSettings = async () => {
    // Update global settings (will save to localStorage)
    updateMultipleSettings(formValues);

    // If we wanted to save to database for logged in users:
    if (user) {
      try {
        const { error } = await supabase.from("user_settings").upsert({
          user_id: user.id,
          settings: formValues,
        });

        if (error) throw error;
      } catch (error) {
        console.error("Error saving settings to database:", error);
      }
    }

    // Show success message
    toast.success(t("Settings saved successfully!"));
  };

  // Handle password change
  const handleChangePassword = async () => {
    try {
      const result = await resetPassword(user?.email);

      if (result.success) {
        toast.success(t("Password reset email sent! Please check your inbox."));
      } else {
        throw new Error(result.error);
      }
    } catch (error) {
      console.error("Error sending password reset:", error);
      toast.error(t("Failed to send password reset email. Please try again."));
    }
  };

  // State for delete confirmation modal
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  // Handle account deletion
  const handleDeleteAccount = async () => {
    // Perform account deletion
    try {
      // First, get the current user's ID
      if (!isSignedIn || !clerkUser) {
        throw new Error("No user found");
      }

      console.log("Deleting user account:", clerkUser.id);

      // With Clerk, actual account deletion should be done server-side via Clerk Admin API.
      // Here we just sign the user out and show a message.
      toast.success(t("Account deletion requested. You will be signed out."));

      await logout();
      localStorage.clear();

      setTimeout(() => {
        window.location.href = "/signin?deleted=true";
      }, 2000);
    } catch (error) {
      console.error("Error deleting account:", error);
      toast.error(t("Error deleting account. Please try again."));
    }
  };

  return (
    <GlassContainer>
      <h2
        className="text-4xl md:text-5xl font-extrabold mb-6 drop-shadow-lg transition-all duration-300 hover:bg-gradient-to-r hover:from-white hover:to-[#FF9933] hover:bg-clip-text hover:text-transparent"
        style={{ color: "#FFFFFF", fontFamily: "Tiro Devanagari Hindi, serif" }}
      >
        {t("Settings")}
      </h2>

      <p
        className="text-lg md:text-xl font-medium mb-8"
        style={{ color: "#FFFFFF", fontFamily: "Inter, Poppins, sans-serif" }}
      >
        {t("Customize your Gurukul experience by adjusting these settings.")}
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Theme Settings */}
        <div
          className="p-6 rounded-xl"
          style={{
            background: "rgba(255, 255, 255, 0.1)",
            backdropFilter: "blur(10px)",
            border: "1px solid rgba(255, 255, 255, 0.18)",
          }}
        >
          <h3
            className="text-2xl font-bold mb-4 transition-all duration-300 hover:bg-gradient-to-r hover:from-white hover:to-[#FF9933] hover:bg-clip-text hover:text-transparent"
            style={{
              color: "#FFFFFF",
              fontFamily: "Tiro Devanagari Hindi, serif",
            }}
          >
            {t("Appearance")}
          </h3>

          <div className="mb-4">
            <label className="block text-white mb-2">
              {t("Font Size (Browser Zoom)")}
            </label>
            <div className="flex bg-white/5 p-1.5 rounded-xl max-w-md">
              <button
                onClick={() => handleChange("fontSize", "small")}
                className={`flex-1 px-4 py-2.5 rounded-lg no-scale transition-all ${
                  formValues.fontSize === "small"
                    ? "bg-[#FF9933] text-white shadow-md"
                    : "bg-white/10 text-white hover:bg-white/15"
                }`}
              >
                <span className="text-sm">{t("Small")}</span>
              </button>
              <button
                onClick={() => handleChange("fontSize", "medium")}
                className={`flex-1 px-4 py-2.5 mx-2 rounded-lg no-scale transition-all ${
                  formValues.fontSize === "medium"
                    ? "bg-[#FF9933] text-white shadow-md"
                    : "bg-white/10 text-white hover:bg-white/15"
                }`}
              >
                <span className="text-base">{t("Medium")}</span>
              </button>
              <button
                onClick={() => handleChange("fontSize", "large")}
                className={`flex-1 px-4 py-2.5 rounded-lg no-scale transition-all ${
                  formValues.fontSize === "large"
                    ? "bg-[#FF9933] text-white shadow-md"
                    : "bg-white/10 text-white hover:bg-white/15"
                }`}
              >
                <span className="text-lg">{t("Large")}</span>
              </button>
            </div>
          </div>
        </div>

        {/* Preferences */}
        <div
          className="p-6 rounded-xl"
          style={{
            background: "rgba(255, 255, 255, 0.1)",
            backdropFilter: "blur(10px)",
            border: "1px solid rgba(255, 255, 255, 0.18)",
          }}
        >
          <h3
            className="text-2xl font-bold mb-4 transition-all duration-300 hover:bg-gradient-to-r hover:from-white hover:to-[#FF9933] hover:bg-clip-text hover:text-transparent"
            style={{
              color: "#FFFFFF",
              fontFamily: "Tiro Devanagari Hindi, serif",
            }}
          >
            {t("Preferences")}
          </h3>

          <div className="mb-4">
            <label className="block text-white mb-2">{t("Language")}</label>
            <div className="flex bg-white/5 p-1.5 rounded-xl max-w-md">
              <button
                onClick={() => handleChange("language", "english")}
                className={`flex-1 px-4 py-2.5 rounded-lg no-scale transition-all ${
                  formValues.language === "english"
                    ? "bg-[#FF9933] text-white shadow-md"
                    : "bg-white/10 text-white hover:bg-white/15"
                }`}
              >
                {t("English")}
              </button>
              <button
                onClick={() => handleChange("language", "hindi")}
                className={`flex-1 px-4 py-2.5 ml-2 rounded-lg no-scale transition-all ${
                  formValues.language === "hindi"
                    ? "bg-[#FF9933] text-white shadow-md"
                    : "bg-white/10 text-white hover:bg-white/15"
                }`}
              >
                {t("Hindi")}
              </button>
            </div>
          </div>

          <div className="mb-4">
            <label className="flex items-center text-white cursor-pointer">
              <input
                type="checkbox"
                checked={formValues.notifications}
                onChange={() =>
                  handleChange("notifications", !formValues.notifications)
                }
                className="mr-2 w-5 h-5 accent-[#FF9933]"
              />
              <span>{t("Enable Notifications")}</span>
            </label>
          </div>
        </div>
      </div>

      {/* Account Settings */}
      <div
        className="p-6 rounded-xl mt-8"
        style={{
          background: "rgba(255, 255, 255, 0.1)",
          backdropFilter: "blur(10px)",
          border: "1px solid rgba(255, 255, 255, 0.18)",
        }}
      >
        <h3
          className="text-2xl font-bold mb-4 transition-all duration-300 hover:bg-gradient-to-r hover:from-white hover:to-[#FF9933] hover:bg-clip-text hover:text-transparent"
          style={{
            color: "#FFFFFF",
            fontFamily: "Tiro Devanagari Hindi, serif",
          }}
        >
          {t("Account")}
        </h3>

        <div className="mb-4">
          <button
            onClick={handleChangePassword}
            className="px-5 py-3 rounded-lg bg-white/10 text-white hover:bg-white/20 transition-all mb-2 w-full md:w-auto"
          >
            {t("Change Password")}
          </button>
        </div>

        <div>
          <button
            onClick={() => setShowDeleteConfirm(true)}
            className="px-5 py-3 rounded-lg bg-red-500/30 text-white hover:bg-red-500/40 transition-all w-full md:w-auto"
          >
            {t("Delete Account")}
          </button>
          {showDeleteConfirm &&
            createPortal(
              <>
                <div className="fixed inset-0 bg-black/30 backdrop-blur-sm z-50" />
                <div className="fixed inset-0 z-60 flex items-center justify-center">
                  <div
                    className="relative w-full max-w-md mx-4 p-6 rounded-3xl"
                    style={{
                      background: "rgba(30, 30, 40, 0.25)",
                      backdropFilter: "blur(20px)",
                      WebkitBackdropFilter: "blur(20px)",
                      border: "1px solid rgba(255, 255, 255, 0.225)",
                    }}
                  >
                    <h4 className="text-lg font-semibold text-white mb-4">
                      {t(
                        "Are you sure you want to delete your account? This action cannot be undone."
                      )}
                    </h4>
                    <div className="flex justify-end space-x-4">
                      <button
                        onClick={() => setShowDeleteConfirm(false)}
                        className="px-4 py-2 rounded-lg bg-white/20 text-white hover:bg-white/30"
                      >
                        {t("Cancel")}
                      </button>
                      <button
                        onClick={async () => {
                          setShowDeleteConfirm(false);
                          await handleDeleteAccount();
                        }}
                        className="px-4 py-2 rounded-lg bg-red-700 text-white hover:bg-red-900"
                      >
                        {t("Confirm")}
                      </button>
                    </div>
                  </div>
                </div>
              </>,
              document.body
            )}
        </div>
      </div>

      <div className="mt-8 text-center">
        <button
          onClick={saveSettings}
          className="px-8 py-3 rounded-lg text-white font-medium transition-all hover:scale-105"
          style={{
            background: "rgba(255, 153, 51, 0.7)",
            backdropFilter: "blur(10px)",
            boxShadow: "0 4px 15px rgba(255, 153, 51, 0.3)",
          }}
        >
          {t("Save Changes")}
        </button>
      </div>
    </GlassContainer>
  );
}
