import React, { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import gsap from "gsap";
import { useGSAP } from "../hooks/useGSAP";
import GlassButton from "../components/GlassButton";
import {
  FiBookOpen,
  FiMessageCircle,
  FiLayout,
  FiFileText,
  FiVideo,
  FiUsers,
  FiFile,
} from "react-icons/fi";
import {
  setIsChatOpen,
  addChatMessage,
  setChatHistory,
  selectSelectedAvatar,
  selectFavorites,
} from "../store/avatarSlice";

export default function Home() {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { t } = useTranslation();
  const selectedAvatar = useSelector(selectSelectedAvatar);
  const favorites = useSelector(selectFavorites);

  // State for tooltip
  const [hoveredButton, setHoveredButton] = useState(null);
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });

  // Ref to track hover timeout for debouncing
  const hoverTimeoutRef = useRef(null);

  // Refs for GSAP animations
  const containerRef = useRef(null);
  const titleRef = useRef(null);
  const subtitleRef = useRef(null);
  const buttonsRef = useRef(null);

  // Function to get the avatar's display name
  const getAvatarName = () => {
    if (!selectedAvatar) return "your AI assistant";

    try {
      // Try to get custom name from localStorage
      const customNames = JSON.parse(localStorage.getItem('avatar-custom-names') || '{}');
      if (customNames[selectedAvatar.id]) {
        return customNames[selectedAvatar.id];
      }

      // If no custom name, use the avatar's name property or generate default
      if (selectedAvatar.name) {
        return selectedAvatar.name;
      }

      // Find the index in favorites to generate default name
      const avatarIndex = favorites.findIndex(fav => fav.id === selectedAvatar.id);
      return avatarIndex >= 0 ? `Guru${avatarIndex + 1}` : "Brihaspati";
    } catch (error) {
      console.error('Error getting avatar name:', error);
      return selectedAvatar.name || "your AI assistant";
    }
  };

  // Function to format messages for avatar chat
  const formatAvatarMessage = (message, role = "assistant", model = "system") => ({
    id: Date.now() + Math.random(),
    role,
    content: message,
    model,
    timestamp: new Date().toISOString(),
    type: "avatar_chat",
  });

  // Tooltip descriptions for hover functionality
  const getTooltipDescription = (section) => {
    const descriptions = {
      dashboard: t("Track your learning progress, set goals, view achievements, and get AI-powered insights to stay motivated in your learning journey."),
      subjects: t("Explore any topic with custom AI-generated lessons. From mathematics to literature, get structured content tailored to your interests."),
      summarizer: t("Upload documents and get instant AI-powered summaries. Extract key points, generate study notes, and ask questions about your content."),
      chatbot: t("Have unlimited conversations with AI. Multiple models available, chat history saved, and context-aware discussions on any topic."),
      tests: t("Assess your knowledge with custom quizzes and practice exams. Get instant feedback and track your performance over time."),
      lectures: t("Access curated educational video content from expert instructors. Interactive players with organized, topic-based learning materials.")
    };

    return descriptions[section] || t("Explore this section of Gurukul!");
  };

  // Navigation descriptions for avatar chat (keeping original for avatar interactions)
  const getNavigationDescription = (section) => {
    const avatarName = getAvatarName();

    const descriptions = {
      dashboard: `📊 **Dashboard - Your Learning Command Center**

Hi! I'm ${avatarName}. The Dashboard is your personal learning analytics hub where you can:

• **Track Progress** - See your daily, weekly, and monthly learning statistics
• **Set Goals** - Establish daily learning targets and monitor completion
• **View Achievements** - Unlock badges and milestones as you progress
• **Learning Streaks** - Maintain consistent study habits with streak tracking
• **Performance Insights** - Get AI-powered recommendations based on your activity

Perfect for staying motivated and organized in your learning journey!`,

      subjects: `📚 **Subjects - Explore Any Topic**

${avatarName} here! The Subjects section is your gateway to unlimited learning:

• **Generate Custom Lessons** - Enter any topic and get structured, comprehensive content
• **Academic Coverage** - From mathematics to literature, science to history
• **Interactive Learning** - Engaging explanations with examples and key concepts
• **Progress Tracking** - Monitor your exploration across different subjects
• **Personalized Recommendations** - AI suggests topics based on your interests

Whether you're studying for exams or exploring new interests, this is your starting point!`,

      summarizer: `📄 **Summarizer - AI-Powered Document Analysis**

Hey there! ${avatarName} speaking. The Summarizer transforms how you process information:

• **Upload Any Document** - PDFs, Word docs, text files, and more
• **Instant Summaries** - Get key points and main ideas in seconds
• **Multiple AI Models** - Choose from Grok, GPT-4, Claude, or Gemini
• **Smart Analysis** - Extract conclusions, methodology, and important details
• **Study Notes Generation** - Convert complex documents into digestible notes
• **Q&A Mode** - Ask specific questions about your uploaded content

Perfect for research, studying, and quickly understanding complex materials!`,

      chatbot: `💬 **Chatbot - Your Full AI Conversation Partner**

${avatarName} here! The Chatbot is where we can have deep, extended conversations:

• **Unlimited Discussions** - No topic is off-limits, ask me anything
• **Multiple AI Models** - Switch between different AI personalities and capabilities
• **Chat History** - All conversations are saved and searchable
• **Context Awareness** - I remember our previous discussions
• **Export Conversations** - Save important discussions as PDFs or text
• **Session Management** - Organize conversations by topic or date

This is where our real learning partnership begins - let's dive deep into any subject!`,

      tests: `📝 **Tests - Assess Your Knowledge**

Hi! ${avatarName} here. The Tests section helps you evaluate and improve your understanding:

• **Subject-Specific Quizzes** - Test knowledge in focused topic areas
• **Practice Exams** - Full-length assessments to simulate real testing conditions
• **Instant Feedback** - Get detailed explanations for correct and incorrect answers
• **Performance Analytics** - Track scores and identify areas for improvement
• **Custom Assessments** - Create personalized tests based on your study materials
• **Progress Monitoring** - See how your knowledge improves over time

Great for exam preparation and validating your learning progress!`,

      lectures: `🎥 **Lectures - Educational Video Content**

${avatarName} speaking! The Lectures section provides rich multimedia learning:

• **Curated Video Library** - High-quality educational content across subjects
• **Expert Instructors** - Learn from professionals and academic experts
• **Interactive Players** - Full video controls with pause, rewind, and speed adjustment
• **Organized by Topic** - Easy browsing through categorized content
• **Self-Paced Learning** - Watch at your own speed and convenience
• **Supplementary Materials** - Additional resources to enhance video content

Perfect for visual learners and those who prefer structured, presentation-style education!`
    };

    return descriptions[section] || `Let me help you explore this section of Gurukul!`;
  };

  // Handle tooltip hover
  const handleTooltipHover = (section, event) => {
    const buttonRect = event.currentTarget.getBoundingClientRect();

    // Use viewport coordinates for fixed positioning to avoid layout shifts
    const viewportX = buttonRect.left + buttonRect.width / 2;
    const viewportY = buttonRect.top;

    // Determine if this is a bottom row button (chatbot, tests, lectures)
    const bottomRowButtons = ['chatbot', 'tests', 'lectures'];
    const isBottomRow = bottomRowButtons.includes(section);

    setTooltipPosition({
      x: viewportX,
      y: isBottomRow ? buttonRect.bottom + 10 : viewportY - 10,
      isBottomRow: isBottomRow
    });
    setHoveredButton(section);
  };

  // Handle tooltip leave
  const handleTooltipLeave = () => {
    setHoveredButton(null);
  };

  // Handle hover on navigation items with debouncing (for avatar chat)
  const handleNavigationHover = (section) => {
    // Clear any existing timeout
    if (hoverTimeoutRef.current) {
      clearTimeout(hoverTimeoutRef.current);
    }

    // Set a small delay to prevent rapid-fire messages
    hoverTimeoutRef.current = setTimeout(() => {
      // Open the avatar chat interface
      dispatch(setIsChatOpen(true));

      // Get the description for this section
      const description = getNavigationDescription(section);

      // Create a fresh chat with just the hover description
      const descriptionMessage = formatAvatarMessage(description, "assistant", "hover-description");

      // Set the chat history to only contain this description message
      dispatch(setChatHistory([descriptionMessage]));
    }, 300); // 300ms delay
  };

  // Initialize GSAP animations
  useGSAP(() => {
    // Create a timeline for sequential animations
    const tl = gsap.timeline({ defaults: { ease: "power3.out" } });

    // Title animation with text reveal effect
    const titleText = titleRef.current.textContent;
    titleRef.current.innerHTML = "";

    // Split text into characters for animation
    const chars = titleText.split("");
    chars.forEach((char) => {
      const span = document.createElement("span");
      span.textContent = char === " " ? "\u00A0" : char;
      span.style.display = "inline-block";
      span.style.opacity = 0;
      titleRef.current.appendChild(span);
    });

    // Animate the title characters
    tl.to(titleRef.current.children, {
      opacity: 1,
      y: 0,
      stagger: 0.05,
      duration: 0.8,
      ease: "power2.out",
    });

    // Animate subtitle
    tl.fromTo(
      subtitleRef.current,
      { opacity: 0, y: 20 },
      { opacity: 1, y: 0, duration: 0.6 },
      "-=0.3" // Start slightly before the title animation finishes
    );

    // Animate buttons
    tl.fromTo(
      buttonsRef.current.children,
      { opacity: 0, y: 20 },
      { opacity: 1, y: 0, stagger: 0.1, duration: 0.6 },
      "-=0.3"
    );


  }, []);

  useEffect(() => {
    const handler = (e) => {
      if (e.deltaY > 0) {
        // Animate out before navigating
        const tl = gsap.timeline({
          onComplete: () => navigate("/chatbot"),
        });

        tl.to(
          [
            titleRef.current,
            subtitleRef.current,
            buttonsRef.current,
          ],
          {
            opacity: 0,
            y: -30,
            stagger: 0.05,
            duration: 0.4,
          }
        );
      }
    };
    window.addEventListener("wheel", handler);
    return () => window.removeEventListener("wheel", handler);
  }, [navigate]);

  // Cleanup hover timeout on unmount
  useEffect(() => {
    return () => {
      if (hoverTimeoutRef.current) {
        clearTimeout(hoverTimeoutRef.current);
      }
    };
  }, []);

  const handleNavigate = (path) => {
    // Animate out before navigating
    const tl = gsap.timeline({
      onComplete: () => navigate(path),
    });

    tl.to(
      [
        titleRef.current,
        subtitleRef.current,
        buttonsRef.current,
      ],
      {
        opacity: 0,
        y: -30,
        stagger: 0.05,
        duration: 0.4,
      }
    );
  };

  return (
    <div
      ref={containerRef}
      className="relative z-10 flex flex-col items-center justify-center w-full px-4 h-auto md:h-[100dvh]"
    >
      <div className="text-center space-y-8">
        <h1
          ref={titleRef}
          className="text-6xl md:text-7xl font-extrabold text-white"
          style={{
            fontFamily: "Nunito, sans-serif",
            textShadow: "0 2px 8px rgba(0, 0, 0, 0.7)"
          }}
        >
          {t("Welcome to Gurukul")}
        </h1>

        <p
          ref={subtitleRef}
          className="text-xl md:text-2xl text-white/95 max-w-3xl mx-auto font-medium"
          style={{
            textShadow: "0 1px 4px rgba(0, 0, 0, 0.6)"
          }}
        >
          {t("Your intelligent learning companion for lifelong growth and discovery")}
        </p>

        <div
          ref={buttonsRef}
          className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6 mt-12 w-full max-w-5xl mx-auto relative"
        >
          {/* First row */}
          <GlassButton
            icon={FiLayout}
            variant="primary"
            className="h-20 text-xl font-bold px-8 py-4 shadow-2xl"
            onClick={() => handleNavigate("/dashboard")}
            onMouseEnter={(e) => handleTooltipHover("dashboard", e)}
            onMouseLeave={handleTooltipLeave}
          >
            {t("Dashboard")}
          </GlassButton>

          <GlassButton
            icon={FiBookOpen}
            variant="primary"
            className="h-20 text-xl font-bold px-8 py-4 shadow-2xl"
            onClick={() => handleNavigate("/subjects")}
            onMouseEnter={(e) => handleTooltipHover("subjects", e)}
            onMouseLeave={handleTooltipLeave}
          >
            {t("Subjects")}
          </GlassButton>

          <GlassButton
            icon={FiFile}
            variant="primary"
            className="h-20 text-xl font-bold px-8 py-4 shadow-2xl"
            onClick={() => handleNavigate("/learn")}
            onMouseEnter={(e) => handleTooltipHover("summarizer", e)}
            onMouseLeave={handleTooltipLeave}
          >
            {t("Summarizer")}
          </GlassButton>

          {/* Second row */}
          <GlassButton
            icon={FiMessageCircle}
            variant="primary"
            className="h-20 text-xl font-bold px-8 py-4 shadow-2xl"
            onClick={() => handleNavigate("/chatbot")}
            onMouseEnter={(e) => handleTooltipHover("chatbot", e)}
            onMouseLeave={handleTooltipLeave}
          >
            {t("Chatbot")}
          </GlassButton>

          <GlassButton
            icon={FiFileText}
            variant="primary"
            className="h-20 text-xl font-bold px-8 py-4 shadow-2xl"
            onClick={() => handleNavigate("/test")}
            onMouseEnter={(e) => handleTooltipHover("tests", e)}
            onMouseLeave={handleTooltipLeave}
          >
            {t("Test")}
          </GlassButton>

          <GlassButton
            icon={FiVideo}
            variant="primary"
            className="h-20 text-xl font-bold px-8 py-4 shadow-2xl"
            onClick={() => handleNavigate("/lectures")}
            onMouseEnter={(e) => handleTooltipHover("lectures", e)}
            onMouseLeave={handleTooltipLeave}
          >
            {t("Lectures")}
          </GlassButton>

          {/* Third row */}
        </div>




      </div>

      {/* Portal-based tooltip to prevent layout shifts */}
      {hoveredButton && createPortal(
        <div
          className="fixed z-[9999] px-5 py-4 backdrop-blur-md text-white text-sm rounded-2xl shadow-2xl border border-white/30 max-w-sm pointer-events-none transition-all duration-300 ease-out"
          style={{
            left: `${tooltipPosition.x}px`,
            top: `${tooltipPosition.y}px`,
            transform: tooltipPosition.isBottomRow ? 'translate(-50%, 0%)' : 'translate(-50%, -100%)',
            background: 'linear-gradient(135deg, rgba(0, 0, 0, 0.7) 0%, rgba(0, 0, 0, 0.5) 50%, rgba(255, 255, 255, 0.1) 100%)',
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.6), 0 0 0 1px rgba(255, 255, 255, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.3)',
            position: 'fixed',
            zIndex: 9999,
          }}
        >
          <div className="text-center leading-relaxed font-medium text-white">
            {getTooltipDescription(hoveredButton)}
          </div>

          {/* Conditional arrows based on position */}
          {tooltipPosition.isBottomRow ? (
            // Bottom row - arrow pointing up
            <>
              <div
                className="absolute bottom-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-[8px] border-r-[8px] border-b-[8px] border-transparent"
                style={{
                  borderBottomColor: 'rgba(0, 0, 0, 0.7)',
                  filter: 'drop-shadow(0 -2px 4px rgba(0, 0, 0, 0.4))',
                }}
              />
              <div
                className="absolute bottom-full left-1/2 transform -translate-x-1/2 translate-y-[1px] w-0 h-0 border-l-[6px] border-r-[6px] border-b-[6px] border-transparent"
                style={{
                  borderBottomColor: 'rgba(0, 0, 0, 0.5)',
                }}
              />
            </>
          ) : (
            // Top row - arrow pointing down
            <>
              <div
                className="absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-[8px] border-r-[8px] border-t-[8px] border-transparent"
                style={{
                  borderTopColor: 'rgba(0, 0, 0, 0.7)',
                  filter: 'drop-shadow(0 2px 4px rgba(0, 0, 0, 0.4))',
                }}
              />
              <div
                className="absolute top-full left-1/2 transform -translate-x-1/2 -translate-y-[1px] w-0 h-0 border-l-[6px] border-r-[6px] border-t-[6px] border-transparent"
                style={{
                  borderTopColor: 'rgba(0, 0, 0, 0.5)',
                }}
              />
            </>
          )}
        </div>,
        document.body
      )}
    </div>
  );
}
