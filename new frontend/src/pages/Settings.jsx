import React, { useState, useEffect } from "react";
import GlassContainer from "../components/GlassContainer";
import { useSettings } from "../hooks/useSettings";
import { supabase } from "../supabaseClient";
import toast from "react-hot-toast";
import { useTranslation } from "react-i18next";
import { createPortal } from "react-dom";

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

  const { t } = useTranslation();
  const [user, setUser] = useState(null);
  const [session, setSession] = useState(null);

  // Local state for form values (to avoid immediate changes until saved)
  const [formValues, setFormValues] = useState({
    theme,
    fontSize,
    language,
    notifications,
    audioEnabled,
    audioVolume,
  });

  // Get user session
  useEffect(() => {
    const fetchSession = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      setSession(session);
      if (session) {
        setUser({
          id: session.user.id,
          email: session.user.email,
          user_metadata: {
            avatar_url: session.user.user_metadata?.avatar_url || null,
            full_name: session.user.user_metadata?.full_name || session.user.email || null,
          },
        });
      }
    };

    fetchSession();

    // Listen for auth state changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
      if (session) {
        setUser({
          id: session.user.id,
          email: session.user.email,
          user_metadata: {
            avatar_url: session.user.user_metadata?.avatar_url || null,
            full_name: session.user.user_metadata?.full_name || session.user.email || null,
          },
        });
      } else {
        setUser(null);
      }
    });

    return () => {
      subscription.unsubscribe();
    };
  }, []);

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

    // If we have a user session, save to database
    if (session) {
      try {
        const { error } = await supabase.from("user_settings").upsert({
          user_id: session.user.id,
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
      if (!session?.user?.email) {
        throw new Error("No user found");
      }

      const { error } = await supabase.auth.resetPasswordForEmail(session.user.email, {
        redirectTo: window.location.origin + "/forgotpassword",
      });

      if (error) throw error;

      toast.success(t("Password reset email sent! Please check your inbox."));
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
      if (!session) {
        throw new Error("No user found");
      }

      // Delete user data from Supabase
      const { error } = await supabase.auth.admin.deleteUser(session.user.id);
      
      if (error) throw error;

      // Sign out the user
      await supabase.auth.signOut();

      toast.success(t("Account deleted successfully."));
      
      // Redirect to sign in page
      setTimeout(() => {
        window.location.href = "/signin";
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

          <div>
            <label className="block text-white mb-2">{t("Theme")}</label>
            <div className="flex bg-white/5 p-1.5 rounded-xl max-w-md">
              <button
                onClick={() => handleChange("theme", "light")}
                className={`flex-1 px-4 py-2.5 rounded-lg no-scale transition-all ${
                  formValues.theme === "light"
                    ? "bg-[#FF9933] text-white shadow-md"
                    : "bg-white/10 text-white hover:bg-white/15"
                }`}
              >
                {t("Light")}
              </button>
              <button
                onClick={() => handleChange("theme", "dark")}
                className={`flex-1 px-4 py-2.5 mx-2 rounded-lg no-scale transition-all ${
                  formValues.theme === "dark"
                    ? "bg-[#FF9933] text-white shadow-md"
                    : "bg-white/10 text-white hover:bg-white/15"
                }`}
              >
                {t("Dark")}
              </button>
              <button
                onClick={() => handleChange("theme", "auto")}
                className={`flex-1 px-4 py-2.5 rounded-lg no-scale transition-all ${
                  formValues.theme === "auto"
                    ? "bg-[#FF9933] text-white shadow-md"
                    : "bg-white/10 text-white hover:bg-white/15"
                }`}
              >
                {t("Auto")}
              </button>
            </div>
          </div>
        </div>

        {/* Notification Settings */}
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
            {t("Notifications")}
          </h3>

          <div className="flex items-center justify-between mb-4">
            <span className="text-white">{t("Enable Notifications")}</span>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={formValues.notifications}
                onChange={(e) => handleChange("notifications", e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#FF9933]"></div>
            </label>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-white">{t("Audio Feedback")}</span>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={formValues.audioEnabled}
                onChange={(e) => handleChange("audioEnabled", e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#FF9933]"></div>
            </label>
          </div>

          {formValues.audioEnabled && (
            <div className="mt-4">
              <label className="block text-white mb-2">{t("Volume")}</label>
              <input
                type="range"
                min="0"
                max="100"
                value={formValues.audioVolume}
                onChange={(e) =>
                  handleChange("audioVolume", parseInt(e.target.value))
                }
                className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-[#FF9933]"
              />
              <div className="text-right text-white text-sm mt-1">
                {formValues.audioVolume}%
              </div>
            </div>
          )}
        </div>

        {/* Account Settings */}
        <div
          className="p-6 rounded-xl md:col-span-2"
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

          {user && (
            <div className="mb-6">
              <div className="flex items-center mb-4">
                <div className="w-12 h-12 rounded-full bg-gray-700 flex items-center justify-center mr-4">
                  <span className="text-white font-bold">
                    {user.user_metadata?.full_name?.charAt(0) ||
                      user.email?.charAt(0) ||
                      "U"}
                  </span>
                </div>
                <div>
                  <div className="text-white font-medium">
                    {user.user_metadata?.full_name || user.email}
                  </div>
                  <div className="text-gray-400 text-sm">{user.email}</div>
                </div>
              </div>

              <div className="flex flex-wrap gap-3">
                <GlassButton onClick={handleChangePassword} variant="secondary">
                  {t("Change Password")}
                </GlassButton>
                <GlassButton
                  onClick={() => setShowDeleteConfirm(true)}
                  variant="danger"
                >
                  {t("Delete Account")}
                </GlassButton>
              </div>
            </div>
          )}

          <div className="flex justify-end">
            <GlassButton onClick={saveSettings} variant="primary">
              {t("Save Settings")}
            </GlassButton>
          </div>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm &&
        createPortal(
          <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div
              className="rounded-2xl p-6 max-w-md w-full"
              style={{
                background: "rgba(30, 30, 46, 0.95)",
                border: "1px solid rgba(255, 255, 255, 0.1)",
              }}
            >
              <h3 className="text-2xl font-bold text-white mb-4">
                {t("Confirm Account Deletion")}
              </h3>
              <p className="text-gray-300 mb-6">
                {t(
                  "Are you sure you want to delete your account? This action cannot be undone and all your data will be permanently lost."
                )}
              </p>
              <div className="flex justify-end space-x-3">
                <GlassButton
                  onClick={() => setShowDeleteConfirm(false)}
                  variant="secondary"
                >
                  {t("Cancel")}
                </GlassButton>
                <GlassButton onClick={handleDeleteAccount} variant="danger">
                  {t("Delete Account")}
                </GlassButton>
              </div>
            </div>
          </div>,
          document.body
        )}
    </GlassContainer>
  );
}