import React, { useState, useEffect } from "react";
import { toast } from "react-hot-toast";
import { Lock, Key } from "lucide-react";
import GlassInput from "../components/GlassInput";
import GlassButton from "../components/GlassButton";
import { useNavigate } from "react-router-dom";
import { supabase } from "../supabaseClient";

export default function UpdatePassword() {
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleUpdatePassword = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setLoading(true);

    if (!password || !confirmPassword) {
      setError("Please fill in both password fields.");
      toast.error("Please fill in both password fields.", {
        position: "top-right",
      });
      setLoading(false);
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      toast.error("Passwords do not match.", {
        position: "top-right",
      });
      setLoading(false);
      return;
    }

    if (password.length < 6) {
      setError("Password must be at least 6 characters long.");
      toast.error("Password must be at least 6 characters long.", {
        position: "top-right",
      });
      setLoading(false);
      return;
    }

    try {
      const { error } = await supabase.auth.updateUser({
        password: password,
      });

      if (error) throw error;

      setSuccess("Password updated successfully! Redirecting to sign in...");
      toast.success("Password updated successfully!", {
        position: "top-right",
      });

      // Redirect to sign in after 2 seconds
      setTimeout(() => {
        navigate("/signin");
      }, 2000);
    } catch (err) {
      const msg = err.message || "Failed to update password";
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
          Update Password
        </h1>

        <p className="text-white mb-6 text-center">
          Enter your new password below.
        </p>

        <form
          className="flex flex-col gap-3 w-full items-center"
          onSubmit={handleUpdatePassword}
        >
          <GlassInput
            name="password"
            type="password"
            placeholder="New Password (min. 6 characters)"
            icon={Lock}
            autoComplete="new-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <GlassInput
            name="confirmPassword"
            type="password"
            placeholder="Confirm New Password"
            icon={Lock}
            autoComplete="new-password"
            required
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
          />
          <GlassButton
            type="submit"
            icon={Key}
            className="w-full mt-2"
            variant="primary"
            disabled={loading}
          >
            {loading ? "Updating..." : "Update Password"}
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