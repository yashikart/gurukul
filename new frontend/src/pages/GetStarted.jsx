import React, { useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { Power3, Power4, Back, Elastic } from "gsap";
import {
  FiArrowRight,
  FiBookOpen,
  FiMessageCircle,
  FiFile,
} from "react-icons/fi";
import GlassButton from "../components/GlassButton";

// Register GSAP plugins
gsap.registerPlugin(ScrollTrigger);

export default function GetStarted() {
  const { t } = useTranslation();
  const navigate = useNavigate();

  // Refs for GSAP animations
  const containerRef = useRef(null);
  const titleRef = useRef(null);
  const subtitleRef = useRef(null);
  const descriptionRef = useRef(null);
  const buttonRef = useRef(null);
  const overlayRef = useRef(null);
  const featureCardsRef = useRef([]);

  // GSAP animations
  useEffect(() => {
    // Initial animation timeline
    const tl = gsap.timeline({ defaults: { ease: Power4.easeOut } });

    // Animate background and overlay with a reveal effect
    tl.fromTo(
      overlayRef.current,
      {
        opacity: 0,
        background: "rgba(0, 0, 0, 0)",
      },
      {
        opacity: 1,
        background: "rgba(0, 0, 0, 0.5)",
        duration: 1.2,
      }
    )

      // Animate logo with a bounce effect
      .fromTo(
        ".logo-text",
        {
          opacity: 0,
          x: -50,
        },
        {
          opacity: 1,
          x: 0,
          duration: 0.8,
          ease: Back.easeOut.config(1.7),
        },
        "-=0.8"
      )

      // Animate the Get Started button with a reveal and bounce
      .fromTo(
        buttonRef.current,
        {
          opacity: 0,
          scale: 0.8,
          x: 50,
        },
        {
          opacity: 1,
          scale: 1,
          x: 0,
          duration: 0.8,
          ease: Back.easeOut.config(1.7),
        },
        "-=0.8"
      )

      // Animate the main title with a split character effect
      .fromTo(
        titleRef.current,
        {
          opacity: 0,
          y: 50,
          skewY: 5,
        },
        {
          opacity: 1,
          y: 0,
          skewY: 0,
          duration: 1,
          ease: Power3.easeOut,
        },
        "-=0.4"
      )

      // Animate the subtitle with a gradient reveal
      .fromTo(
        subtitleRef.current,
        {
          opacity: 0,
          y: 30,
          backgroundSize: "0% 100%",
        },
        {
          opacity: 1,
          y: 0,
          backgroundSize: "100% 100%",
          duration: 1.2,
          ease: Power3.easeOut,
        },
        "-=0.8"
      )

      // Animate the description paragraph with a fade-in
      .fromTo(
        descriptionRef.current,
        {
          opacity: 0,
          y: 20,
        },
        {
          opacity: 1,
          y: 0,
          duration: 0.8,
          ease: Power3.easeOut,
        },
        "-=0.9"
      );

    // Create a separate timeline for feature cards with staggered animations
    const featuresTl = gsap.timeline({
      defaults: { ease: Back.easeOut.config(1.7) },
      delay: 0.5,
    });

    // Animate each feature card with a staggered bounce effect
    featuresTl.fromTo(
      featureCardsRef.current,
      {
        opacity: 0,
        y: 50,
        scale: 0.9,
        rotation: -2,
      },
      {
        opacity: 1,
        y: 0,
        scale: 1,
        rotation: 0,
        duration: 0.8,
        stagger: 0.15,
      }
    );

    // Animate the feature icons with a bounce and rotation
    featuresTl.fromTo(
      ".feature-icon",
      {
        scale: 0,
        rotation: -30,
      },
      {
        scale: 1,
        rotation: 0,
        duration: 0.6,
        stagger: 0.15,
        ease: Elastic.easeOut.config(1, 0.5),
      },
      "-=1.2"
    );

    // Store references to elements for cleanup
    const featureCards = [...featureCardsRef.current];
    const buttonElement = buttonRef.current;

    // Add continuous subtle floating animation to feature cards
    featureCards.forEach((card, index) => {
      gsap.to(card, {
        y: -5 + (index % 2) * 10,
        duration: 2 + index * 0.2,
        repeat: -1,
        yoyo: true,
        ease: "sine.inOut",
        delay: index * 0.2,
      });
    });

    
    // Create event handlers for feature cards
    const cardEnterHandlers = [];
    const cardLeaveHandlers = [];

    // Add hover effects for feature cards
    featureCards.forEach((card, index) => {
      // Create named handlers so we can properly remove them later
      const handleCardEnter = () => {
        gsap.to(card, {
          y: -15,
          scale: 1.05,
          boxShadow: "0 15px 30px rgba(255, 153, 51, 0.3)",
          duration: 0.3,
          ease: Power3.easeOut,
        });

        // Also animate the icon inside
        const icon = card.querySelector(".feature-icon");
        if (icon) {
          gsap.to(icon, {
            scale: 1.2,
            rotation: 5,
            duration: 0.5,
            ease: Elastic.easeOut.config(1.5, 0.5),
          });
        }
      };

      const handleCardLeave = () => {
        gsap.to(card, {
          y: 0,
          scale: 1,
          boxShadow: "0 8px 24px rgba(255, 153, 51, 0.15)",
          duration: 0.3,
          ease: Power3.easeOut,
        });

        // Reset the icon animation
        const icon = card.querySelector(".feature-icon");
        if (icon) {
          gsap.to(icon, {
            scale: 1,
            rotation: 0,
            duration: 0.3,
            ease: Power3.easeOut,
          });
        }
      };

      // Store handlers for cleanup
      cardEnterHandlers[index] = handleCardEnter;
      cardLeaveHandlers[index] = handleCardLeave;

      // Add event listeners
      card.addEventListener("mouseenter", handleCardEnter);
      card.addEventListener("mouseleave", handleCardLeave);
    });

    return () => {
      // Clean up all event listeners

      // Remove event listeners from feature cards
      featureCards.forEach((card, index) => {
        if (card) {
          card.removeEventListener("mouseenter", cardEnterHandlers[index]);
          card.removeEventListener("mouseleave", cardLeaveHandlers[index]);
        }
      });

      // Kill all animations
      tl.kill();
      featuresTl.kill();
      gsap.killTweensOf(featureCards);
      gsap.killTweensOf(".feature-icon");
    };
  }, []);

  // Handle Get Started button click with animation
  const handleGetStarted = () => {
    localStorage.setItem("gurukul_visited", "true");

    // Create a dramatic exit animation
    const exitTl = gsap.timeline({
      onComplete: () => navigate("/signin"),
    });

    // First, scale up and fade out the button with a flash effect
    exitTl
      .to(buttonRef.current.querySelector("button"), {
        scale: 1.5,
        boxShadow: "0 0 50px rgba(255, 153, 51, 0.9)",
        opacity: 0,
        duration: 0.5,
        ease: Power3.easeInOut,
      })

      // Animate out the feature cards with a staggered effect
      .to(
        featureCardsRef.current,
        {
          opacity: 0,
          y: -50,
          scale: 0.8,
          rotation: -5,
          duration: 0.6,
          stagger: 0.08,
          ease: Power3.easeInOut,
        },
        "-=0.3"
      )

      // Animate out the title, subtitle and description with a dramatic effect
      .to(
        [titleRef.current, subtitleRef.current, descriptionRef.current],
        {
          opacity: 0,
          y: -30,
          scale: 0.95,
          stagger: 0.08,
          duration: 0.5,
          ease: Power3.easeInOut,
        },
        "-=0.5"
      )

      // Finally, fade out the overlay with a flash effect
      .to(
        overlayRef.current,
        {
          opacity: 0,
          duration: 0.5,
          ease: Power4.easeInOut,
        },
        "-=0.3"
      );
  };

  return (
    <div
      ref={containerRef}
      style={{
        width: "100%",
        height: "100vh",
        overflow: "hidden",
        position: "relative",
        backgroundImage: 'url(/bg/bg.png)',
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
        backgroundAttachment: 'fixed'
      }}
    >

      {/* Background overlay */}
      <div
        ref={overlayRef}
        style={{
          position: "fixed",
          inset: 0,
          backgroundColor: "rgba(0, 0, 0, 0.5)",
          zIndex: 1,
        }}
      ></div>

      {/* Content Container */}
      <div
        style={{
          position: "relative",
          zIndex: 2,
          height: "100vh",
          display: "flex",
          flexDirection: "column",
          padding: "2rem",
        }}
      >
        {/* Header */}
        <header
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: "2rem",
          }}
        >
          <h1
            className="logo-text"
            style={{
              fontFamily: "Nunito, sans-serif",
              fontSize: "2rem",
              fontWeight: "bold",
              color: "white",
              textShadow: "0 2px 4px rgba(0,0,0,0.3)",
            }}
          >
            Gurukul
          </h1>

          <div ref={buttonRef}>
            <GlassButton
              icon={FiArrowRight}
              variant="primary"
              onClick={handleGetStarted}
              className="hover-effect"
            >
              {t("Get Started")}
            </GlassButton>
          </div>
        </header>

        {/* Main Content */}
        <main
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
            alignItems: "center",
            textAlign: "center",
          }}
        >
          {/* Hero Section */}
          <div style={{ maxWidth: "800px", marginBottom: "3rem" }}>
            <h1
              ref={titleRef}
              style={{
                fontSize: "3.5rem",
                fontWeight: "800",
                color: "white",
                marginBottom: "1rem",
                fontFamily: "Nunito, sans-serif",
                textShadow: "0 2px 4px rgba(0,0,0,0.3)",
              }}
            >
              {t("Welcome to Gurukul")}
            </h1>

            <h2
              ref={subtitleRef}
              style={{
                fontSize: "1.8rem",
                background: "linear-gradient(90deg, #FF9933, #FFD700)",
                WebkitBackgroundClip: "text",
                backgroundClip: "text",
                color: "transparent",
                marginBottom: "1.5rem",
              }}
            >
              {t("Where Ancient Wisdom Meets Modern Technology")}
            </h2>

            <p
              ref={descriptionRef}
              style={{
                fontSize: "1.2rem",
                color: "rgba(255, 255, 255, 0.8)",
                maxWidth: "700px",
                margin: "0 auto",
              }}
            >
              {t("Enhance your learning experience with AI-powered tools, personalized study plans, and interactive content designed to help you excel in your academic journey.")}
            </p>
          </div>

          {/* Feature Cards */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))",
              gap: "1.5rem",
              width: "100%",
              maxWidth: "1200px",
            }}
          >
            {/* Feature 1 */}
            <div
              ref={(el) => (featureCardsRef.current[0] = el)}
              style={{
                background: "linear-gradient(135deg, rgba(255,255,255,0.28) 0%, rgba(255,255,255,0.18) 100%)",
                backdropFilter: "blur(14px)",
                WebkitBackdropFilter: "blur(14px)",
                border: "1px solid rgba(255,255,255,0.35)",
                borderRadius: "1rem",
                padding: "1.5rem",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                textAlign: "center",
                boxShadow: "0 8px 24px rgba(255, 153, 51, 0.15)",
                transition: "transform 0.3s ease, box-shadow 0.3s ease",
              }}
              onMouseEnter={(e) => {
                gsap.to(e.currentTarget, {
                  y: -5,
                  boxShadow: "0 12px 28px rgba(255, 153, 51, 0.25)",
                  duration: 0.3,
                });
              }}
              onMouseLeave={(e) => {
                gsap.to(e.currentTarget, {
                  y: 0,
                  boxShadow: "0 8px 24px rgba(255, 153, 51, 0.15)",
                  duration: 0.3,
                });
              }}
            >
              <div
                className="feature-icon"
                style={{
                  width: "3rem",
                  height: "3rem",
                  borderRadius: "50%",
                  background: "linear-gradient(135deg, #FF9933, #FFD700)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  marginBottom: "1rem",
                  fontSize: "1.5rem",
                  color: "white",
                }}
              >
                <FiBookOpen />
              </div>
              <h3
                style={{
                  fontSize: "1.2rem",
                  fontWeight: "bold",
                  color: "white",
                  marginBottom: "0.5rem",
                }}
              >
                {t("Interactive Subjects")}
              </h3>
              <p style={{ color: "rgba(255, 255, 255, 0.8)" }}>
                {t("Explore subjects with interactive lessons and 3D visualizations.")}
              </p>
            </div>

            {/* Feature 2 */}
            <div
              ref={(el) => (featureCardsRef.current[1] = el)}
              style={{
                background: "linear-gradient(135deg, rgba(255,255,255,0.28) 0%, rgba(255,255,255,0.18) 100%)",
                backdropFilter: "blur(14px)",
                WebkitBackdropFilter: "blur(14px)",
                border: "1px solid rgba(255,255,255,0.35)",
                borderRadius: "1rem",
                padding: "1.5rem",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                textAlign: "center",
                boxShadow: "0 8px 24px rgba(255, 153, 51, 0.15)",
                transition: "transform 0.3s ease, box-shadow 0.3s ease",
              }}
              onMouseEnter={(e) => {
                gsap.to(e.currentTarget, {
                  y: -5,
                  boxShadow: "0 12px 28px rgba(255, 153, 51, 0.25)",
                  duration: 0.3,
                });
              }}
              onMouseLeave={(e) => {
                gsap.to(e.currentTarget, {
                  y: 0,
                  boxShadow: "0 8px 24px rgba(255, 153, 51, 0.15)",
                  duration: 0.3,
                });
              }}
            >
              <div
                className="feature-icon"
                style={{
                  width: "3rem",
                  height: "3rem",
                  borderRadius: "50%",
                  background: "linear-gradient(135deg, #FF9933, #FFD700)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  marginBottom: "1rem",
                  fontSize: "1.5rem",
                  color: "white",
                }}
              >
                <FiMessageCircle />
              </div>
              <h3
                style={{
                  fontSize: "1.2rem",
                  fontWeight: "bold",
                  color: "white",
                  marginBottom: "0.5rem",
                }}
              >
                {t("AI Guru Assistant")}
              </h3>
              <p style={{ color: "rgba(255, 255, 255, 0.8)" }}>
                {t("Chat with our AI tutor for personalized guidance and support.")}
              </p>
            </div>

            {/* Feature 3 */}
            <div
              ref={(el) => (featureCardsRef.current[2] = el)}
              style={{
                background: "linear-gradient(135deg, rgba(255,255,255,0.28) 0%, rgba(255,255,255,0.18) 100%)",
                backdropFilter: "blur(14px)",
                WebkitBackdropFilter: "blur(14px)",
                border: "1px solid rgba(255,255,255,0.35)",
                borderRadius: "1rem",
                padding: "1.5rem",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                textAlign: "center",
                boxShadow: "0 8px 24px rgba(255, 153, 51, 0.15)",
                transition: "transform 0.3s ease, box-shadow 0.3s ease",
              }}
              onMouseEnter={(e) => {
                gsap.to(e.currentTarget, {
                  y: -5,
                  boxShadow: "0 12px 28px rgba(255, 153, 51, 0.25)",
                  duration: 0.3,
                });
              }}
              onMouseLeave={(e) => {
                gsap.to(e.currentTarget, {
                  y: 0,
                  boxShadow: "0 8px 24px rgba(255, 153, 51, 0.15)",
                  duration: 0.3,
                });
              }}
            >
              <div
                className="feature-icon"
                style={{
                  width: "3rem",
                  height: "3rem",
                  borderRadius: "50%",
                  background: "linear-gradient(135deg, #FF9933, #FFD700)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  marginBottom: "1rem",
                  fontSize: "1.5rem",
                  color: "white",
                }}
              >
                <FiFile />
              </div>
              <h3
                style={{
                  fontSize: "1.2rem",
                  fontWeight: "bold",
                  color: "white",
                  marginBottom: "0.5rem",
                }}
              >
                {t("Smart Learning Tools")}
              </h3>
              <p style={{ color: "rgba(255, 255, 255, 0.8)" }}>
                {t("Analyze documents and generate insights to enhance learning.")}
              </p>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}