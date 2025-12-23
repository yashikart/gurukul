import React, { useState } from "react";
import { toast } from "react-hot-toast";
import { Mail, RotateCcw } from "lucide-react";
import GlassInput from "../components/GlassInput";
import GlassButton from "../components/GlassButton";
import { useNavigate } from "react-router-dom";
import { supabase } from "../supabaseClient";

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleResetPassword = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setLoading(true);

    if (!email) {
      setError("Please enter your email address.");
      toast.error("Please enter your email address.", {
        position: "top-right",
      });
      setLoading(false);
      return;
    }

    try {
      const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: window.location.origin + "/update-password",
      });

      if (error) throw error;

      setSuccess("Password reset instructions sent! Please check your email.");
      toast.success("Password reset instructions sent! Please check your email.", {
        position: "top-right",
      });

      // Clear form
      setEmail("");
    } catch (err) {
      const msg = err.message || "Failed to send password reset instructions";
      setError(msg);
      toast.error(msg, { position: "top-right" });
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
          Reset Password
        </h1>

        <p className="text-white mb-6 text-center">
          Enter your email address and we'll send you instructions to reset your password.
        </p>

        <form
          className="flex flex-col gap-3 w-full items-center"
          onSubmit={handleResetPassword}
        >
          <GlassInput
            name="email"
            type="email"
            placeholder="Email"
            icon={Mail}
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <GlassButton
            type="submit"
            icon={RotateCcw}
            className="w-full mt-2"
            variant="primary"
            disabled={loading}
          >
            {loading ? "Sending..." : "Send Reset Instructions"}
          </GlassButton>
        </form>

        {error && (
          <div className="text-red-300 text-sm mt-4 font-semibold text-center">
            {error}
          </div>
        )}
        {success && (
          <div className="text-green-300 text-sm mt-4 font-semibold text-center">
            {success}
          </div>
        )}

        <div className="mt-6 flex flex-col gap-3 items-center text-sm">
          <div className="w-full border-t border-white/20 my-2"></div>
          <button
            onClick={() => navigate("/signin")}
            className="text-white hover:text-[#FFD700] transition-colors font-medium"
          >
            Back to Sign In
          </button>
        </div>
      </section>
    </main>
  );
}