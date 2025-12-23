import React, { useRef, useEffect } from "react";
import GlassContainer from "../components/GlassContainer";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { TextPlugin } from "gsap/TextPlugin";
import { FiBriefcase, FiBook, FiMonitor } from "react-icons/fi";
import { useTranslation } from "react-i18next";
import "../styles/about.css";

// Register GSAP plugins
gsap.registerPlugin(ScrollTrigger, TextPlugin);

export default function About() {
  const { t } = useTranslation();
  // Main section refs
  const containerRef = useRef(null);
  const contentRef = useRef(null);
  const titleRef = useRef(null);
  const subtitleRef = useRef(null);
  const introRef = useRef(null);

  // Philosophy section refs
  const philosophyTitleRef = useRef(null);
  const philosophyTextRef = useRef(null);

  // Approach section refs
  const approachTitleRef = useRef(null);
  const approachCardsRef = useRef(null);

  // Closing section ref
  const closingRef = useRef(null);

  // Initialize main animations
  useEffect(() => {
    // Create a main timeline
    const mainTl = gsap.timeline();

    // Title animation with gradient effect
    mainTl.fromTo(
      titleRef.current,
      {
        opacity: 0,
        y: -50,
        scale: 0.9,
      },
      {
        opacity: 1,
        y: 0,
        scale: 1,
        duration: 1,
        ease: "power3.out",
        onComplete: () => {
          // Add the class to trigger the underline animation
          titleRef.current.classList.add("animate");
        },
      }
    );

    // Subtitle animation with text reveal
    mainTl.fromTo(
      subtitleRef.current,
      { opacity: 0 },
      {
        opacity: 1,
        duration: 1,
        ease: "power2.out",
      },
      "-=0.5"
    );

    // Intro paragraph animation
    mainTl.fromTo(
      introRef.current,
      { opacity: 0, y: 30 },
      {
        opacity: 1,
        y: 0,
        duration: 0.8,
        ease: "power2.out",
      },
      "-=0.7"
    );

    // Create scroll animations for all sections
    ScrollTrigger.batch(".about-section", {
      interval: 0.1,
      batchMax: 3,
      onEnter: (batch) => {
        gsap.fromTo(
          batch,
          { opacity: 0, y: 50 },
          {
            opacity: 1,
            y: 0,
            stagger: 0.15,
            duration: 0.8,
            ease: "power3.out",
          }
        );
      },
      start: "top 85%",
    });

    // Create scroll animations for cards
    ScrollTrigger.batch(".about-card", {
      interval: 0.1,
      onEnter: (batch) => {
        gsap.fromTo(
          batch,
          { opacity: 0, y: 50, rotateY: -15 },
          {
            opacity: 1,
            y: 0,
            rotateY: 0,
            stagger: 0.1,
            duration: 0.8,
            ease: "back.out(1.7)",
          }
        );
      },
      start: "top 85%",
    });

    // Create scroll animations for timeline items
    ScrollTrigger.batch(".timeline-item", {
      interval: 0.1,
      onEnter: (batch) => {
        gsap.fromTo(
          batch,
          { opacity: 0, scale: 0.8 },
          {
            opacity: 1,
            scale: 1,
            stagger: 0.2,
            duration: 0.6,
            ease: "power2.out",
          }
        );
      },
      start: "top 85%",
    });

    // No special animation for quote (removed)

    // Create a special animation for the closing text
    ScrollTrigger.create({
      trigger: closingRef.current,
      start: "top 85%",
      onEnter: () => {
        gsap.fromTo(
          closingRef.current,
          { opacity: 0, y: 30 },
          {
            opacity: 1,
            y: 0,
            duration: 0.8,
            ease: "power2.out",
          }
        );
      },
      once: true,
    });

    // Cleanup function
    return () => {
      ScrollTrigger.getAll().forEach((trigger) => trigger.kill());
    };
  }, []);

  // Setup card hover animations
  useEffect(() => {
    // Get all cards
    const cards = document.querySelectorAll(".about-card");

    cards.forEach((card) => {
      // Create hover animation
      const hoverTl = gsap.timeline({ paused: true });

      hoverTl.to(card, {
        y: -10,
        scale: 1.02,
        boxShadow:
          "0 20px 30px rgba(0, 0, 0, 0.2), 0 0 15px rgba(255, 153, 51, 0.2)",
        background: "rgba(255, 255, 255, 0.12)",
        duration: 0.3,
        ease: "power2.out",
      });

      // Find the icon in the card
      const icon = card.querySelector(".about-card-icon");
      if (icon) {
        hoverTl.to(
          icon,
          {
            y: -5,
            scale: 1.1,
            color: "#FFD700",
            duration: 0.2,
            ease: "power1.out",
          },
          0
        );
      }

      // Find the title in the card
      const title = card.querySelector(".about-card-title");
      if (title) {
        hoverTl.to(
          title,
          {
            color: "#FFD700",
            duration: 0.2,
            ease: "power1.out",
          },
          0
        );
      }

      // Add event listeners
      card.addEventListener("mouseenter", () => hoverTl.play());
      card.addEventListener("mouseleave", () => hoverTl.reverse());
    });

    // Cleanup function
    return () => {
      cards.forEach((card) => {
        card.removeEventListener("mouseenter", () => {});
        card.removeEventListener("mouseleave", () => {});
      });
    };
  }, []);

  return (
    <GlassContainer>
      <div className="about-container" ref={containerRef}>
        <div className="text-center mb-12" ref={contentRef}>
          <h1
            ref={titleRef}
            className="about-title text-4xl md:text-5xl font-extrabold mb-4"
            style={{
              background: "linear-gradient(to right, #FFFFFF, #FF9933)",
              WebkitBackgroundClip: "text",
              backgroundClip: "text",
              color: "transparent",
            }}
          >
            {t("About Gurukul")}
          </h1>

          <h2
            ref={subtitleRef}
            className="text-xl md:text-2xl font-medium mb-6 text-white/80"
          >
            {t("Where Ancient Wisdom Meets Modern Technology")}
          </h2>

          <p
            ref={introRef}
            className="text-lg md:text-xl font-medium max-w-4xl mx-auto"
            style={{ color: "#FFFFFF" }}
          >
            {t("Gurukul is a modern educational platform inspired by ancient Indian teaching traditions. Our mission is to blend timeless wisdom with cutting-edge technology to create transformative learning experiences.")}
          </p>
        </div>

        {/* Philosophy Section */}
        <div className="about-section" ref={philosophyTitleRef}>
          <h2
            className="text-2xl md:text-3xl font-bold mb-6"
            style={{
              background: "linear-gradient(to right, #FFFFFF, #FF9933)",
              WebkitBackgroundClip: "text",
              backgroundClip: "text",
              color: "transparent",
            }}
          >
            {t("Our Philosophy")}
          </h2>

          <div ref={philosophyTextRef}>
            <p className="text-white/90 mb-4">
              {t("We envision a world where education transcends boundaries, where ancient wisdom and modern technology converge to create immersive, personalized learning experiences that honor the traditional Guru-Shishya relationship.")}
            </p>
            <p className="text-white/90">
              {t("Our approach is rooted in the belief that true education nurtures not just the intellect, but the whole person. We combine the depth of ancient Indian knowledge systems with the accessibility and interactivity of modern digital platforms.")}
            </p>
          </div>
        </div>

        {/* Approach Section */}
        <div className="about-section" ref={approachTitleRef}>
          <h2
            className="text-2xl md:text-3xl font-bold mb-6"
            style={{
              background: "linear-gradient(to right, #FFFFFF, #FF9933)",
              WebkitBackgroundClip: "text",
              backgroundClip: "text",
              color: "transparent",
            }}
          >
            {t("Our Approach")}
          </h2>

          <div
            className="grid grid-cols-1 md:grid-cols-3 gap-8"
            ref={approachCardsRef}
          >
            <div className="about-card">
              <div className="about-card-icon">
                <FiBook />
              </div>
              <h3 className="about-card-title text-xl">{t("Ancient Wisdom")}</h3>
              <p className="about-card-content">
                {t("We draw from centuries of Indian philosophical traditions, presenting timeless knowledge in accessible formats for the modern learner.")}
              </p>
            </div>

            <div className="about-card">
              <div className="about-card-icon">
                <FiBriefcase />
              </div>
              <h3 className="about-card-title text-xl">{t("AI-Powered Learning")}</h3>
              <p className="about-card-content">
                {t("Our platform uses advanced AI to adapt to your learning style and pace, providing a truly personalized experience that evolves with you.")}
              </p>
            </div>

            <div className="about-card">
              <div className="about-card-icon">
                <FiMonitor />
              </div>
              <h3 className="about-card-title text-xl">{t("Immersive Technology")}</h3>
              <p className="about-card-content">
                {t("Through 3D visualization and interactive elements, we create engaging learning environments that inspire curiosity and deep understanding.")}
              </p>
            </div>
          </div>
        </div>

        {/* Closing Section */}
        <div
          ref={closingRef}
          className="text-center mt-16 mb-8 max-w-3xl mx-auto"
        >
          <p className="text-lg text-white/90 font-medium">
            {t("Join us on this journey of discovery and growth as we explore the treasures of knowledge together. At Gurukul, we believe that learning is a lifelong journey, and we're here to guide you every step of the way.")}
          </p>
        </div>
      </div>
    </GlassContainer>
  );
}
