import React, { useState } from "react";
import { toast } from "react-hot-toast";
import { Mail, Lock, LogIn } from "lucide-react";
import GlassInput from "../components/GlassInput";
import GlassButton from "../components/GlassButton";
import { useNavigate, Link } from "react-router-dom";
import { useDispatch } from "react-redux";
import { setUser } from "../store/authSlice";
import { supabase } from "../supabaseClient";
import { useTranslation } from "react-i18next";

export default function SignIn() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const [error, setError] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSignIn = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      if (!email || !password) {
        setError(t("Please enter both email and password."));
        toast.error(t("Please enter both email and password."), {
          position: "bottom-right",
        });
        setLoading(false);
        return;
      }

      // Check network connectivity first
      if (!navigator.onLine) {
        throw new Error(t("No internet connection. Please check your network."));
      }

      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (error) throw error;

      // Update Redux store with user data
      dispatch(
        setUser({
          id: data.user.id,
          email: data.user.email,
          user_metadata: {
            avatar_url: data.user.user_metadata?.avatar_url || null,
            full_name: data.user.user_metadata?.full_name || data.user.email || null,
          },
        })
      );

      toast.success(t("Logged in successfully!"), {
        position: "bottom-right",
        id: "auth-success",
      });

      navigate("/dashboard");
    } catch (err) {
      console.error("Sign in error:", err);
      
      // Handle specific error cases
      if (err.message?.includes("Invalid login credentials") || err.message?.includes("Invalid login")) {
        setError(t("Invalid email or password. Please try again."));
        toast.error(t("Invalid email or password. Please try again."), {
          position: "bottom-right",
          duration: 5000,
        });
      } else if (err.message?.includes("Failed to fetch") || err.name === "AuthRetryableFetchError") {
        const errorMessage = t("Network error: Unable to connect to authentication service. Please check your internet connection and try again.");
        setError(errorMessage);
        toast.error(errorMessage, {
          position: "bottom-right",
          duration: 7000,
        });
        console.error("Network error details:", {
          message: err.message,
          name: err.name,
          stack: err.stack,
          online: navigator.onLine,
        });
      } else if (err.message?.includes("No internet connection")) {
        setError(t(err.message));
        toast.error(t(err.message), {
          position: "bottom-right",
          duration: 5000,
        });
      } else {
        const errorMessage = err.message || t("Failed to sign in. Please try again.");
        setError(errorMessage);
        toast.error(errorMessage, {
          position: "bottom-right",
          duration: 5000,
        });
      }
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
          className="text-3xl font-bold mb-8"
          style={{
            color: "#FFD700",
            fontFamily: "Nunito, sans-serif",
            textShadow: "0 2px 4px rgba(0,0,0,0.15)",
          }}
        >
          {t("Sign In")}
        </h1>
        <div className="w-full flex flex-col gap-4 items-center">
          <form
            className="flex flex-col gap-3 w-full items-center"
            autoComplete="on"
            onSubmit={handleSignIn}
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
              placeholder={t("Password")}
              icon={Lock}
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            <GlassButton
              type="submit"
              icon={LogIn}
              className="w-full mt-2"
              variant="primary"
              disabled={loading}
            >
              {loading ? t("Signing in...") : t("Sign In")}
            </GlassButton>
          </form>
          {error && (
            <div className="text-red-300 text-sm mt-4 font-semibold">
              {error}
            </div>
          )}
          
          <div className="mt-7 flex flex-col gap-3 items-center text-sm">
            <div className="w-full border-t border-white/20 my-2"></div>
            {/* Forgot Password link */}
            <Link
              to="/forgotpassword"
              className="text-white hover:text-[#FFD700] transition-colors"
            >
              {t("Forgot Password?")}
            </Link>

            {/* Sign Up link */}
            <Link
              to="/signup"
              className="text-white hover:text-[#FFD700] transition-colors font-medium"
            >
              {t("Don't have an account? Sign Up")}
            </Link>
          </div>
        </div>
      </section>
    </main>
  );
}