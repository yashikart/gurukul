import React, { useState, useEffect } from "react";
import { toast } from "react-hot-toast";
import { Mail, Lock, LogIn, RefreshCcw } from "lucide-react";
import GlassInput from "../components/GlassInput";
import GlassButton from "../components/GlassButton";
import { useNavigate, useLocation, Link } from "react-router-dom";
import { getLastVisitedPath } from "../utils/routeUtils";
import { useSignIn, useAuth, useUser } from "@clerk/clerk-react";

export default function SignIn() {
  const navigate = useNavigate();
  const location = useLocation();
  const [error, setError] = useState("");
  const { isLoaded, signIn, setActive } = useSignIn();
  const { signOut } = useAuth();
  const { isSignedIn } = useUser();

  useEffect(() => {
    if (isSignedIn) {
      navigate("/home");
    }
  }, [isSignedIn, navigate]);

  // Check for deleted=true parameter in URL
  useEffect(() => {
    const searchParams = new URLSearchParams(location.search);
    if (searchParams.get("deleted") === "true") {
      // Show a notification that the account was deleted
      toast.success("Your account has been successfully deleted.", {
        position: "top-right",
        icon: "🗑️",
        duration: 5000,
        id: "account-deleted",
      });

      // Remove the parameter from the URL without reloading the page
      const newUrl = window.location.pathname;
      window.history.replaceState({}, document.title, newUrl);
    }
  }, [location]);

  const handleOAuthSignIn = async (provider) => {
    setError("");

    try {
      toast.loading("Redirecting to sign in...", {
        position: "bottom-right",
        id: "oauth-loading",
      });

      await signIn.authenticateWithRedirect({
        strategy: provider === "google" ? "oauth_google" : provider,
        redirectUrl: "/auth/callback",
        redirectUrlComplete: "/home",
      });
    } catch (err) {
      toast.dismiss("oauth-loading");
      console.error("OAuth sign in error:", err);
      setError(err.errors?.[0]?.longMessage || err.message || "Failed to sign in");
      toast.error("Authentication failed. Please try again.", {
        position: "bottom-right",
      });
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
          Sign In
        </h1>
        <div className="w-full flex flex-col gap-4 items-center">
          <form
            className="flex flex-col gap-3 w-full items-center"
            autoComplete="on"
            onSubmit={async (e) => {
              e.preventDefault();
              setError("");

              const loadingToast = toast.loading("Signing in...", {
                position: "bottom-right",
              });

              try {
                const email = e.target.email.value;
                const password = e.target.password.value;

                if (!email || !password) {
                  setError("Please enter both email and password.");
                  toast.error("Please enter both email and password.", {
                    position: "bottom-right",
                  });
                  return;
                }

                if (!isLoaded) return; // Clerk not ready yet

                const result = await signIn.create({ identifier: email, password });

                if (result?.status === "complete") {
                  await setActive({ session: result.createdSessionId });
                  toast.dismiss(loadingToast);
                  toast.success("Logged in successfully!", {
                    position: "bottom-right",
                    id: "auth-success",
                  });
                  navigate(getLastVisitedPath());
                } else {
                  throw new Error("Sign in not completed");
                }
              } catch (err) {
                toast.dismiss(loadingToast);
                const errorMessage = err.errors?.[0]?.longMessage || err.message || "Failed to sign in. Please try again.";
                setError(errorMessage);
                toast.error(errorMessage, {
                  position: "bottom-right",
                  duration: 5000,
                });
              }
            }}
          >
            <GlassInput
              name="email"
              type="email"
              placeholder="Email"
              icon={Mail}
              autoComplete="username"
              required
            />
            <GlassInput
              name="password"
              type="password"
              placeholder="Password"
              icon={Lock}
              autoComplete="current-password"
              required
            />
            <GlassButton
              type="submit"
              icon={LogIn}
              className="w-full mt-2"
              variant="primary"
            >
              Sign in with Email
            </GlassButton>
          </form>
          <GlassButton
            type="button"
            icon={RefreshCcw}
            onClick={() => handleOAuthSignIn("google")}
            className="w-full mt-3"
          >
            Sign in with Google
          </GlassButton>
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
              Forgot Password?
            </Link>

            {/* Sign Up link */}
            <Link
              to="/signup"
              className="text-white hover:text-[#FFD700] transition-colors font-medium"
            >
              Don't have an account? Sign Up
            </Link>
          </div>
        </div>
      </section>
    </main>
  );
}
