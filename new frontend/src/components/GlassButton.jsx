import React, { useRef, forwardRef } from "react";
import gsap from "gsap";
import { useGSAP } from "../hooks/useGSAP";

/**
 * GlassButton - Modern glassmorphic button with GSAP animations
 * Props: icon, children, className, variant, ...props
 */
const GlassButton = forwardRef(function GlassButton({
  icon: Icon,
  children,
  className = "",
  variant = "default", // default, primary, accent
  ...props
}, ref) {
  // Refs for GSAP animations
  const buttonRef = useRef(null);
  const iconRef = useRef(null);
  const textRef = useRef(null);

  // Define variant-specific styles
  const getStyles = () => {
    const baseStyles = {
      background: "rgba(255, 255, 255, 0.15)",
      backdropFilter: "blur(12px)",
      WebkitBackdropFilter: "blur(12px)",
      border: "1px solid rgba(255, 255, 255, 0.25)",
      boxShadow: "0 4px 12px rgba(0, 0, 0, 0.15)",
      color: "#fff",
    };

    switch (variant) {
      case "primary":
        return {
          ...baseStyles,
          background: "linear-gradient(135deg, #FF8C00 0%, #FFA500 50%, #FF4500 100%)",
          backdropFilter: "blur(16px)",
          WebkitBackdropFilter: "blur(16px)",
          border: "2px solid #FF8C00",
          boxShadow: "0 8px 32px rgba(255, 140, 0, 0.6), 0 0 0 1px rgba(255, 165, 0, 0.8), inset 0 1px 0 rgba(255, 255, 255, 0.8)",
          color: "#FFFFFF",
          fontWeight: 700,
          textShadow: "0 2px 4px rgba(0, 0, 0, 0.5)",
        };
      case "accent":
        return {
          ...baseStyles,
          background: "linear-gradient(135deg, rgba(93, 0, 30, 0.4) 0%, rgba(139, 69, 19, 0.3) 50%, rgba(160, 82, 45, 0.2) 100%)",
          backdropFilter: "blur(16px)",
          WebkitBackdropFilter: "blur(16px)",
          border: "2px solid rgba(160, 82, 45, 0.6)",
          boxShadow: "0 8px 32px rgba(93, 0, 30, 0.25), 0 0 0 1px rgba(160, 82, 45, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.4)",
          color: "#FFFFFF",
          fontWeight: 700,
          textShadow: "0 2px 4px rgba(0, 0, 0, 0.3)",
        };
      default:
        return {
          ...baseStyles,
          background: "linear-gradient(135deg, rgba(255, 255, 255, 0.25) 0%, rgba(255, 255, 255, 0.15) 50%, rgba(255, 255, 255, 0.1) 100%)",
          backdropFilter: "blur(16px)",
          WebkitBackdropFilter: "blur(16px)",
          border: "2px solid rgba(255, 255, 255, 0.4)",
          boxShadow: "0 8px 32px rgba(255, 255, 255, 0.15), 0 0 0 1px rgba(255, 255, 255, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.3)",
          color: "#FFFFFF",
          fontWeight: 600,
          textShadow: "0 2px 4px rgba(0, 0, 0, 0.3)",
        };
    }
  };

  // Initialize GSAP animations
  useGSAP(() => {
    // Initial entrance animation
    gsap.fromTo(
      buttonRef.current,
      { opacity: 0, y: 10, scale: 0.95 },
      { opacity: 1, y: 0, scale: 1, duration: 0.5, ease: "power2.out" }
    );
  }, []);

  // Handle hover animations
  const handleMouseEnter = (e) => {
    // Enhanced button glow effect
    gsap.to(buttonRef.current, {
      scale: 1.08,
      boxShadow:
        variant === "primary"
          ? "0 12px 40px rgba(255, 140, 0, 0.9), 0 0 30px rgba(255, 165, 0, 1), inset 0 1px 0 rgba(255, 255, 255, 0.9)"
          : variant === "accent"
          ? "0 12px 40px rgba(93, 0, 30, 0.5), 0 0 20px rgba(160, 82, 45, 0.6), inset 0 1px 0 rgba(255, 255, 255, 0.6)"
          : "0 12px 40px rgba(255, 255, 255, 0.4), 0 0 20px rgba(255, 255, 255, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.6)",
      background:
        variant === "primary"
          ? "linear-gradient(135deg, #FFB84D 0%, #FFCC66 50%, #FF6633 100%)"
          : variant === "accent"
          ? "linear-gradient(135deg, rgba(93, 0, 30, 0.6) 0%, rgba(139, 69, 19, 0.5) 50%, rgba(160, 82, 45, 0.4) 100%)"
          : "linear-gradient(135deg, rgba(255, 255, 255, 0.4) 0%, rgba(255, 255, 255, 0.3) 50%, rgba(255, 255, 255, 0.2) 100%)",
      duration: 0.3,
      ease: "power2.out",
    });

    // Enhanced icon and text animations
    if (iconRef.current) {
      gsap.to(iconRef.current, {
        scale: 1.2,
        rotate: 8,
        filter: "drop-shadow(0 0 8px rgba(255, 255, 255, 0.8))",
        duration: 0.3,
        ease: "power2.out",
      });
    }

    gsap.to(textRef.current, {
      scale: 1.05,
      filter: "drop-shadow(0 0 6px rgba(255, 255, 255, 0.6))",
      duration: 0.3,
      ease: "power2.out",
    });

    // Call custom onMouseEnter handler if provided
    if (props.onMouseEnter) {
      props.onMouseEnter(e);
    }
  };

  // Handle mouse leave animations
  const handleMouseLeave = (e) => {
    // Reset button to original enhanced state
    gsap.to(buttonRef.current, {
      scale: 1,
      boxShadow:
        variant === "primary"
          ? "0 8px 32px rgba(255, 140, 0, 0.6), 0 0 0 1px rgba(255, 165, 0, 0.8), inset 0 1px 0 rgba(255, 255, 255, 0.8)"
          : variant === "accent"
          ? "0 8px 32px rgba(93, 0, 30, 0.25), 0 0 0 1px rgba(160, 82, 45, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.4)"
          : "0 8px 32px rgba(255, 255, 255, 0.15), 0 0 0 1px rgba(255, 255, 255, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.3)",
      background:
        variant === "primary"
          ? "linear-gradient(135deg, #FF8C00 0%, #FFA500 50%, #FF4500 100%)"
          : variant === "accent"
          ? "linear-gradient(135deg, rgba(93, 0, 30, 0.4) 0%, rgba(139, 69, 19, 0.3) 50%, rgba(160, 82, 45, 0.2) 100%)"
          : "linear-gradient(135deg, rgba(255, 255, 255, 0.25) 0%, rgba(255, 255, 255, 0.15) 50%, rgba(255, 255, 255, 0.1) 100%)",
      duration: 0.3,
      ease: "power2.out",
    });

    // Reset icon and text
    if (iconRef.current) {
      gsap.to(iconRef.current, {
        scale: 1,
        rotate: 0,
        filter: "none",
        duration: 0.3,
        ease: "power2.out",
      });
    }

    gsap.to(textRef.current, {
      scale: 1,
      filter: "none",
      duration: 0.3,
      ease: "power2.out",
    });

    // Call custom onMouseLeave handler if provided
    if (props.onMouseLeave) {
      props.onMouseLeave(e);
    }
  };

  // Handle click animation
  const handleClick = (e) => {
    // Click animation
    gsap.to(buttonRef.current, {
      scale: 0.95,
      duration: 0.15,
      ease: "power2.inOut",
      onComplete: () => {
        gsap.to(buttonRef.current, {
          scale: 1,
          duration: 0.15,
          ease: "power2.inOut",
        });
      },
    });

    // If there's an onClick handler in props, call it
    if (props.onClick) {
      props.onClick(e);
    }
  };

  // Extract custom handlers from props to avoid passing them to DOM
  const { onMouseEnter: customOnMouseEnter, onMouseLeave: customOnMouseLeave, onClick: customOnClick, ...restProps } = props;

  return (
    <button
      ref={ref || buttonRef}
      className={`
        flex items-center justify-center gap-2 rounded-xl
        px-6 py-3 font-semibold
        focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#FFD700]/30 focus:ring-offset-transparent
        ${className}
      `}
      style={{
        ...getStyles(),
        fontFamily: "Nunito, sans-serif",
      }}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      onClick={handleClick}
      {...restProps}
    >
      {Icon && <Icon className="w-5 h-5" />}
      <span ref={textRef}>{children}</span>
    </button>
  );
});

export default GlassButton;
