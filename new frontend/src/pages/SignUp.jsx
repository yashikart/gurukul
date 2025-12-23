import React, { useState } from "react";
import { toast } from "react-hot-toast";
import { Mail, Lock, UserPlus } from "lucide-react";
import GlassInput from "../components/GlassInput";
import GlassButton from "../components/GlassButton";
import { supabase } from "../supabaseClient";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";

export default function SignUp() {
  const { t } = useTranslation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSignUp = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setLoading(true);

    // Validation
    if (!email || !password || !confirmPassword) {
      setError(t("Please fill in all fields."));
      toast.error(t("Please fill in all fields."), {
        position: "top-right",
      });
      setLoading(false);
      return;
    }

    if (password !== confirmPassword) {
      setError(t("Passwords do not match."));
      toast.error(t("Passwords do not match."), {
        position: "top-right",
      });
      setLoading(false);
      return;
    }

    if (password.length < 6) {
      setError(t("Password must be at least 6 characters long."));
      toast.error(t("Password must be at least 6 characters long."), {
        position: "top-right",
      });
      setLoading(false);
      return;
    }

    try {
      // Check network connectivity first
      if (!navigator.onLine) {
        throw new Error(t("No internet connection. Please check your network."));
      }

      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          emailRedirectTo: window.location.origin + "/verify-email",
        },
      });

      if (error) throw error;

      setSuccess(t("Account created successfully! Please check your email for verification link."));
      toast.success(t("Account created successfully! Please check your email for verification link."), {
        position: "top-right",
      });

      // Clear form
      setEmail("");
      setPassword("");
      setConfirmPassword("");
      
      // Redirect to sign in after 3 seconds
      setTimeout(() => {
        navigate("/signin");
      }, 3000);
    } catch (err) {
      console.error("Sign up error:", err);
      
      let errorMessage = err.message || t("Sign up failed");
      
      // Handle specific error cases
      if (err.message?.includes("Failed to fetch") || err.name === "AuthRetryableFetchError") {
        errorMessage = t("Network error: Unable to connect to authentication service. Please check your internet connection and try again.");
        console.error("Network error details:", {
          message: err.message,
          name: err.name,
          stack: err.stack,
          online: navigator.onLine,
        });
      } else if (err.message?.includes("User already registered")) {
        errorMessage = t("An account with this email already exists. Please sign in instead.");
      } else if (err.message?.includes("Password")) {
        errorMessage = err.message;
      }
      
      setError(errorMessage);
      toast.error(errorMessage, { 
        position: "top-right",
        duration: err.message?.includes("Failed to fetch") ? 7000 : 5000,
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen w-full flex items-center justify-center relative overflow-hidden">
      {/* Background Image */}
      <div
        className="absolute inset-0 z-0"
        style={{
          backgroundImage: "url(/bg/bg.png)",
          backgroundSize: "cover",
          backgroundPosition: "center",
          backgroundRepeat: "no-repeat",
          filter: "brightness(0.7)",
          WebkitFilter: "brightness(0.7)",
        }}
      />

      <section className="glass-card relative z-10">
        <h1
          className="text-3xl font-bold mb-6"
          style={{
            color: "#FFD700",
            fontFamily: "Tiro Devanagari Hindi, serif",
            textShadow: "0 2px 4px rgba(0,0,0,0.15)",
          }}
        >
          {t("Create Account")}
        </h1>

        <form
          className="flex flex-col gap-3 w-full items-center"
          onSubmit={handleSignUp}
        >
          <GlassInput
            name="email"
            type="email"
            placeholder={t("Email")}
            icon={Mail}
            autoComplete="username"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <GlassInput
            name="password"
            type="password"
            placeholder={t("Password (min. 6 characters)")}
            icon={Lock}
            autoComplete="new-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <GlassInput
            name="confirmPassword"
            type="password"
            placeholder={t("Confirm Password")}
            icon={Lock}
            autoComplete="new-password"
            required
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
          />
          <GlassButton
            type="submit"
            icon={UserPlus}
            className="w-full mt-2"
            variant="primary"
            disabled={loading}
          >
            {loading ? t("Creating Account...") : t("Sign Up")}
          </GlassButton>
        </form>

        {error && (
          <div className="text-red-300 text-sm mt-4 font-semibold">{error}</div>
        )}
        {success && (
          <div className="text-green-300 text-sm mt-4 font-semibold">
            {success}
          </div>
        )}

        <div className="mt-7 flex flex-col gap-3 items-center text-sm">
          <div className="w-full border-t border-white/20 my-2"></div>
          {/* Back to Sign In link */}
          <div>
            <button
              onClick={() => navigate("/signin")}
              className="text-white hover:text-[#FFD700] transition-colors font-medium"
            >
              {t("Already have an account? Sign In")}
            </button>
          </div>
        </div>
      </section>
    </main>
  );
}