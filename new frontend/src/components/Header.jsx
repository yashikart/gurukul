import React, { useState, useEffect, useRef } from "react";
import { useNavigate, NavLink, useLocation } from "react-router-dom";
import { supabase } from "../supabaseClient";
import gsap from "gsap";
import { useGSAP } from "../hooks/useGSAP";
import { Menu, X, Globe, ChevronDown } from "lucide-react";
import { useSettings } from "../hooks/useSettings";
import { useTranslation } from "react-i18next";
import "../styles/header.css";

export default function Header({ onToggleSidebar, sidebarCollapsed }) {
  const navigate = useNavigate();
  const location = useLocation();
  const [avatarUrl, setAvatarUrl] = useState("");
  const [user, setUser] = useState(null);
  const [session, setSession] = useState(null);
  const [isLanguageDropdownOpen, setIsLanguageDropdownOpen] = useState(false);
  const { language, updateLanguage } = useSettings();
  const { t } = useTranslation();
  const languageDropdownRef = useRef(null);

  // Refs for GSAP animations
  const headerRef = useRef(null);
  const logoRef = useRef(null);
  const aboutLinkRef = useRef(null);
  const logoutBtnRef = useRef(null);
  const languageBtnRef = useRef(null);

  // We'll use CSS hover effects instead of GSAP for better reliability

  // Initial animation when component mounts
  useGSAP(() => {
    // Initial animation for header
    gsap.fromTo(
      headerRef.current,
      { y: -100, opacity: 0 },
      { y: 0, opacity: 1, duration: 0.8, ease: "power3.out" }
    );

    // Staggered animation for header elements
    gsap.fromTo(
      [logoRef.current, aboutLinkRef.current, languageBtnRef.current, logoutBtnRef.current],
      { y: -20, opacity: 0 },
      {
        y: 0,
        opacity: 1,
        duration: 0.6,
        stagger: 0.1,
        ease: "power2.out",
        delay: 0.3,
      }
    );
  }, []);

  // Setup Sign Out button hover animation in a separate useEffect
  useEffect(() => {
    const logoutBtn = logoutBtnRef.current;
    if (!logoutBtn) return;

    // Set initial state with simple styling
    gsap.set(logoutBtn, {
      border: "2px solid transparent",
      borderRadius: "24px",
      boxSizing: "border-box",
      position: "relative",
      overflow: "visible",
    });

    // Simple hover handlers using GSAP for smooth transitions
    const handleMouseEnter = () => {
      // Border color and background change to orange
      gsap.to(logoutBtn, {
        borderColor: "#FF9933", // Orange border
        backgroundColor: "rgba(255, 153, 51, 0.3)", // More vibrant orange background
        duration: 0.15,
        ease: "power2.out",
      });
    };

    const handleMouseLeave = () => {
      gsap.killTweensOf(logoutBtn);

      // Simple fade out
      gsap.to(logoutBtn, {
        borderColor: "transparent",
        backgroundColor: "rgba(255, 255, 255, 0.12)", // Reset to original background
        duration: 0.15,
        ease: "power2.out",
      });
    };

    // Add event listeners
    logoutBtn.addEventListener("mouseenter", handleMouseEnter);
    logoutBtn.addEventListener("mouseleave", handleMouseLeave);

    // Return cleanup function
    return () => {
      if (logoutBtn) {
        logoutBtn.removeEventListener("mouseenter", handleMouseEnter);
        logoutBtn.removeEventListener("mouseleave", handleMouseLeave);
      }
    };
  }, []);

  // Border animation for active link
  useEffect(() => {
    // Capture current refs to use in cleanup function
    const aboutLink = aboutLinkRef.current;

    // Reset border animation
    if (aboutLink) {
      gsap.set(aboutLink, {
        borderColor: "transparent",
        borderWidth: "2px",
        borderStyle: "solid",
        boxSizing: "border-box",
      });
    }

    // Apply border animation if about page is active
    if (location.pathname === "/about" && aboutLink) {
      const tl = gsap.timeline();

      // Start from bottom
      tl.to(aboutLink, {
        borderBottomColor: "#FFA94D",
        duration: 0.15,
        ease: "power2.inOut",
      })
        // Then left side
        .to(aboutLink, {
          borderLeftColor: "#FFA94D",
          duration: 0.15,
          ease: "power2.inOut",
        })
        // Then top
        .to(aboutLink, {
          borderTopColor: "#FFA94D",
          duration: 0.15,
          ease: "power2.inOut",
        })
        // Then right side
        .to(aboutLink, {
          borderRightColor: "#FFA94D",
          duration: 0.15,
          ease: "power2.inOut",
        });

      // No text glow effect as requested
    }

    // Cleanup function
    return () => {
      if (aboutLink) {
        // Kill all animations
        gsap.killTweensOf(aboutLink);

        // Reset border
        gsap.set(aboutLink, {
          borderColor: "transparent",
          borderWidth: "2px",
          borderStyle: "solid",
          boxSizing: "border-box",
        });

        // No text glow to reset
      }
    };
  }, [location.pathname]);

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
        
        // Set avatar URL
        setAvatarUrl(session.user.user_metadata?.avatar_url || 
                   `https://ui-avatars.com/api/?name=${encodeURIComponent(session.user.email || 'User')}`);
      } else {
        setUser(null);
        setAvatarUrl("");
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
        
        // Set avatar URL
        setAvatarUrl(session.user.user_metadata?.avatar_url || 
                   `https://ui-avatars.com/api/?name=${encodeURIComponent(session.user.email || 'User')}`);
      } else {
        setUser(null);
        setAvatarUrl("");
      }
    });

    return () => {
      subscription.unsubscribe();
    };
  }, []);

  // Close language dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        languageDropdownRef.current &&
        !languageDropdownRef.current.contains(event.target) &&
        languageBtnRef.current &&
        !languageBtnRef.current.contains(event.target)
      ) {
        setIsLanguageDropdownOpen(false);
      }
    };

    if (isLanguageDropdownOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isLanguageDropdownOpen]);

  // Handle language change
  const handleLanguageChange = (newLanguage) => {
    updateLanguage(newLanguage);
    setIsLanguageDropdownOpen(false);
  };

  const languages = [
    { code: "english", label: "English", nativeLabel: "English" },
    { code: "arabic", label: "Arabic", nativeLabel: "العربية" },
  ];

  const handleLogout = async () => {
    // Click animation - faster and smoother
    if (logoutBtnRef.current) {
      gsap.to(logoutBtnRef.current, {
        scale: 0.97,
        duration: 0.07,
        ease: "power2.in",
        onComplete: async () => {
          if (logoutBtnRef.current) {
            gsap.to(logoutBtnRef.current, {
              scale: 1,
              duration: 0.1,
              ease: "power2.out",
            });
          }
          // Sign out from Supabase
          await supabase.auth.signOut();
          navigate("/signin");
        },
      });
    } else {
      // Sign out from Supabase
      await supabase.auth.signOut();
      navigate("/signin");
    }
  };

  const handleLogoClick = () => {
    // Click animation - faster and smoother
    if (logoRef.current) {
      gsap.to(logoRef.current, {
        scale: 0.95,
        duration: 0.07,
        ease: "power2.in",
        onComplete: () => {
          if (logoRef.current) {
            gsap.to(logoRef.current, {
              scale: 1,
              duration: 0.1,
              ease: "power2.out",
            });
          }
          navigate("/home");
        },
      });
    } else {
      navigate("/home");
    }
  };

  return (
    <header
      ref={headerRef}
      className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-4 sm:px-6 py-3 sm:py-4 backdrop-blur-md bg-white/5 border-b border-white/10"
    >
      {/* Logo */}
      <div
        ref={logoRef}
        onClick={handleLogoClick}
        className="cursor-pointer flex items-center space-x-2 sm:space-x-3 transition-transform duration-150 ease-out hover:scale-105"
      >
        <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-gradient-to-br from-[#FF9933] to-[#e94560] flex items-center justify-center">
          <span className="text-white font-bold text-sm sm:text-base">G</span>
        </div>
        <h1 className="text-white font-bold text-lg sm:text-xl tracking-wide">
          {t("Gurukul")}
        </h1>
      </div>

      {/* Desktop Navigation */}
      <nav className="hidden md:flex items-center space-x-1">
        <NavLink
          ref={aboutLinkRef}
          to="/about"
          className={({ isActive }) =>
            `px-4 py-2 rounded-lg transition-all duration-200 ${
              isActive
                ? "text-[#FFA94D] bg-white/10"
                : "text-white hover:text-[#FFA94D] hover:bg-white/10"
            }`
          }
        >
          {t("About")}
        </NavLink>
      </nav>

      {/* User Actions */}
      <div className="flex items-center space-x-3">
        {/* Language Switcher */}
        <div className="relative">
          <button
            ref={languageBtnRef}
            onClick={() => setIsLanguageDropdownOpen(!isLanguageDropdownOpen)}
            className="px-3 py-1.5 sm:px-4 sm:py-2 text-white text-sm font-medium rounded-full bg-white/12 hover:bg-white/20 transition-all duration-200 border-2 border-transparent flex items-center space-x-2"
            aria-label="Change language"
          >
            <Globe className="w-4 h-4" />
            <span className="hidden sm:inline">
              {languages.find((lang) => lang.code === language)?.nativeLabel || "English"}
            </span>
            <ChevronDown className={`w-4 h-4 transition-transform duration-200 ${isLanguageDropdownOpen ? "rotate-180" : ""}`} />
          </button>

          {/* Language Dropdown */}
          {isLanguageDropdownOpen && (
            <div
              ref={languageDropdownRef}
              className="absolute right-0 mt-2 w-48 bg-white/10 backdrop-blur-md border border-white/20 rounded-lg shadow-lg overflow-hidden z-50"
              style={{
                animation: "fadeIn 0.2s ease-out",
              }}
            >
              {languages.map((lang) => (
                <button
                  key={lang.code}
                  onClick={() => handleLanguageChange(lang.code)}
                  className={`w-full px-4 py-2.5 text-sm transition-all duration-200 flex items-center justify-between ${
                    language === lang.code
                      ? "bg-[#FF9933]/30 text-[#FFA94D] font-medium"
                      : "text-white hover:bg-white/10"
                  } ${lang.code === "arabic" ? "text-right" : "text-left"}`}
                  dir={lang.code === "arabic" ? "rtl" : "ltr"}
                >
                  <span>{lang.nativeLabel}</span>
                  {language === lang.code && (
                    <span className="text-[#FFA94D]">{lang.code === "arabic" ? "✓" : "✓"}</span>
                  )}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Avatar and Logout for authenticated users */}
        {session && user ? (
          <>
            <div className="hidden sm:flex items-center space-x-3">
              <div className="flex items-center space-x-2">
                {avatarUrl ? (
                  <img
                    src={avatarUrl}
                    alt="User Avatar"
                    className="w-8 h-8 rounded-full object-cover border-2 border-white/20"
                  />
                ) : (
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#FF9933] to-[#e94560] flex items-center justify-center">
                    <span className="text-white font-bold text-xs">
                      {user.user_metadata?.full_name?.charAt(0) ||
                        user.email?.charAt(0) ||
                        "U"}
                    </span>
                  </div>
                )}
                <span className="text-white text-sm font-medium hidden lg:inline">
                  {user.user_metadata?.full_name || user.email}
                </span>
              </div>
            </div>

            <button
              ref={logoutBtnRef}
              onClick={handleLogout}
              className="px-3 py-1.5 sm:px-4 sm:py-2 text-white text-sm font-medium rounded-full bg-white/12 hover:bg-white/20 transition-all duration-200 border-2 border-transparent"
            >
              {t("Sign Out")}
            </button>
          </>
        ) : null}

        {/* Mobile menu button */}
        <button
          onClick={onToggleSidebar}
          className="md:hidden p-2 rounded-lg text-white hover:bg-white/10 transition-colors"
        >
          {sidebarCollapsed ? (
            <Menu className="w-6 h-6" />
          ) : (
            <X className="w-6 h-6" />
          )}
        </button>
      </div>
    </header>
  );
}