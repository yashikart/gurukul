import React, { useState, useEffect } from "react";
import { toast } from "react-hot-toast";
import { Mail, Lock, UserPlus, RefreshCcw } from "lucide-react";
import GlassInput from "../components/GlassInput";
import GlassButton from "../components/GlassButton";
import { useSignUp } from "@clerk/clerk-react";

export default function SignUp() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [code, setCode] = useState("");
  const [step, setStep] = useState("email");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const { isLoaded, signUp } = useSignUp();

  useEffect(() => {
    // Ensure CAPTCHA div exists
    if (!document.getElementById("clerk-captcha")) {
      console.warn("CAPTCHA div not found");
    }
  }, []);

  const handleSignUp = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");

    if (!email || !password) {
      setError("Please enter both email and password.");
      toast.error("Please enter both email and password.", {
        position: "top-right",
      });
      return;
    }

    // Check if CAPTCHA div exists
    if (!document.getElementById("clerk-captcha")) {
      setError("CAPTCHA not ready. Please refresh the page.");
      toast.error("CAPTCHA not ready. Please refresh the page.", {
        position: "top-right",
      });
      return;
    }

    try {
      if (!isLoaded) return;

      await signUp.create({ emailAddress: email, password });
      await signUp.prepareEmailAddressVerification({ strategy: "email_code" });

      setSuccess("Check your email for a verification code.");
      toast.success("Check your email for a verification code.", {
        position: "top-right",
      });
      setStep("verify");
    } catch (err) {
      const msg = err.errors?.[0]?.longMessage || err.message || "Sign up failed";
      setError(msg);
      toast.error(msg, { position: "top-right" });
    }
  };

  const handleVerify = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");

    if (!code) {
      setError("Please enter the verification code.");
      toast.error("Please enter the verification code.", {
        position: "top-right",
      });
      return;
    }

    try {
      if (!isLoaded) return;

      const result = await signUp.attemptEmailAddressVerification({ code });

      if (result.status === "complete") {
        setSuccess("Email verified successfully! You can now sign in.");
        toast.success("Email verified successfully!", {
          position: "top-right",
        });
        // Redirect to sign in after 2 seconds
        setTimeout(() => {
          window.location.href = "/SignIn";
        }, 2000);
      } else {
        setError("Verification failed. Please try again.");
        toast.error("Verification failed. Please try again.", {
          position: "top-right",
        });
      }
    } catch (err) {
      const msg = err.errors?.[0]?.longMessage || err.message || "Verification failed";
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
          {step === "email" ? "Sign Up" : "Verify Email"}
        </h1>

        {step === "email" ? (
          <form
            className="flex flex-col gap-3 w-full items-center"
            onSubmit={handleSignUp}
          >
            <GlassInput
              name="email"
              type="email"
              placeholder="Email"
              icon={Mail}
              autoComplete="username"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            <GlassInput
              name="password"
              type="password"
              placeholder="Password"
              icon={Lock}
              autoComplete="new-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            <div id="clerk-captcha"></div>
            <GlassButton
              type="submit"
              icon={UserPlus}
              className="w-full mt-2"
              variant="primary"
            >
              Sign Up
            </GlassButton>
          </form>
        ) : (
          <form
            className="flex flex-col gap-3 w-full items-center"
            onSubmit={handleVerify}
          >
            <GlassInput
              name="code"
              type="text"
              placeholder="Verification Code"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              required
            />
            <GlassButton
              type="submit"
              icon={RefreshCcw}
              className="w-full mt-2"
              variant="primary"
            >
              Verify
            </GlassButton>
            <button
              type="button"
              onClick={() => setStep("email")}
              className="text-white hover:text-[#FFD700] transition-colors font-medium text-sm"
            >
              Back to Sign Up
            </button>
          </form>
        )}

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
            {(() => {
              try {
                // eslint-disable-next-line
                const { Link } = require("react-router-dom");
                return (
                  <Link
                    to="/SignIn"
                    className="text-white hover:text-[#FFD700] transition-colors font-medium"
                  >
                    Already have an account? Sign In
                  </Link>
                );
              } catch {
                return (
                  <a
                    href="/SignIn"
                    className="text-white hover:text-[#FFD700] transition-colors font-medium"
                  >
                    Already have an account? Sign In
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
