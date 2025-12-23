import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "react-hot-toast";
import GlassInput from "../components/GlassInput";
import GlassButton from "../components/GlassButton";
import { RefreshCcw, Mail, CheckCircle } from "lucide-react";
import { supabase } from "../supabaseClient";

const VerifyEmail = () => {
  const [email, setEmail] = useState("");
  const [success, setSuccess] = useState("");
  const [error, setError] = useState("");
  const [resending, setResending] = useState(false);
  const [verified, setVerified] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    // Get email from URL params or local storage
    const urlParams = new URLSearchParams(window.location.search);
    const emailFromParams = urlParams.get("email");
    if (emailFromParams) {
      setEmail(emailFromParams);
    } else {
      // Try to get email from local storage
      const storedEmail = localStorage.getItem("signup_email");
      if (storedEmail) {
        setEmail(storedEmail);
      }
    }
  }, []);

  const handleResendVerification = async () => {
    setResending(true);
    setError("");
    setSuccess("");

    try {
      if (!email) {
        throw new Error("Email not found. Please sign up again.");
      }

      const { error } = await supabase.auth.resend({
        type: "signup",
        email: email,
      });

      if (error) throw error;

      setSuccess("Verification email resent! Check your inbox.");
      toast.success("Verification email resent! Check your inbox.", {
        position: "top-right",
      });
    } catch (err) {
      const msg = err.message || "Failed to resend verification email";
      setError(msg);
      toast.error(msg, { position: "top-right" });
    } finally {
      setResending(false);
    }
  };

  const handleCheckVerification = async () => {
    try {
      // Get current session to check if email is verified
      const { data: { session } } = await supabase.auth.getSession();
      
      if (session?.user?.email_confirmed_at) {
        setVerified(true);
        setSuccess("Email verified successfully! Redirecting to dashboard...");
        toast.success("Email verified successfully!", {
          position: "top-right",
        });
        
        // Redirect to dashboard after 2 seconds
        setTimeout(() => {
          navigate("/dashboard");
        }, 2000);
      } else {
        setError("Email not yet verified. Please check your inbox for the verification link.");
        toast.error("Email not yet verified. Please check your inbox.", {
          position: "top-right",
        });
      }
    } catch (err) {
      const msg = err.message || "Failed to check verification status";
      setError(msg);
      toast.error(msg, { position: "top-right" });
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
          Verify Your Email
        </h1>
        
        <p className="text-white mb-6 text-center">
          Please check your inbox for a verification link.
        </p>

        {verified ? (
          <div className="text-center py-8">
            <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
            <p className="text-white text-lg mb-4">
              {success || "Email verified successfully!"}
            </p>
            <p className="text-gray-300">Redirecting to dashboard...</p>
          </div>
        ) : (
          <>
            <div className="mt-4">
              <GlassButton
                onClick={handleCheckVerification}
                className="w-full mb-4"
                variant="primary"
              >
                Check Verification Status
              </GlassButton>
              
              <GlassButton
                onClick={handleResendVerification}
                disabled={resending}
                className="w-full"
                variant="secondary"
              >
                {resending ? "Sending..." : "Resend Verification Email"}
              </GlassButton>
            </div>

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
          </>
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
};

export default VerifyEmail;