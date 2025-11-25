import React, { useState } from "react";
import { Mail, Key } from "lucide-react";
import { toast } from "react-hot-toast";
import GlassInput from "../components/GlassInput";
import GlassButton from "../components/GlassButton";
import { useClerk } from "@clerk/clerk-react";

export default function ForgotPassword() {
  const [emailSent, setEmailSent] = useState(false);
  const [error, setError] = useState("");
  const { client } = useClerk();

  const handleReset = async (e) => {
    e.preventDefault();
    setError("");
    setEmailSent(false);
    const email = e.target.email.value;

    if (!email) {
      setError("Please enter your email.");
      toast.error("Please enter your email.", {
        position: "bottom-right",
        icon: "📧",
      });
      return;
    }

    // Show loading toast
    const loadingToast = toast.loading("Sending reset instructions...", {
      position: "bottom-right",
    });

    try {
      await client.sendPasswordResetEmail({ emailAddress: email });

      // Dismiss loading toast
      toast.dismiss(loadingToast);

      setEmailSent(true);
      toast.success("Reset instructions sent! Check your email inbox.", {
        position: "bottom-right",
        icon: "✉️",
        duration: 5000,
      });
    } catch (err) {
      // Dismiss loading toast
      toast.dismiss(loadingToast);

      setError("An unexpected error occurred. Please try again.");
      toast.error("An unexpected error occurred. Please try again.", {
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
          className="text-3xl font-bold mb-6"
          style={{
            color: "#FFD700",
            fontFamily: "Nunito, sans-serif",
            textShadow: "0 2px 4px rgba(0,0,0,0.15)",
          }}
        >
          Forgot Password
        </h1>
        <form
          className="flex flex-col gap-3 w-full items-center"
          onSubmit={handleReset}
        >
          <GlassInput
            name="email"
            type="email"
            placeholder="Enter your email"
            icon={Mail}
            autoComplete="username"
            required
          />
          <GlassButton
            type="submit"
            icon={Key}
            className="w-full mt-2"
            variant="primary"
          >
            Send Reset Link
          </GlassButton>
        </form>
        {emailSent && (
          <div className="text-green-300 text-sm mt-4 font-semibold">
            Check your email for a reset link!
          </div>
        )}
        {error && (
          <div className="text-red-300 text-sm mt-4 font-semibold">{error}</div>
        )}

        <div className="mt-7 flex flex-col gap-3 items-center text-sm">
          <div className="w-full border-t border-white/20 my-2"></div>
          {/* Back to Sign In link */}
          <div>
            {(() => {
              try {
                // eslint-disable-next-line
                const { Link } = require("react-router-dom");
                return (
                  <Link
                    to="/SignIn"
                    className="text-white hover:text-[#FFD700] transition-colors font-medium"
                  >
                    Back to Sign In
                  </Link>
                );
              } catch {
                return (
                  <a
                    href="/SignIn"
                    className="text-white hover:text-[#FFD700] transition-colors font-medium"
                  >
                    Back to Sign In
                  </a>
                );
              }
            })()}
          </div>
        </div>
      </section>
    </main>
  );
}
