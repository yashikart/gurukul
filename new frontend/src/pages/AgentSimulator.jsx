import React, { useState, useEffect, useRef } from "react";
import { useSelector } from "react-redux";
import GlassContainer from "../components/GlassContainer";
import { toast } from "react-hot-toast";
import gsap from "gsap";
import { useTranslation } from "react-i18next";
import "../styles/agentDashboard.css";
import "../styles/skewFill.css";
import "../styles/pdfUpload.css";
import {
  useSendAgentMessageMutation,
  useStartAgentSimulationMutation,
  useStopAgentSimulationMutation,
  useResetAgentSimulationMutation,
} from "../api/agentApiSlice";
import {
  useSendLearningDataMutation,
  useLazyGetLearningTaskStatusQuery,
  useUploadPdfForChatMutation,
  useNotifyPdfRemovedMutation,
} from "../api/learningApiSlice";
import {
  useCreateLessonMutation,
} from "../api/subjectsApiSlice";
import {
  useGenerateEnhancedLessonMutation,
  useGetIntegrationStatusQuery,
  formatEnhancedLessonData,
  useAskEdumentorMutation,
} from "../api/orchestrationApiSlice";
import {
  useStartFinancialSimulationMutation,
  useLazyGetSimulationStatusQuery,
  useLazyGetSimulationResultsByTaskIdQuery,
  useCreateFinancialForecastMutation,
} from "../api/financialApiSlice";
import { selectUser, selectUserId } from "../store/authSlice";
import { selectAudioEnabled, selectAudioVolume } from "../store/settingsSlice";
import agentLogsService from "../services/agentLogsService";
import { API_BASE_URL, CHAT_API_BASE_URL, WELLNESS_API_BASE_URL } from "../config";
import {
  Play,
  Pause,
  RotateCcw,
  Cpu,
  BrainCircuit,
  Bot,
  Sparkles,
  MessageSquare,
  ArrowRight,
  ArrowLeft,
  BookOpen,
  Book,
  DollarSign,
  Heart,
  Target,
  Clock,
  Plus,
  Minus,
  Wallet,
  AlertTriangle,
  User,
  ShoppingBag,
  FileText,
  Pin,
  X,
  Activity,
  Settings,
} from "lucide-react";

// Unique ID generator to prevent duplicate keys
let messageIdCounter = 0;
const generateUniqueId = () => {
  messageIdCounter += 1;
  return `${Date.now()}-${messageIdCounter}`;
};

export default function AgentSimulator() {
  const { t, i18n } = useTranslation();
  const user = useSelector(selectUser);
  const userId = useSelector(selectUserId) || "guest-user";
  const audioEnabled = useSelector(selectAudioEnabled);
  const audioVolumeFromStore = useSelector(selectAudioVolume);

  // API mutations
  const [sendAgentMessage] = useSendAgentMessageMutation();
  const [startAgentSimulation] = useStartAgentSimulationMutation();
  const [stopAgentSimulation] = useStopAgentSimulationMutation();
  const [resetAgentSimulation] = useResetAgentSimulationMutation();

  // Learning API mutations and queries
  const [sendLearningData] = useSendLearningDataMutation();
  const [getLearningTaskStatus] = useLazyGetLearningTaskStatusQuery();
  const [uploadPdfForChat] = useUploadPdfForChatMutation();
  const [notifyPdfRemoved] = useNotifyPdfRemovedMutation();

  // Financial API mutations and queries
  const [startFinancialSimulation] = useStartFinancialSimulationMutation();
  const [getSimulationStatus] = useLazyGetSimulationStatusQuery();
  const [getSimulationResultsByTaskId] =
    useLazyGetSimulationResultsByTaskIdQuery();
  const [createFinancialForecast] = useCreateFinancialForecastMutation();

  // EduMentor API mutations and queries
  const [createLesson] = useCreateLessonMutation();
  const [generateEnhancedLesson] = useGenerateEnhancedLessonMutation();
  const [askEdumentor] = useAskEdumentorMutation();
  const { data: integrationStatus } = useGetIntegrationStatusQuery();

  // Wellness Bot state - converted to profile structure like EduMentor
  const [wellnessProfile, setWellnessProfile] = useState({
    wellnessType: "emotional", // "emotional" or "financial"
    moodScore: 5,
    stressLevel: 3,
    wellnessGoals: [],
    preferredActivities: [],
    stressTriggers: [],
    copingStrategies: [],
  });
  
  // Legacy wellness state (kept for backward compatibility if needed)
  const [wellnessQuery, setWellnessQuery] = useState("");
  const [isWellnessLoading, setIsWellnessLoading] = useState(false);
  const [wellnessResponse, setWellnessResponse] = useState(null);

  // Custom audio player state
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentAudio, setCurrentAudio] = useState(null);
  const [audioVolume] = useState(audioVolumeFromStore);
  const [isMuted] = useState(!audioEnabled);
  const audioRef = useRef(null);

  const [agents, setAgents] = useState([
    {
      id: 1,
      name: "EduMentor",
      type: "education",
      status: "idle",
      color: "#10B981", // Green
      icon: BookOpen,
      confidence: 0.85,
      goal: "Knowledge transfer",
      description: "Specialized in educational content and academic guidance",
    },
    {
      id: 2,
      name: "FinancialCrew",
      type: "financial",
      status: "idle",
      color: "#3B82F6", // Blue
      icon: DollarSign,
      confidence: 0.78,
      goal: "Financial literacy",
      description: "Expert in financial planning and investment strategies",
    },
    {
      id: 3,
      name: "WellnessBot",
      type: "wellness",
      status: "idle",
      color: "#F97316", // Orange
      icon: Heart,
      confidence: 0.92,
      goal: "Health optimization",
      description: "Focused on mental and physical wellbeing advice",
    },
  ]);

  // Financial simulation form state
  const [financialProfile, setFinancialProfile] = useState({
    name: "",
    monthlyIncome: "",
    expenses: [{ id: 1, name: "", amount: "" }],
    financialGoal: "",
    financialType: "Conservative", // Can be "Conservative", "Moderate", or "Aggressive"
    riskLevel: "Low", // Can be "Low", "Medium", or "High"
  });

  // EduMentor form state (same inputs as Subjects.jsx)
  const [eduMentorProfile, setEduMentorProfile] = useState({
    selectedSubject: "",
    topic: "",
    includeWikipedia: true,
    useKnowledgeStore: true,
    useOrchestration: true,
  });

  // EduMentor lesson state
  const [lessonData, setLessonData] = useState(null);
  const [isGeneratingLesson, setIsGeneratingLesson] = useState(false);
  const [lessonTaskId, setLessonTaskId] = useState(null);

  // Safely render activity content that may be an object or string
  const renderActivityContent = (activity) => {
    if (!activity) return null;
    if (typeof activity === 'string') {
      return <p className="text-white/90 leading-relaxed">{activity}</p>;
    }
    if (Array.isArray(activity)) {
      return (
        <ul className="list-disc list-inside text-white/90 leading-relaxed">
          {activity.map((item, idx) => (
            <li key={idx}>{typeof item === 'string' ? item : JSON.stringify(item)}</li>
          ))}
        </ul>
      );
    }
    if (typeof activity === 'object') {
      const { title, description, instructions, materials_needed, materials, steps } = activity;
      return (
        <div className="space-y-3">
          {title && <p className="text-white font-semibold">{title}</p>}
          {description && <p className="text-white/90 leading-relaxed">{description}</p>}

          {Array.isArray(instructions) && instructions.length > 0 && (
            <div>
              <p className="text-white/80 font-medium">{t("Instructions")}:</p>
              <ol className="list-decimal list-inside text-white/90 space-y-1 mt-1">
                {instructions.map((ins, idx) => (
                  <li key={idx}>{ins}</li>
                ))}
              </ol>
            </div>
          )}
          {typeof instructions === 'string' && instructions && (
            <p className="text-white/90">{instructions}</p>
          )}

          {Array.isArray(steps) && steps.length > 0 && (
            <div>
              <p className="text-white/80 font-medium">{t("Steps")}:</p>
              <ol className="list-decimal list-inside text-white/90 space-y-1 mt-1">
                {steps.map((s, idx) => (
                  <li key={idx}>{s}</li>
                ))}
              </ol>
            </div>
          )}

          {Array.isArray(materials_needed) && materials_needed.length > 0 && (
            <div>
              <p className="text-white/80 font-medium">{t("Materials Needed")}:</p>
              <ul className="list-disc list-inside text-white/90 space-y-1 mt-1">
                {materials_needed.map((m, idx) => (
                  <li key={idx}>{m}</li>
                ))}
              </ul>
            </div>
          )}
          {Array.isArray(materials) && materials.length > 0 && (
            <div>
              <p className="text-white/80 font-medium">{t("Materials")}:</p>
              <ul className="list-disc list-inside text-white/90 space-y-1 mt-1">
                {materials.map((m, idx) => (
                  <li key={idx}>{m}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      );
    }
    return <p className="text-white/90 leading-relaxed">{String(activity)}</p>;
  };

  // Safely render question content that may be an object or string
  const renderQuestionContent = (question) => {
    if (!question) return null;
    if (typeof question === 'string') {
      return <p className="text-white/90 leading-relaxed italic">"{question}"</p>;
    }
    if (Array.isArray(question)) {
      return (
        <ul className="list-disc list-inside text-white/90">
          {question.map((q, idx) => (
            <li key={idx}>{typeof q === 'string' ? q : JSON.stringify(q)}</li>
          ))}
        </ul>
      );
    }
    if (typeof question === 'object') {
      const text = question.text || question.question || question.prompt || question.title || '';
      const options = question.options || question.choices || [];
      return (
        <div className="space-y-3">
          {text && (
            <p className="text-white/90 leading-relaxed italic">"{text}"</p>
          )}
          {Array.isArray(options) && options.length > 0 && (
            <ul className="list-disc list-inside text-white/90">
              {options.map((opt, idx) => (
                <li key={idx}>{typeof opt === 'string' ? opt : JSON.stringify(opt)}</li>
              ))}
            </ul>
          )}
        </div>
      );
    }
    return <p className="text-white/90 leading-relaxed">{String(question)}</p>;
  };

  // Financial simulation processing state
  const [isProcessingSimulation, setIsProcessingSimulation] = useState(false);
  const [simulationTaskId, setSimulationTaskId] = useState(null);
  const [simulationProgress, setSimulationProgress] = useState(0);
  const [isLoadingResults, setIsLoadingResults] = useState(false);
  const refreshIntervalRef = useRef(null);

  const [isSimulating, setIsSimulating] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [messages, setMessages] = useState([]);
  const [userInput, setUserInput] = useState("");
  const [selectedPdfs, setSelectedPdfs] = useState([]);
  const [activePdfId, setActivePdfId] = useState(null);
  const fileInputRef = useRef(null);

  const [isTimelineOpen, setIsTimelineOpen] = useState(true);

  // State for financial simulation results
  const [simulationResults, setSimulationResults] = useState(null);
  const [currentMonth, setCurrentMonth] = useState(1); // Track which month to display

  const containerRef = useRef(null);
  const messagesEndRef = useRef(null);
  const timelineRef = useRef(null);

  // Scroll to bottom of messages
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);



  // Handle PDF file selection
  const handleFileChange = async (event) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    const file = files[0];

    // Validate file type
    if (file.type !== "application/pdf") {
      toast.error(t("Please select a PDF file"));
      return;
    }

    // Validate file size (10MB max)
    if (file.size > 10 * 1024 * 1024) {
      toast.error(t("File size should be less than 10MB"));
      return;
    }

    // Show loading toast
    const loadingToast = toast.loading(t("Uploading") + ` ${file.name}...`);

    try {
      // Get the user ID from Redux store
      let userId = "guest-user";
      if (user && user.id) {
        userId = user.id;
      }

      // Upload the PDF using RTK Query
      const response = await uploadPdfForChat({
        user_id: userId,
        pdf_file: file,
      }).unwrap();

      // Dismiss loading toast and show success
      toast.dismiss(loadingToast);
      toast.success(`${file.name} ${t("uploaded successfully")}`, {
        icon: "📄",
        duration: 3000,
      });

      // Add the PDF to the selected PDFs list
      const newPdf = {
        id: response.pdf_id,
        name: file.name,
        size: file.size,
      };

      setSelectedPdfs((prev) => [...prev, newPdf]);

      // Set as active PDF if it's the first one
      if (!activePdfId) {
        setActivePdfId(response.pdf_id);
      }
    } catch (error) {
      toast.dismiss(loadingToast);
      toast.error(
        "Error uploading PDF: " + (error.data?.error || error.message)
      );
    }

    // Reset the file input
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  // Handle removing a PDF
  const handleRemovePdf = async (pdfId) => {
    // Get the user ID from Redux store
    let userId = "guest-user";
    if (user && user.id) {
      userId = user.id;
    }

    // Show loading toast
    const loadingToast = toast.loading("Removing PDF...");

    try {
      // Notify the server about PDF removal using RTK Query
      await notifyPdfRemoved({
        user_id: userId,
        pdf_id: pdfId,
      }).unwrap();

      // Update local state
      setSelectedPdfs((prev) => prev.filter((pdf) => pdf.id !== pdfId));

      // If the removed PDF was active, set the first remaining PDF as active
      if (activePdfId === pdfId) {
        const remainingPdfs = selectedPdfs.filter((pdf) => pdf.id !== pdfId);
        setActivePdfId(remainingPdfs.length > 0 ? remainingPdfs[0].id : null);
      }

      // Show success toast
      toast.dismiss(loadingToast);
      toast.success(t("PDF removed successfully"), {
        icon: "🗑️",
        duration: 2000,
      });
    } catch (error) {
      // Still remove the PDF locally even if the server notification fails
      setSelectedPdfs((prev) => prev.filter((pdf) => pdf.id !== pdfId));

      // If the removed PDF was active, set the first remaining PDF as active
      if (activePdfId === pdfId) {
        const remainingPdfs = selectedPdfs.filter((pdf) => pdf.id !== pdfId);
        setActivePdfId(remainingPdfs.length > 0 ? remainingPdfs[0].id : null);
      }

      // Show error toast
      toast.dismiss(loadingToast);
      console.error("Error notifying PDF removal:", error);
      toast.success(t("PDF removed from chat"));
    }
  };

  // Cleanup interval on component unmount
  useEffect(() => {
    // Cleanup function to clear the interval when component unmounts
    return () => {
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current);
        refreshIntervalRef.current = null;
      }
    };
  }, []);

  // Animation for container entrance and skew fill setup
  useEffect(() => {
    // Container entrance animation
    gsap.fromTo(
      containerRef.current,
      { opacity: 0, y: 20 },
      { opacity: 1, y: 0, duration: 0.6, ease: "power2.out" }
    );

    // Set up GSAP animations for skew fill effect
    const agentCards = document.querySelectorAll(".agent-card");

    // Function to create skew fill animation
    const createSkewAnimation = (element) => {
      // Create a pseudo-element for the skew animation
      const skewElement = document.createElement("div");
      skewElement.className = "gsap-skew-element";

      // Add the skew element to the parent
      element.style.position = "relative";
      element.style.overflow = "hidden";
      element.appendChild(skewElement);

      // Check if this is an agent card
      const isAgentCard = element.classList.contains("agent-card");

      // Create a subtle hover effect
      element.addEventListener("mouseenter", () => {
        // Skip animation if this is a selected agent card
        if (isAgentCard && element.classList.contains("selected-agent")) {
          return;
        }

        // First, subtle shadow effect (unless it's already selected)
        // Don't use y transform for insight panels to avoid layout shifts
        if (
          element.classList.contains("insight-panel") ||
          element.classList.contains("insight-card")
        ) {
          gsap.to(element, {
            boxShadow: "0 3px 10px rgba(0, 0, 0, 0.08)",
            duration: 0.3,
            ease: "power2.out",
          });
        } else {
          gsap.to(element, {
            y: isAgentCard ? -2 : -1,
            boxShadow: isAgentCard
              ? "0 5px 15px rgba(0, 0, 0, 0.1)"
              : "0 3px 10px rgba(0, 0, 0, 0.08)",
            duration: 0.3,
            ease: "power2.out",
          });
        }

        // Then, the skew animation
        gsap.fromTo(
          skewElement,
          { left: "-120%", opacity: 0.8, width: "80%" },
          {
            left: "120%",
            opacity: 1,
            width: "80%",
            duration: 0.7,
            ease: "power1.inOut",
          }
        );
      });

      // Reset on mouse leave
      element.addEventListener("mouseleave", () => {
        // Skip animation if this is a selected agent card
        if (isAgentCard && element.classList.contains("selected-agent")) {
          return;
        }

        // Reset position and shadow
        if (
          element.classList.contains("insight-panel") ||
          element.classList.contains("insight-card")
        ) {
          gsap.to(element, {
            boxShadow: "0 0 0 rgba(0, 0, 0, 0)",
            duration: 0.3,
            ease: "power2.out",
          });
        } else {
          gsap.to(element, {
            y: 0,
            boxShadow: "0 0 0 rgba(0, 0, 0, 0)",
            duration: 0.3,
            ease: "power2.out",
          });
        }

        // Reset skew element
        gsap.set(skewElement, { left: "-120%", opacity: 0.8, width: "80%" });
      });

      // Special animation for selected agent cards
      if (isAgentCard) {
        // Create a periodic subtle glow animation for selected cards
        const createSelectedAnimation = () => {
          if (element.classList.contains("selected-agent")) {
            // Subtle pulsing glow effect
            gsap.fromTo(
              skewElement,
              { left: "-120%", opacity: 0.7, width: "80%" },
              {
                left: "120%",
                opacity: 1,
                width: "80%",
                duration: 1.5,
                ease: "power1.inOut",
                onComplete: () => {
                  // Reset and repeat after a delay
                  gsap.set(skewElement, {
                    left: "-120%",
                    opacity: 0.7,
                    width: "80%",
                  });
                  gsap.delayedCall(3, createSelectedAnimation);
                },
              }
            );
          }
        };

        // Set up a mutation observer to watch for class changes
        const observer = new MutationObserver((mutations) => {
          mutations.forEach((mutation) => {
            if (mutation.attributeName === "class") {
              // Check if the selected-agent class was added
              if (element.classList.contains("selected-agent")) {
                createSelectedAnimation();
              }
            }
          });
        });

        // Start observing the element
        observer.observe(element, { attributes: true });
      }
    };

    // Apply to timeline items - we need to target the actual card divs
    document
      .querySelectorAll(".timeline-item > div")
      .forEach(createSkewAnimation);

    // Apply to agent insight panel cards
    document.querySelectorAll(".insight-card").forEach(createSkewAnimation);

    // Apply to the entire insight panel
    document.querySelectorAll(".insight-panel").forEach(createSkewAnimation);

    // Apply to agent cards
    agentCards.forEach(createSkewAnimation);
  }, []);

  // Handle financial profile changes
  const handleFinancialProfileChange = (field, value) => {
    setFinancialProfile((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  // Handle EduMentor profile changes
  const handleEduMentorProfileChange = (field, value) => {
    setEduMentorProfile((prev) => ({
      ...prev,
      [field]: value,
    }));

    // Clear lesson data when subject or topic changes
    if (field === "selectedSubject" || field === "topic") {
      if (lessonData) {
        setLessonData(null);
        setLessonTaskId(null);
      }
    }
  };

  // Handle WellnessBot profile changes
  const handleWellnessProfileChange = (field, value) => {
    setWellnessProfile((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  // Generate lesson using the same logic as Subjects.jsx
  const generateEduMentorLesson = async () => {
    const trimmedSubject = eduMentorProfile.selectedSubject.trim();
    const trimmedTopic = eduMentorProfile.topic.trim();

    // Validate inputs
    if (!trimmedSubject || !trimmedTopic) {
      toast.error(t("Please provide both subject and topic for lesson generation"));
      return;
    }

    setIsGeneratingLesson(true);

    // Set the education agent as active and start simulation mode
    const educationAgent = agents.find(agent => agent.type === "education");
    if (educationAgent) {
      setSelectedAgent(educationAgent.id);
      setIsSimulating(true);

      // Update agent status
      setAgents(prevAgents =>
        prevAgents.map(agent => ({
          ...agent,
          status: agent.type === "education" ? "active" : "idle",
        }))
      );
    }

    try {
      let createResponse;

      // Check if orchestration is available and enabled
      const isOrchestrationAvailable = integrationStatus?.integration_status?.overall_valid &&
                                      integrationStatus?.runtime_status?.orchestration_engine_initialized;

      if (isOrchestrationAvailable && eduMentorProfile.useOrchestration) {
        // Use enhanced lesson generation with orchestration
        console.log("🚀 Using enhanced lesson generation with orchestration...");

        toast.success(
          t("🎯 Enhanced lesson generation started! Using AI orchestration for personalized content."),
          {
            icon: "🚀",
            duration: 4000,
            style: {
              background: 'linear-gradient(135deg, rgba(15, 15, 25, 0.95), rgba(25, 25, 35, 0.95))',
              color: '#fff',
              border: '1px solid rgba(34, 197, 94, 0.3)',
              borderRadius: '12px',
              fontSize: '14px',
              maxWidth: '450px',
              fontWeight: '500',
              boxShadow: '0 0 20px rgba(34, 197, 94, 0.1)',
            },
          }
        );

        createResponse = await generateEnhancedLesson({
          subject: trimmedSubject,
          topic: trimmedTopic,
          user_id: userId,
          use_orchestration: true,
          include_triggers: true,
          include_wikipedia: eduMentorProfile.includeWikipedia,
        });
      } else {
        // Fallback to basic lesson creation
        console.log("📚 Using basic lesson generation...");

        createResponse = await createLesson({
          subject: trimmedSubject,
          topic: trimmedTopic,
          user_id: userId,
          include_wikipedia: eduMentorProfile.includeWikipedia,
          force_regenerate: true,
        });
      }

      console.log("Lesson generation response:", createResponse);

      if (createResponse.error) {
        throw createResponse.error || new Error("Failed to initiate lesson creation");
      }

      // Check if response has task_id (async processing) or lesson data (immediate response)
      const taskId = createResponse.data?.task_id;
      const lessonData = createResponse.data;

      if (taskId) {
        // Async processing - poll for completion
        console.log("Using async lesson generation with task_id:", taskId);
        setLessonTaskId(taskId);

        // Add system message about lesson generation
        setMessages((prev) => [
          ...prev,
          {
            id: generateUniqueId(),
            sender: "system",
            content: `${t("Generating lesson for")} ${trimmedSubject}: ${trimmedTopic}. ${t("This may take a few minutes...")}`,
            timestamp: new Date().toISOString(),
          },
        ]);

        // Poll for lesson completion
        await pollForLessonCompletion(taskId);
      } else if (lessonData && (lessonData.content || lessonData.status === 'success')) {
        // Immediate response - use lesson data directly
        console.log("Using immediate lesson generation response");

        // Add system message about lesson generation
        setMessages((prev) => [
          ...prev,
          {
            id: generateUniqueId(),
            sender: "system",
            content: `${t("Generated lesson for")} ${trimmedSubject}: ${trimmedTopic}`,
            timestamp: new Date().toISOString(),
          },
        ]);

        // Process the lesson data immediately
        await handleLessonCompletion(lessonData);
      } else {
        // Log the response for debugging
        console.error("Unexpected response format:", createResponse);
        throw new Error(`Invalid response format: Expected task_id or lesson data, got: ${JSON.stringify(createResponse.data)}`);
      }

    } catch (error) {
      console.error("Error generating lesson:", error);
      toast.error(`${t("Failed to generate lesson")}: ${error.message || error}`);

      setMessages((prev) => [
        ...prev,
        {
          id: generateUniqueId(),
          sender: "system",
          content: `${t("Failed to generate lesson")}: ${error.message || error}`,
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setIsGeneratingLesson(false);
    }
  };

  // Handle immediate lesson completion (for direct responses without task_id)
  const handleLessonCompletion = async (lessonData) => {
    try {
      console.log("Processing immediate lesson data:", lessonData);

      // Format the lesson data
      let formattedLesson;
      if (integrationStatus?.integration_status?.overall_valid && eduMentorProfile.useOrchestration) {
        formattedLesson = formatEnhancedLessonData(lessonData);
      } else {
        formattedLesson = lessonData;
      }

      // Create a new object to avoid modifying frozen/sealed objects
      // Normalize lesson data structure - map content/text to explanation if needed
      let normalizedLesson = { ...formattedLesson };
      
      if (normalizedLesson && !normalizedLesson.explanation) {
        if (normalizedLesson.content) {
          normalizedLesson = { ...normalizedLesson, explanation: normalizedLesson.content };
        } else if (normalizedLesson.text) {
          normalizedLesson = { ...normalizedLesson, explanation: normalizedLesson.text };
        }
      }

      // Ensure activity is accessible
      if (normalizedLesson && !normalizedLesson.activity && normalizedLesson.enhanced_features?.activity) {
        normalizedLesson = { ...normalizedLesson, activity: normalizedLesson.enhanced_features.activity };
      }

      console.log("Formatted lesson data:", normalizedLesson);
      setLessonData(normalizedLesson);

      // Add success message
      setMessages((prev) => [
        ...prev,
        {
          id: generateUniqueId(),
          sender: "learning-agent",
          agentName: "EduMentor",
          agentColor: "#10B981",
          agentType: "education",
          content: `${t("Lesson generated successfully! Here's your personalized content for")} ${eduMentorProfile.selectedSubject}: ${eduMentorProfile.topic}`,
          isLoading: false,
          timestamp: new Date().toISOString(),
        },
      ]);

      toast.success(t("Lesson generated successfully!"), {
        icon: "📚",
        duration: 4000,
      });

    } catch (error) {
      console.error("Error processing lesson data:", error);
      throw error;
    }
  };

  // Poll for lesson completion using the same approach as Subjects.jsx
  const pollForLessonCompletion = async (taskId, maxAttempts = 60) => {
    let attempts = 0;
    let lessonFound = false;



    while (attempts < maxAttempts && !lessonFound) {
      attempts++;
      console.log(`Polling attempt ${attempts}/${maxAttempts} for task ${taskId}...`);

      // Wait 2 seconds between attempts (lesson generation takes time)
      if (attempts > 1) {
        await new Promise((resolve) => setTimeout(resolve, 2000));
      }

      try {
        // Check task status using the status endpoint (same as Subjects.jsx)
        const statusUrl = `${API_BASE_URL}/lessons/status/${taskId}`;
        console.log(`Polling URL: ${statusUrl}`);

        const statusResponse = await fetch(statusUrl);

        if (!statusResponse.ok) {
          throw new Error(`HTTP ${statusResponse.status}: ${statusResponse.statusText}`);
        }

        const statusData = await statusResponse.json();
        console.log(`Status Response (attempt ${attempts}):`, statusData);

        if (statusData.status === 'completed' && statusData.lesson_data) {
          // Successfully retrieved lesson data
          console.log("Lesson generation completed:", statusData.lesson_data);

          // Format the lesson data
          let formattedLesson;
          if (integrationStatus?.integration_status?.overall_valid && eduMentorProfile.useOrchestration) {
            formattedLesson = formatEnhancedLessonData(statusData.lesson_data);
          } else {
            formattedLesson = statusData.lesson_data;
          }

          // Normalize lesson data structure - map content/text to explanation if needed
          if (formattedLesson && !formattedLesson.explanation) {
            if (formattedLesson.content) {
              formattedLesson.explanation = formattedLesson.content;
            } else if (formattedLesson.text) {
              formattedLesson.explanation = formattedLesson.text;
            }
          }

          // Ensure activity is accessible
          if (formattedLesson && !formattedLesson.activity && formattedLesson.enhanced_features?.activity) {
            formattedLesson.activity = formattedLesson.enhanced_features.activity;
          }

          console.log("Formatted lesson data from polling:", formattedLesson);
          setLessonData(formattedLesson);
          lessonFound = true;

          // Add success message
          setMessages((prev) => [
            ...prev,
            {
              id: generateUniqueId(),
              sender: "learning-agent",
              agentName: "EduMentor",
              agentColor: "#10B981",
              agentType: "education",
              content: `${t("Lesson generated successfully! Here's your personalized content for")} ${eduMentorProfile.selectedSubject}: ${eduMentorProfile.topic}`,
              isLoading: false,
              timestamp: new Date().toISOString(),
            },
          ]);

          toast.success(t("Lesson generated successfully!"), {
            icon: "📚",
            duration: 4000,
          });

          return formattedLesson;
        } else if (statusData.status === 'pending') {
          console.log("Lesson generation pending...");
          // Continue polling
        } else if (statusData.status === 'failed') {
          throw new Error(statusData.error || "Lesson generation failed");
        }
      } catch (pollError) {
        console.log(`Polling attempt ${attempts} failed:`, pollError);
        // Continue polling unless it's the last attempt
        if (attempts === maxAttempts) {
          throw pollError;
        }
      }
    }

    if (!lessonFound) {
      throw new Error("Lesson generation timed out. Please try again.");
    }
  };

  // Handle expense changes
  const handleExpenseChange = (id, field, value) => {
    setFinancialProfile((prev) => ({
      ...prev,
      expenses: prev.expenses.map((expense) =>
        expense.id === id ? { ...expense, [field]: value } : expense
      ),
    }));
  };

  // Add new expense
  const addExpense = () => {
    setFinancialProfile((prev) => ({
      ...prev,
      expenses: [
        ...prev.expenses,
        {
          id: prev.expenses.length + 1,
          name: "",
          amount: "",
        },
      ],
    }));
  };

  // Remove expense
  const removeExpense = (id) => {
    setFinancialProfile((prev) => ({
      ...prev,
      expenses: prev.expenses.filter((expense) => expense.id !== id),
    }));
  };

  // Fetch simulation results from the API
  const fetchSimulationResults = async (isInitialFetch = false) => {
    try {
      setIsLoadingResults(true);

      // Check if we have a simulation task ID
      if (!simulationTaskId) {
        console.log("No simulation task ID available, cannot fetch results");
        setIsLoadingResults(false);
        return;
      }

      console.log("Fetching simulation results for task ID:", simulationTaskId);

      // Call the RTK Query function to get simulation results by task ID
      const response = await getSimulationResultsByTaskId(simulationTaskId).unwrap();

      console.log("Raw simulation results:", response);

      // RTK Query unwrap() already handles the success check
      // Extract the data from the nested response structure
      const responseData = response?.data || {};

      console.log("Extracted data from response:", responseData);

      // Add debugging to understand the structure
      console.log("Processed simulation results structure:", {
        simulated_cashflow: Array.isArray(responseData.simulated_cashflow),
        discipline_report: Array.isArray(responseData.discipline_report),
        goal_status: Array.isArray(responseData.goal_status),
        behavior_tracker: Array.isArray(responseData.behavior_tracker),
        karmic_tracker: Array.isArray(responseData.karmic_tracker),
        financial_strategy: Array.isArray(responseData.financial_strategy),
      });

      // Ensure all expected arrays exist and are arrays
      const safeResults = {
        ...responseData,
        // Include metadata from the response
        task_id: response?.task_id,
        task_status: response?.task_status,
        user_id: response?.user_id,
        status: response?.status,
        ready: response?.ready,
        message: response?.message,
        // Ensure data arrays are properly extracted
        simulated_cashflow: Array.isArray(responseData.simulated_cashflow)
          ? responseData.simulated_cashflow
          : [],
        discipline_report: Array.isArray(responseData.discipline_report)
          ? responseData.discipline_report
          : [],
        goal_status: Array.isArray(responseData.goal_status) ? responseData.goal_status : [],
        behavior_tracker: Array.isArray(responseData.behavior_tracker)
          ? responseData.behavior_tracker
          : [],
        karmic_tracker: Array.isArray(responseData.karmic_tracker)
          ? responseData.karmic_tracker
          : [],
        financial_strategy: Array.isArray(responseData.financial_strategy)
          ? responseData.financial_strategy
          : [],
        person_history: Array.isArray(responseData.person_history)
          ? responseData.person_history
          : [],
        monthly_reflections: Array.isArray(responseData.monthly_reflections)
          ? responseData.monthly_reflections
          : [],
      };

      setSimulationResults(safeResults);

      // Check if the simulation is complete
      const isComplete = checkIfSimulationComplete(safeResults);

      if (isComplete) {
        // If simulation is complete, stop the refresh interval
        setIsProcessingSimulation(false);
        if (refreshIntervalRef.current) {
          clearInterval(refreshIntervalRef.current);
          refreshIntervalRef.current = null;
        }

        // Add a system message about the completed simulation only once
        if (isInitialFetch) {
          // Check if we already have a "results loaded" message
          const hasResultsLoadedMessage = (prev) =>
            prev.some(
              (msg) =>
                msg.sender === "system" &&
                msg.content === "Financial simulation results have been loaded."
            );

          setMessages((prev) => {
            // Only add the message if it doesn't already exist
            if (!hasResultsLoadedMessage(prev)) {
              return [
                ...prev,
                {
                  id: generateUniqueId(),
                  sender: "system",
                  content: "Financial simulation results have been loaded.",
                  timestamp: new Date().toISOString(),
                },
              ];
            }
            return prev;
          });
        }
      } else {
        // If simulation is not complete, ensure the refresh interval is running
        setIsProcessingSimulation(true);
        if (!refreshIntervalRef.current) {
          startRefreshInterval();
        }

        // Only add a processing message on initial fetch and if it doesn't already exist
        if (isInitialFetch) {
          // Check if we already have a processing message
          const hasProcessingMessage = (prev) =>
            prev.some(
              (msg) =>
                msg.sender === "system" &&
                msg.content ===
                  "Financial simulation is processing. Results will update automatically."
            );

          setMessages((prev) => {
            // Only add the message if it doesn't already exist
            if (!hasProcessingMessage(prev)) {
              return [
                ...prev,
                {
                  id: generateUniqueId(),
                  sender: "system",
                  content:
                    "Financial simulation is processing. Results will update automatically.",
                  timestamp: new Date().toISOString(),
                },
              ];
            }
            return prev;
          });
        }
      }

      return safeResults;
    } catch (error) {
      console.error("Failed to fetch simulation results:", error);

      // Only show error toast on initial fetch to avoid spamming
      if (isInitialFetch) {
        toast.error("Could not load simulation results. Please try again.");
      }

      return null;
    } finally {
      setIsLoadingResults(false);
    }
  };

  // Check if the simulation is complete based on the results
  const checkIfSimulationComplete = (results) => {
    // First check if the API explicitly tells us the simulation is complete
    if (results.is_complete === true) {
      return true;
    }

    // Check if the task status is completed
    if (results.task_status === "completed") {
      return true;
    }

    // Consider simulation complete if we have data in all major sections
    // or if we have at least some data and it's been processed

    // Check if we have data in all major sections
    const hasAllSections =
      results.simulated_cashflow?.length > 0 &&
      results.discipline_report?.length > 0 &&
      results.goal_status?.length > 0 &&
      results.financial_strategy?.length > 0 &&
      results.behavior_tracker?.length > 0 &&
      results.karmic_tracker?.length > 0;

    // Check if we have at least some data in any section
    const hasSomeData =
      results.simulated_cashflow?.length > 0 ||
      results.discipline_report?.length > 0 ||
      results.goal_status?.length > 0 ||
      results.financial_strategy?.length > 0 ||
      results.behavior_tracker?.length > 0 ||
      results.karmic_tracker?.length > 0;

    // Check if the data has a processing status
    const processingStatus = results.processing_status || "complete";
    const isProcessingComplete = processingStatus === "complete";

    // Check if progress is 100%
    const isProgressComplete = results.progress === 100;

    return (
      hasAllSections ||
      (hasSomeData && (isProcessingComplete || isProgressComplete))
    );
  };

  // Start the interval to refresh simulation results
  const startRefreshInterval = () => {
    // Clear any existing interval first
    if (refreshIntervalRef.current) {
      clearInterval(refreshIntervalRef.current);
    }

    // Set a new interval to poll for results every 2 seconds
    refreshIntervalRef.current = setInterval(async () => {
      if (isProcessingSimulation) {
        // If we have a task ID, use the new API to check status and get results
        if (simulationTaskId) {
          try {
            // Get the user ID from Supabase auth via Redux store
            let userId = "anonymous-user";
            if (user && user.id) {
              userId = user.id;
            }

            // Check the simulation status using RTK Query
            const statusResponse = await getSimulationStatus(
              simulationTaskId
            ).unwrap();

            if (statusResponse) {
              console.log("Simulation status:", statusResponse.task_status);

              // Update progress if available
              if (statusResponse.progress !== undefined) {
                setSimulationProgress(statusResponse.progress);
              }

              // If the simulation is completed, get the results
              if (statusResponse.task_status === "completed") {
                // Get the results using the task ID with RTK Query
                const resultsResponse = await getSimulationResultsByTaskId(
                  simulationTaskId
                ).unwrap();

                if (resultsResponse) {
                  // Process and store the results with proper data extraction
                  const processedResults = {
                    ...resultsResponse?.data || {},
                    // Include metadata from the response
                    task_id: resultsResponse?.task_id,
                    task_status: resultsResponse?.task_status,
                    user_id: resultsResponse?.user_id,
                    status: resultsResponse?.status,
                    ready: resultsResponse?.ready,
                    message: resultsResponse?.message,
                  };
                  setSimulationResults(processedResults);

                  // Mark simulation as no longer processing
                  setIsProcessingSimulation(false);

                  // Set progress to 100%
                  setSimulationProgress(100);

                  // Clear the interval
                  clearInterval(refreshIntervalRef.current);
                  refreshIntervalRef.current = null;

                  // Show success toast
                  toast.success(
                    t("Financial simulation completed successfully!"),
                    {
                      icon: "💰",
                      duration: 4000,
                    }
                  );

                  // Add a system message about the completed simulation
                  setMessages((prev) => {
                    // Check if we already have a "results loaded" message
                    const hasResultsLoadedMessage = prev.some(
                      (msg) =>
                        msg.sender === "system" &&
                        msg.content ===
                          "Financial simulation results have been loaded."
                    );

                    if (!hasResultsLoadedMessage) {
                      return [
                        ...prev,
                        {
                          id: generateUniqueId(),
                          sender: "system",
                          content:
                            "Financial simulation results have been loaded.",
                          timestamp: new Date().toISOString(),
                        },
                      ];
                    }
                    return prev;
                  });
                }
              }
              // If the simulation is running but has partial results
              else if (
                statusResponse.task_status === "running" &&
                statusResponse.partial_results
              ) {
                // Get the partial results using the task ID with RTK Query
                const resultsResponse = await getSimulationResultsByTaskId(
                  simulationTaskId
                ).unwrap();

                if (resultsResponse) {
                  // Process and store the partial results with proper data extraction
                  const processedResults = {
                    ...resultsResponse?.data || {},
                    // Include metadata from the response
                    task_id: resultsResponse?.task_id,
                    task_status: resultsResponse?.task_status,
                    user_id: resultsResponse?.user_id,
                    status: resultsResponse?.status,
                    ready: resultsResponse?.ready,
                    message: resultsResponse?.message,
                  };
                  setSimulationResults(processedResults);

                  // Keep the simulation processing state active
                  setIsProcessingSimulation(true);
                }
              }
              // If the simulation failed, show an error
              else if (statusResponse.task_status === "failed") {
                toast.error(t("Financial simulation failed. Please try again."));
                setIsProcessingSimulation(false);
                clearInterval(refreshIntervalRef.current);
                refreshIntervalRef.current = null;
              }
              // Otherwise, continue polling
            }
          } catch (error) {
            console.error("Error checking simulation status:", error);
          }
        }
        // Fallback to the old method if we don't have a task ID
        else {
          fetchSimulationResults(false); // false means it's not an initial fetch
        }
      } else {
        // If we're no longer processing, clear the interval
        clearInterval(refreshIntervalRef.current);
        refreshIntervalRef.current = null;
      }
    }, 2000); // 2 seconds
  };

  // Send financial simulation data to the API - Now sends directly to financial endpoint
  const sendFinancialSimulationData = async () => {
    // Show loading state
    setIsLoadingResults(true);
    
    try {

      // Validate required fields
      if (!financialProfile.name || financialProfile.name.trim() === '') {
        toast.error(t('Please enter your name before starting financial simulation'));
        return null;
      }

      if (!financialProfile.monthlyIncome || parseFloat(financialProfile.monthlyIncome) <= 0) {
        toast.error(t('Please enter a valid monthly income before starting financial simulation'));
        return null;
      }

      if (!financialProfile.financialGoal || financialProfile.financialGoal.trim() === '') {
        toast.error(t('Please enter your financial goal before starting financial simulation'));
        return null;
      }

      // Calculate total expenses
      const total_expenses = financialProfile.expenses.reduce(
        (total, expense) => total + (parseFloat(expense.amount) || 0),
        0
      );

      // Format the data according to the Financial Simulator API's expected structure
      const simulationRequest = {
        profile: {
          name: financialProfile.name.trim(),
          monthly_income: parseFloat(financialProfile.monthlyIncome),
          expenses: financialProfile.expenses
            .filter(expense => expense.name && expense.name.trim() !== '' && expense.amount && parseFloat(expense.amount) > 0)
            .map((expense) => ({
              name: expense.name.trim(),
              amount: parseFloat(expense.amount),
            })),
          financial_goal: financialProfile.financialGoal.trim(),
          financial_type: financialProfile.financialType || "Conservative",
          risk_level: financialProfile.riskLevel || "Low",
        },
        simulation_months: 12, // Default to 12 months
        user_id: user?.id || "anonymous-user",
      };

      // Instead of starting simulation, send a message directly to financial endpoint
      const financialAgent = agents.find((a) => a.type === "financial");
      if (!financialAgent) {
        toast.error("Financial agent not found");
        return null;
      }

      // Create a query asking for financial advice based on the profile
      const queryText = `Please provide me with comprehensive financial advice based on my profile. My monthly income is ₹${financialProfile.monthlyIncome}, my expenses total ₹${financialProfile.expenses.reduce((sum, e) => sum + (parseFloat(e.amount) || 0), 0)}, my financial goal is ${financialProfile.financialGoal}, my investment style is ${financialProfile.financialType}, and my risk tolerance is ${financialProfile.riskLevel}.`;

      // Add loading message
      const loadingMessageId = generateUniqueId() + 1;
      const loadingMessage = {
        id: loadingMessageId,
        sender: financialAgent.id,
        agentName: financialAgent.name,
        agentColor: financialAgent.color,
        agentType: financialAgent.type,
        content: "",
        isLoading: true,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, loadingMessage]);

      try {
        // Get current language (map i18n language to backend format)
        const currentLanguage = i18n.language === "ar" ? "arabic" : "english";
        
        // Call the financial endpoint
        const financialPayload = {
          query: queryText,
          user_id: user?.id || "anonymous",
          name: financialProfile.name || undefined,
          monthly_income: parseFloat(financialProfile.monthlyIncome) || undefined,
          financial_goal: financialProfile.financialGoal || undefined,
          financial_type: financialProfile.financialType || undefined,
          risk_level: financialProfile.riskLevel || undefined,
          language: currentLanguage,
        };

        // Add expenses if available
        if (financialProfile.expenses && financialProfile.expenses.length > 0) {
          const validExpenses = financialProfile.expenses
            .filter(exp => exp.name && exp.name.trim() !== '' && exp.amount && parseFloat(exp.amount) > 0)
            .map(exp => ({
              name: exp.name.trim(),
              amount: parseFloat(exp.amount)
            }));
          
          if (validExpenses.length > 0) {
            financialPayload.expenses = validExpenses;
          }
        }

        const response = await fetch(`${WELLNESS_API_BASE_URL}/financial`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Accept": "application/json",
          },
          body: JSON.stringify(financialPayload),
        });

        if (!response.ok) {
          setMessages((prev) => prev.filter((msg) => msg.id !== loadingMessageId));
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        
        // Remove loading message
        setMessages((prev) => prev.filter((msg) => msg.id !== loadingMessageId));

        // Extract response content
        let responseContent = "";
        if (data.response) {
          responseContent = data.response;
        } else if (data.message) {
          responseContent = data.message;
        } else {
          responseContent = "I received your request, but couldn't process it properly. Please try again.";
        }

        if (!responseContent || responseContent.trim().length === 0) {
          throw new Error("Empty response received from financial API");
        }

        // Add agent message with response
        const agentMessage = {
          id: generateUniqueId() + 2,
          sender: financialAgent.id,
          agentName: financialAgent.name,
          agentColor: financialAgent.color,
          agentType: financialAgent.type,
          content: responseContent.trim(),
          timestamp: new Date().toISOString(),
          isLoading: false,
        };
        
        setMessages((prev) => [...prev, agentMessage]);
        
        toast.success(t("Financial guidance received!"), {
          duration: 3000,
        });

        // Start simulation so the UI shows it's active
        setIsSimulating(true);

        return data;
      } catch (error) {
        console.error("Error in FinancialCrew Start button:", error);
        
        // Remove loading message
        setMessages((prev) => prev.filter((msg) => !msg.isLoading || msg.id !== loadingMessageId));
        
        // Show error toast
        toast.error(t("Failed to get financial guidance. Please try again."), {
          duration: 5000,
        });
        
        // Add error message to chat
        setMessages((prev) => [
          ...prev,
          {
            id: generateUniqueId() + 1,
            sender: "system",
            agentName: "System",
            agentColor: "#EF4444",
            agentType: "system",
            content: t("I apologize, but I couldn't process your financial query. Please try again or check your connection."),
            timestamp: new Date().toISOString(),
            isLoading: false,
          },
        ]);
        
        return null;
      }
    } catch (outerError) {
      console.error("Failed to send financial simulation data:", outerError);

      // Enhanced error handling for validation errors
      let errorMessage = "Unknown error occurred";
      
      if (outerError?.data) {
        // Handle API validation errors
        if (outerError.data.detail) {
          if (Array.isArray(outerError.data.detail)) {
            // Pydantic validation errors
            const validationErrors = outerError.data.detail.map(e => {
              const field = e.loc ? e.loc.join('.') : 'unknown field';
              return `${field}: ${e.msg || e.message}`;
            }).join(', ');
            errorMessage = `Validation error: ${validationErrors}`;
          } else {
            errorMessage = outerError.data.detail;
          }
        } else {
          errorMessage = outerError.data.message || JSON.stringify(outerError.data);
        }
      } else if (outerError?.message) {
        errorMessage = outerError.message;
      } else if (typeof outerError === 'string') {
        errorMessage = outerError;
      }

      // Provide more specific error messages
      if (errorMessage.includes("Failed to fetch") || errorMessage.includes("Connection")) {
        toast.error(
          "Could not connect to financial simulation server. Please check if the service is running."
        );
      } else if (errorMessage.includes("timed out")) {
        toast.error(
          "Connection to financial simulation server timed out. Please try again."
        );
      } else if (errorMessage.includes("validation") || errorMessage.includes("field required") || errorMessage.includes("greater than 0")) {
        toast.error(
          `Invalid financial data: ${errorMessage}. Please check your input values.`
        );
      } else {
        toast.error(`Financial simulation error: ${errorMessage}`);
      }

      // Continue with local simulation even if API call fails
      return null;
    } finally {
      setIsLoadingResults(false);
    }
  };

  // Start simulation
  const startSimulation = async () => {
    if (agents.length === 0) {
      toast.error(t("Add at least one agent to start simulation"));
      return;
    }

    setIsSimulating(true);

    // Determine which agent to activate
    let activeAgentId;

    if (selectedAgent) {
      // If an agent is selected, activate only that agent
      activeAgentId = selectedAgent;
    } else {
      // If no agent is selected, activate the first agent
      activeAgentId = agents[0].id;
      // Also set it as selected
      setSelectedAgent(activeAgentId);
    }

    // Update agent statuses - only activate the selected agent
    setAgents(
      agents.map((agent) => ({
        ...agent,
        status: agent.id === activeAgentId ? "active" : "idle",
      }))
    );

    // Add initial system message - reset messages
    const startMessage = {
      id: generateUniqueId(),
      sender: "system",
      content: `${t("Agent simulation started.")} ${
        agents.find((a) => a.id === activeAgentId).name
      } ${t("is active and ready to assist.")}`,
      timestamp: new Date().toISOString(),
    };
    setMessages([startMessage]);

    // Get the active agent
    const activeAgent = agents.find((a) => a.id === activeAgentId);

    // Log agent start in Supabase
    try {
      const userId = user?.id || "guest-user";
      await agentLogsService.logAgentStart({
        userId,
        agentId: activeAgent.id,
        agentName: activeAgent.name,
        agentType: activeAgent.type,
      });
      // Agent start logged successfully
    } catch (error) {
      // Continue with simulation even if logging fails
    }

    // If the financial agent is active, send the financial simulation data and fetch results
    if (activeAgent && activeAgent.type === "financial") {
      // Show refresh note popup so users know results will update
      toast('click referesh spontaniusly so the data will be updated and refreshed', {
        icon: '🔄',
        duration: 6000,
      });
      try {
        await sendFinancialSimulationData();

        // Add a small delay to ensure the backend has processed the data
        setTimeout(async () => {
          try {
            await fetchSimulationResults();
          } catch (error) {
            console.error("Error fetching simulation results:", error);
          }
        }, 2000);
      } catch (error) {
        console.error("Error in financial simulation during startup:", error);
        // Continue with simulation even if financial data sending fails
      }
    }

    // If the education agent is active, validate and start lesson generation
    if (activeAgent && activeAgent.type === "education") {
      // Validate that subject and topic are provided
      if (!eduMentorProfile.selectedSubject.trim() || !eduMentorProfile.topic.trim()) {
        toast.error("Please provide both subject and topic for the learning session");
        setIsSimulating(false);
        // Reset agent status
        setAgents(
          agents.map((agent) => ({
            ...agent,
            status: "idle",
          }))
        );
        return;
      }

      // Add a system message about the learning session starting
      setMessages((prev) => [
        ...prev,
        {
          id: generateUniqueId() + 1,
          sender: "system",
          content: `Learning session started for ${eduMentorProfile.selectedSubject}: ${eduMentorProfile.topic}`,
          timestamp: new Date().toISOString(),
        },
      ]);

      // Start lesson generation
      try {
        await generateEduMentorLesson();
      } catch (error) {
        console.error("Error starting lesson generation:", error);
        toast.error("Failed to start lesson generation. Please try again.");
      }
    }

    // If financial agent is selected, start financial simulation automatically
    if (activeAgent && activeAgent.type === "financial") {
      // Validate financial profile before starting simulation
      if (financialProfile.name && financialProfile.monthlyIncome && financialProfile.financialGoal) {
        // Add a system message about the financial session starting
        setMessages((prev) => [
          ...prev,
          {
            id: generateUniqueId() + 1,
            sender: "system",
            content: `Financial simulation started for ${financialProfile.name}`,
            timestamp: new Date().toISOString(),
          },
        ]);

        // Start financial simulation
        try {
          await sendFinancialSimulationData();
        } catch (error) {
          console.error("Error starting financial simulation:", error);
          toast.error("Failed to start financial simulation. Please try again.");
        }
      } else {
        toast.info("Please fill in your financial profile (name, income, and goal) before starting simulation.");
      }
    }

    // Call the API to start the simulation
    try {
      // Include financial profile data if the financial agent is selected
      const payload = {
        agentId: activeAgentId,
        userId: user?.id || "anonymous-user", // Use Supabase user ID or fallback to anonymous user
      };

      // Add financial profile data if the financial agent is active
      if (activeAgent && activeAgent.type === "financial") {
        // Create a copy of the financial profile without the uniqueId field
        // as it will be handled by the backend
        const { uniqueId: _uniqueId, ...financialProfileData } =
          financialProfile;
        payload.financialProfile = financialProfileData;
      }

      // Add EduMentor profile data if the education agent is active
      if (activeAgent && activeAgent.type === "education") {
        payload.eduMentorProfile = eduMentorProfile;
      }

      // Add WellnessBot profile data if the wellness agent is active
      if (activeAgent && activeAgent.type === "wellness") {
        payload.wellnessProfile = {
          wellnessType: wellnessProfile.wellnessType,
          moodScore: wellnessProfile.moodScore,
          stressLevel: wellnessProfile.stressLevel,
          wellnessGoals: wellnessProfile.wellnessGoals,
          preferredActivities: wellnessProfile.preferredActivities,
          stressTriggers: wellnessProfile.stressTriggers,
          copingStrategies: wellnessProfile.copingStrategies,
        };
      }

      await startAgentSimulation(payload).unwrap();
      toast.success("Simulation started");
    } catch (error) {
      console.error("Failed to start simulation:", error);

      // Check for 404 error
      if (error?.status === 404) {
        // Add system message about the error
        setMessages((prev) => [
          ...prev,
          {
            id: generateUniqueId(),
            sender: "system",
            content:
              "The simulation server is currently unavailable. Running in local mode.",
            timestamp: new Date().toISOString(),
          },
        ]);

        toast.error("Simulation server unavailable. Running in local mode.");
      } else {
        // For other errors, just show a toast but continue with local simulation
        toast.success("Simulation started in local mode");
      }

      // Continue with local simulation even if API call fails
    }
  };

  // Stop simulation
  const stopSimulation = async () => {
    setIsSimulating(false);

    // Find the active agent before updating statuses
    const activeAgent = agents.find((a) => a.status === "active");

    // Update agent statuses
    setAgents(
      agents.map((agent) => ({
        ...agent,
        status: "idle",
      }))
    );

    // Add system message
    setMessages((prev) => [
      ...prev,
      {
        id: generateUniqueId(),
        sender: "system",
        content: "Simulation paused.",
        timestamp: new Date().toISOString(),
      },
    ]);

    // Log agent stop in Supabase
    if (activeAgent) {
      try {
        const userId = user?.id || "guest-user";
        await agentLogsService.logAgentStop({
          userId,
          agentId: activeAgent.id,
        });
        console.log(
          `Logged agent stop: ${activeAgent.name} (${activeAgent.id})`
        );
      } catch (error) {
        console.error("Error logging agent stop:", error);
        // Continue with simulation even if logging fails
      }
    }

    // Call the API to stop the simulation
    try {
      if (activeAgent) {
        await stopAgentSimulation({
          agentId: activeAgent.id,
          userId: user?.id || "anonymous-user", // Use Supabase user ID or fallback to anonymous user
        }).unwrap();
      }
      toast.success("Simulation paused");
    } catch (error) {
      console.error("Failed to stop simulation:", error);

      // Check for 404 error
      if (error?.status === 404) {
        // Just log the error, no need to show a message to the user since we're already in local mode
        console.log(
          "Simulation server unavailable. Already running in local mode."
        );
      } else {
        // For other errors, just show a toast
        toast.success("Simulation paused in local mode");
      }

      // Continue with local simulation even if API call fails
    }
  };

  // Reset simulation
  const resetSimulation = async () => {
    setIsSimulating(false);
    setMessages([]);

    // Reset agent statuses
    setAgents(
      agents.map((agent) => ({
        ...agent,
        status: "idle",
      }))
    );

    // Log agent reset in Supabase
    try {
      const userId = user?.id || "anonymous-user";
      await agentLogsService.logAgentReset({ userId });
      console.log(`Logged agent reset for user: ${userId}`);
    } catch (error) {
      console.error("Error logging agent reset:", error);
      // Continue with simulation even if logging fails
    }

    // Call the API to reset the simulation
    try {
      await resetAgentSimulation({
        userId: user?.id || "anonymous-user", // Use Supabase user ID or fallback to anonymous user
      }).unwrap();
      toast.success(t("Simulation reset"));
    } catch (error) {
      console.error("Failed to reset simulation:", error);

      // Check for 404 error
      if (error?.status === 404) {
        // Just log the error, no need to show a message to the user since we're already in local mode
        console.log(
          t("Simulation server unavailable. Already running in local mode.")
        );
        toast.success(t("Simulation reset in local mode"));
      } else {
        // For other errors, just show a toast
        toast.success(t("Simulation reset in local mode"));
      }

      // Continue with local simulation even if API call fails
    }
  };

  // Handle wellness query - using dedicated wellness API endpoint
  const handleWellnessQuery = async () => {
    console.log("handleWellnessQuery called", { wellnessQuery, wellnessProfile });
    
    if (!wellnessQuery.trim()) {
      toast.error(t("Please enter your wellness concern"));
      return;
    }

    setIsWellnessLoading(true);
    console.log("Starting wellness query with:", { wellnessQuery, wellnessType: wellnessProfile.wellnessType });

    try {
      // Build wellness query with profile context
      let queryText = wellnessQuery;
      
      // Add wellness profile context to the query for better guidance
      if (wellnessProfile.wellnessType === "emotional") {
        const moodDescription = wellnessProfile.moodScore <= 3 ? "very low" : 
                               wellnessProfile.moodScore <= 5 ? "low" : 
                               wellnessProfile.moodScore <= 7 ? "moderate" : "good";
        const stressDescription = wellnessProfile.stressLevel <= 3 ? "low stress" : 
                                 wellnessProfile.stressLevel <= 5 ? "moderate stress" : 
                                 wellnessProfile.stressLevel <= 7 ? "high stress" : "very high stress";
        
        let contextInfo = `\n\nContext: My mood score is ${wellnessProfile.moodScore}/10 (${moodDescription}) and stress level is ${wellnessProfile.stressLevel}/10 (${stressDescription}).`;
        
        if (wellnessProfile.wellnessGoals.length > 0) {
          contextInfo += ` My wellness goals: ${wellnessProfile.wellnessGoals.join(", ")}.`;
        }
        if (wellnessProfile.stressTriggers.length > 0) {
          contextInfo += ` Things that stress me: ${wellnessProfile.stressTriggers.join(", ")}.`;
        }
        if (wellnessProfile.copingStrategies.length > 0) {
          contextInfo += ` What helps me cope: ${wellnessProfile.copingStrategies.join(", ")}.`;
        }
        
        queryText = wellnessQuery + contextInfo;
      } else {
        // Financial wellness context
        if (wellnessProfile.wellnessGoals.length > 0) {
          queryText = wellnessQuery + `\n\nContext: My financial goals: ${wellnessProfile.wellnessGoals.join(", ")}.`;
        }
      }

      // Add user message to chat first
      const userMessage = {
        id: generateUniqueId(),
        sender: "user",
        content: wellnessQuery,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMessage]);

      // Add loading message
      const loadingMessageId = generateUniqueId() + 1;
      const loadingMessage = {
        id: loadingMessageId,
        sender: "wellness-agent",
        agentName: "WellnessBot",
        agentColor: "#F97316",
        agentType: "wellness",
        content: "",
        isLoading: true,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, loadingMessage]);

      // Get current language (map i18n language to backend format)
      const currentLanguage = i18n.language === "ar" ? "arabic" : "english";

      // Call the dedicated wellness endpoint
      const wellnessUrl = new URL(`${WELLNESS_API_BASE_URL}/wellness`);
      wellnessUrl.searchParams.append("query", queryText);
      wellnessUrl.searchParams.append("user_id", userId || "anonymous");
      wellnessUrl.searchParams.append("language", currentLanguage);
      
      const response = await fetch(wellnessUrl.toString(), {
        method: "GET",
        headers: {
          "Accept": "application/json",
        },
      });

      if (!response.ok) {
        setMessages((prev) => prev.filter((msg) => msg.id !== loadingMessageId));
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      console.log("Wellness API Response:", data);
      
      // Remove loading message
      setMessages((prev) => prev.filter((msg) => msg.id !== loadingMessageId));

      // Extract response content from the wellness API response
      let responseContent = "";
      if (data.response) {
        responseContent = data.response;
      } else if (data.message) {
        responseContent = data.message;
      } else {
        console.warn("Unexpected wellness API response format:", data);
        responseContent = "I received your wellness query, but couldn't process it properly. Please try again.";
      }

      // Clean the response to remove echoed query and context
      // The API often echoes back the query with context, we want to remove that
      if (responseContent) {
        // Pattern 1: Match "Thank you for reaching out about '...'." and extract everything after the closing quote and period
        // This handles both cases: with and without context in the quoted string
        const echoPattern = /^Thank you for reaching out about ['"](?:[^'"]*?Context:[^'"]*?|[^'"]*?)['"]\.\s*/i;
        responseContent = responseContent.replace(echoPattern, "");
        
        // Pattern 2: Remove any remaining "Context: ..." patterns that might be outside quotes
        responseContent = responseContent.replace(/(?:^|\s)(?:\\n\\n|\\n|\n\n|\s)Context:.*?\.\s*/gi, "");
        
        // Pattern 3: Remove any quoted text at the start that looks like an echo
        responseContent = responseContent.replace(/^['"].*?['"]\.\s*/, "");
        
        // Pattern 4: Find where the actual advice starts (common starters)
        // Look for patterns like "It's important", "Here are", "I recommend", etc.
        const adviceStarters = [
          /It'?s\s+(?:important|crucial|essential|vital)/i,
          /Here\s+are/i,
          /I\s+(?:recommend|suggest|advise)/i,
          /You\s+(?:should|can|may|might)/i,
          /Consider/i,
          /Try/i,
          /Focus\s+on/i,
          /Remember/i,
          /Take\s+time/i,
        ];
        
        for (const pattern of adviceStarters) {
          const match = responseContent.match(pattern);
          if (match && match.index > 0) {
            // Found advice starter, extract from there
            responseContent = responseContent.substring(match.index).trim();
            break;
          }
        }
        
        // Clean up: normalize whitespace (convert \n to space, collapse multiple spaces)
        responseContent = responseContent.replace(/\\n/g, " ").replace(/\n/g, " ").replace(/\s+/g, " ").trim();
      }

      // Validate that we have actual content
      if (!responseContent || responseContent.trim().length === 0) {
        console.error("Empty response content received after cleaning");
        throw new Error("Empty response received from wellness API");
      }

      console.log("Extracted response content length:", responseContent.length);
      console.log("Extracted response content preview:", responseContent.substring(0, 200));

      // Ensure we have meaningful content
      const trimmedContent = responseContent.trim();
      if (trimmedContent.length === 0) {
        throw new Error("Response content is empty after trimming");
      }

      // Add agent response
      const wellnessMessage = {
        id: generateUniqueId() + 2,
        sender: "wellness-agent",
        agentName: "WellnessBot",
        agentColor: "#F97316",
        agentType: "wellness",
        content: trimmedContent,
        wellnessType: wellnessProfile.wellnessType,
        timestamp: new Date().toISOString(),
        isLoading: false,
        // Include sources if available
        sources: data.sources || null,
      };
      
      console.log("Adding wellness message to chat:", wellnessMessage);
      setMessages((prev) => {
        const updated = [...prev, wellnessMessage];
        console.log("Updated messages count:", updated.length);
        return updated;
      });
      setWellnessResponse({ content: trimmedContent });
      
      // Show success toast
      toast.success(t("Wellness guidance received!"), {
        duration: 3000,
      });

      // Clear the query
      setWellnessQuery("");
    } catch (error) {
      console.error("Wellness query error:", error);
      
      // Remove loading message on error
      setMessages((prev) => prev.filter((msg) => !msg.isLoading || msg.sender !== "wellness-agent"));

      toast.error(t("Failed to get wellness guidance. Please try again."));
      
      // Add error message to chat
      const errorMessage = {
        id: generateUniqueId() + 3,
        sender: "system",
        content: t("Error: Could not get wellness guidance. Please check your connection and try again."),
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsWellnessLoading(false);
    }
  };



  // Function to fetch learning response from a task ID using RTK Query
  const fetchLearningResponse = async (taskId) => {
    try {
      console.log("FETCHING LEARNING RESPONSE FOR TASK:", taskId);

      // Log the current messages state before fetching
      console.log("MESSAGES BEFORE FETCH:", messages);

      console.log("STARTING RTK QUERY OPERATION...");
      const data = await getLearningTaskStatus(taskId).unwrap();
      console.log("RTK QUERY RESPONSE:", data);
      console.log("RESPONSE FIELD:", data.response);

      // Check the status of the response
      if (data && data.status) {
        console.log("RESPONSE STATUS:", data.status);

        // If the status is "completed", show the final response
        if (data.status === "completed" && data.response) {
          console.log("TASK COMPLETED! Showing final response");

          // FORCE ADD a new message with the final response
          console.log("FORCE ADDING FINAL RESPONSE TO UI");

          // First, remove any loading messages
          setMessages((prev) =>
            prev.filter(
              (msg) => !(msg.sender === "learning-agent" && msg.isLoading)
            )
          );

          // Then add the new response message
          setTimeout(() => {
            const finalMessage = {
              id: generateUniqueId(),
              sender: "learning-agent",
              agentName: "Learning Assistant",
              agentColor: "#8B5CF6",
              agentType: "learning",
              content: data.response,
              isLoading: false,
              timestamp: new Date().toISOString(),
            };

            console.log("ADDING FINAL MESSAGE:", finalMessage);

            setMessages((prev) => [...prev, finalMessage]);

            // Force a re-render
            setTimeout(() => {
              console.log("FORCING RE-RENDER");
              setMessages((prev) => [...prev]);
            }, 100);
          }, 100);

          console.log("ADDED FINAL RESPONSE TO UI:", data.response);
          return data;
        }
        // If the status is "running" or "queued", poll again after a delay
        else if (data.status === "running" || data.status === "queued") {
          console.log("TASK STILL RUNNING. Will check again in 2 seconds");

          // Update any existing loading message or add a new one
          setMessages((prev) => {
            // Find any existing loading message
            const loadingMessageIndex = prev.findIndex(
              (msg) => msg.sender === "learning-agent" && msg.isLoading
            );

            if (loadingMessageIndex >= 0) {
              // Update the existing loading message
              console.log("Updating existing loading message");
              const updatedMessages = [...prev];
              updatedMessages[loadingMessageIndex] = {
                ...updatedMessages[loadingMessageIndex],
                content: data.response || "Still processing your request...",
                timestamp: new Date().toISOString(),
              };
              return updatedMessages;
            } else {
              // Add a new loading message
              console.log("Adding new loading message");
              return [
                ...prev,
                {
                  id: generateUniqueId(),
                  sender: "learning-agent",
                  agentName: "Learning Assistant",
                  agentColor: "#8B5CF6",
                  agentType: "learning",
                  content: data.response || "Processing your request... ⏳",
                  isLoading: true,
                  timestamp: new Date().toISOString(),
                },
              ];
            }
          });

          // Poll again after 1 second
          setTimeout(() => {
            console.log("Polling again for task:", taskId);
            fetchLearningResponse(taskId);
          }, 1000);

          return data;
        }
      } else if (data && data.response) {
        // Fallback for when status is not provided but response is
        console.log(
          "NO STATUS FIELD BUT RESPONSE FOUND. Showing response directly."
        );

        // FORCE ADD a new message with the direct response
        console.log("FORCE ADDING DIRECT RESPONSE TO UI");

        // First, remove any loading messages
        setMessages((prev) =>
          prev.filter(
            (msg) => !(msg.sender === "learning-agent" && msg.isLoading)
          )
        );

        // Then add the new response message
        setTimeout(() => {
          const finalMessage = {
            id: generateUniqueId(),
            sender: "learning-agent",
            agentName: "Learning Assistant",
            agentColor: "#8B5CF6",
            agentType: "learning",
            content: data.response,
            isLoading: false,
            timestamp: new Date().toISOString(),
          };

          console.log("ADDING DIRECT MESSAGE:", finalMessage);

          setMessages((prev) => [...prev, finalMessage]);

          // Force a re-render
          setTimeout(() => {
            console.log("FORCING RE-RENDER");
            setMessages((prev) => [...prev]);
          }, 100);
        }, 100);

        console.log("ADDED RESPONSE TO UI:", data.response);
        return data;
      } else {
        console.error("NO RESPONSE OR STATUS FIELD FOUND IN DATA:", data);

        // Add an error message
        setMessages((prev) => [
          ...prev,
          {
            id: generateUniqueId(),
            sender: "system",
            content: "No response received from the server.",
            timestamp: new Date().toISOString(),
          },
        ]);

        return null;
      }
    } catch (error) {
      console.error("ERROR FETCHING RESPONSE:", error);

      // Add an error message
      setMessages((prev) => [
        ...prev,
        {
          id: generateUniqueId(),
          sender: "system",
          content: "Error connecting to the learning service.",
          timestamp: new Date().toISOString(),
        },
      ]);

      return null;
    }
  };

  // Function to poll for task status - kept for backward compatibility
  // eslint-disable-next-line no-unused-vars
  const pollTaskStatus = async (
    taskId,
    userId,
    maxAttempts = 60, // Increased max attempts since we're polling more frequently
    interval = 1500 // 1.5 seconds between polls as recommended (1-2 seconds)
  ) => {
    let attempts = 0;

    // Add a loading message
    const loadingMessageId = generateUniqueId();
    setMessages((prev) => [
      ...prev,
      {
        id: loadingMessageId,
        sender: "learning-agent",
        agentName: "Learning Assistant",
        agentColor: "#8B5CF6", // Purple color for learning agent
        agentType: "learning",
        content: "Your question is being processed...",
        isLoading: true,
        timestamp: new Date().toISOString(),
      },
    ]);

    // Start polling
    const poll = async () => {
      if (attempts >= maxAttempts) {
        // Replace loading message with timeout message
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === loadingMessageId
              ? {
                  ...msg,
                  content:
                    "Sorry, it's taking longer than expected to process your request. Please try again later.",
                  isLoading: false,
                }
              : msg
          )
        );
        return null;
      }

      attempts++;

      try {
        // Try direct fetch first using the dynamic API base URL
        // Example: ${API_BASE_URL}/user/learning/af3c9b32-48ff-4ca3-afbd-4e88e475c0d6
        const directUrl = `${API_BASE_URL}/user/learning/${taskId}`;
        console.log(`Polling attempt ${attempts} - Direct URL:`, directUrl);

        let statusResponse;

        try {
          // Use RTK Query to get learning task status
          statusResponse = await getLearningTaskStatus(taskId).unwrap();
          console.log(`RTK Query response:`, statusResponse);
        } catch (rtkError) {
          console.error("Error with RTK Query:", rtkError);
          statusResponse = null;
        }

        console.log(`Polling attempt ${attempts} - Response:`, statusResponse);

        // Check if we have a valid response
        if (statusResponse) {
          // Check if the task is complete based on the status field
          // Handle both the API function response format and the direct URL response format
          const isCompleted =
            statusResponse.status === "completed" ||
            (statusResponse.response && !statusResponse.isLoading);

          if (isCompleted) {
            // Extract the response content - handle both formats
            // Format 1: From API function with response field
            // Format 2: From direct URL with response field
            let responseContent = null;

            if (statusResponse.response) {
              responseContent = statusResponse.response;
            } else if (
              statusResponse.chat_history &&
              statusResponse.chat_history.length > 0
            ) {
              // Get the last assistant message from chat history
              const assistantMessages = statusResponse.chat_history.filter(
                (msg) => msg.role === "assistant"
              );
              if (assistantMessages.length > 0) {
                responseContent =
                  assistantMessages[assistantMessages.length - 1].content;
              }
            }

            if (responseContent) {
              console.log(
                "Found response content to display:",
                responseContent
              );

              // Replace loading message with actual response
              setMessages((prev) => {
                const updatedMessages = prev.map((msg) =>
                  msg.id === loadingMessageId
                    ? {
                        ...msg,
                        content: responseContent,
                        isLoading: false,
                      }
                    : msg
                );
                console.log("Updated messages:", updatedMessages);
                return updatedMessages;
              });

              // Log the updated state after a short delay to ensure state has been updated
              setTimeout(() => {
                console.log("Current messages state after update:", messages);
              }, 100);

              // Show a toast notification to confirm the response was received
              toast.success("Learning task completed successfully!", {
                icon: "🎓",
                duration: 3000,
              });

              return statusResponse;
            } else {
              // No valid response content found
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === loadingMessageId
                    ? {
                        ...msg,
                        content:
                          "Sorry, I couldn't generate a proper response. Please try again.",
                        isLoading: false,
                      }
                    : msg
                )
              );
              return null;
            }
          } else if (statusResponse.status === "failed") {
            // Replace loading message with error message
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === loadingMessageId
                  ? {
                      ...msg,
                      content:
                        statusResponse.error ||
                        "Sorry, there was an error processing your request.",
                      isLoading: false,
                    }
                  : msg
              )
            );
            return null;
          } else if (
            statusResponse.status === "queued" ||
            statusResponse.status === "running" ||
            statusResponse.status === "processing"
          ) {
            // Task is still in progress, continue polling
            // Update the loading message with appropriate text based on status
            const statusText =
              statusResponse.status === "queued"
                ? "Your question is in queue..."
                : "Processing your request...";

            if (attempts % 3 === 0) {
              // Update the message every 3 attempts
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === loadingMessageId
                    ? {
                        ...msg,
                        content: statusText,
                      }
                    : msg
                )
              );
            }
          }

          // Wait for the specified interval
          await new Promise((resolve) => setTimeout(resolve, interval));

          // Continue polling
          return poll();
        } else {
          // Replace loading message with error message
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === loadingMessageId
                ? {
                    ...msg,
                    content:
                      "Sorry, there was an error checking the status of your request.",
                    isLoading: false,
                  }
                : msg
            )
          );
          return null;
        }
      } catch (error) {
        console.error("Error polling task status:", error);

        // Replace loading message with error message
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === loadingMessageId
              ? {
                  ...msg,
                  content:
                    "Sorry, there was an error checking the status of your request.",
                  isLoading: false,
                }
              : msg
          )
        );
        return null;
      }
    };

    return poll();
  };

  // Handle user input submission
  const handleSubmit = async (e) => {
    if (e) e.preventDefault();

    if (!userInput.trim()) return;

    // Add user message
    const userMessage = {
      id: generateUniqueId(),
      sender: "user",
      content: userInput,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    const messageText = userInput;
    setUserInput("");

    // Get the user ID from Supabase auth - define it at the beginning of the function
    // so it's available throughout the entire function scope
    let userId = "anonymous-user";

    // Use the user ID from Redux store if available
    if (user && user.id) {
      userId = user.id;
      console.log("Using authenticated user ID:", userId);
    } else {
      console.log("No authenticated user found, using anonymous-user");
    }

    // Check if wellnessBot is the active agent - if so, skip learning endpoint entirely
    // For wellnessBot, we always use the chat API directly, regardless of simulation state
    const activeAgentCheck = agents.find((a) => a.status === "active");
    const wellnessBotAgent = agents.find((a) => a.type === "wellness");
    const isWellnessBotActive = (activeAgentCheck && activeAgentCheck.type === "wellness") || 
                                (wellnessBotAgent && !activeAgentCheck); // Also handle if wellnessBot exists but no agent is active
    console.log("WellnessBot check:", { activeAgentCheck, wellnessBotAgent, isWellnessBotActive, isSimulating });

    // Always send the user message to the learning endpoint (except for wellnessBot which uses its own API)
    // Skip learning endpoint if wellnessBot is active OR if simulation is running with wellnessBot
    if (!isWellnessBotActive) {
      try {
      console.log("Sending user message to learning endpoint:", messageText);

      // Check if this is an education agent - if so, use orchestration edumentor endpoint
      const activeAgent = agents.find((a) => a.status === "active");
      const educationAgent = agents.find((a) => a.type === "education");
      
      // Consider it an education agent if:
      // 1. Active agent is education type, OR
      // 2. There's lesson data (user generated a lesson), OR
      // 3. EduMentor profile has subject/topic set (user is working with EduMentor)
      const hasActiveEducationAgent = activeAgent && activeAgent.type === "education";
      const hasLessonData = !!lessonData;
      const hasEduMentorProfile = !!(eduMentorProfile?.selectedSubject && eduMentorProfile?.topic);
      const isEducationAgent = hasActiveEducationAgent || hasLessonData || hasEduMentorProfile;

      console.log("Education agent check:", {
        isEducationAgent,
        hasActiveEducationAgent,
        hasLessonData,
        hasEduMentorProfile,
        activeAgentType: activeAgent?.type,
        lessonDataKeys: lessonData ? Object.keys(lessonData) : null,
        profileSubject: eduMentorProfile?.selectedSubject,
        profileTopic: eduMentorProfile?.topic,
        isSimulating
      });

      // If it's an education agent, use the orchestration edumentor endpoint
      // Skip the learning endpoint entirely for education agents
      if (isEducationAgent) {
        console.log("Using EduMentor orchestration endpoint for education agent");
        // Get current language (map i18n language to backend format)
        const currentLanguage = i18n.language === "ar" ? "arabic" : "english";
        
        try {
          const edumentorResponse = await askEdumentor({
            query: messageText,
            user_id: userId,
            language: currentLanguage,
          }).unwrap();

          console.log("EduMentor response received:", edumentorResponse);

          // Extract the explanation from the response
          const responseContent = edumentorResponse.explanation || edumentorResponse.response || "I'm here to help you learn!";

          // Add the EduMentor response as a message
          setMessages((prev) => [
            ...prev,
            {
              id: generateUniqueId() + 1,
              sender: "learning-agent",
              agentName: "EduMentor Learning Assistant",
              agentColor: "#8B5CF6",
              agentType: "learning",
              content: responseContent,
              timestamp: new Date().toISOString(),
            },
          ]);
          return;
        } catch (edumentorError) {
          console.error("EduMentor endpoint error:", edumentorError);
          
          // Show error message to user instead of falling through
          setMessages((prev) => [
            ...prev,
            {
              id: generateUniqueId() + 1,
              sender: "system",
              content: "Sorry, I couldn't process your message. Please try again later.",
              timestamp: new Date().toISOString(),
            },
          ]);
          toast.error("Failed to get response from EduMentor. Please try again.");
          return;
        }
      }

      // Only use PDF ID if there's an active PDF
      // Skip learning endpoint entirely if this is an education agent
      if (isEducationAgent) {
        console.log("Skipping learning endpoint - this is an education agent");
        return;
      }

      let documentId = null;

      // If there's an active PDF, use its ID
      if (activePdfId) {
        documentId = activePdfId;
      }
      // If simulation is running, use agent type as context
      else if (isSimulating) {
        if (activeAgent) {
          // Don't set documentId here - we'll let the backend handle it
          // Just log the agent type for debugging
          console.log("Active agent type:", activeAgent.type);
        }
      }

      // For simulation mode, use synchronous processing (wait=true)
      // For learning mode, use asynchronous processing (wait=false)
      const wait = isSimulating;

      // Prepare the learning data payload
      const learningPayload = {
        user_id: userId,
        query: messageText,
        ...(documentId && { pdf_id: documentId }),
      };

      const learningResponse = await sendLearningData(learningPayload).unwrap();

      // If simulation is not running, display the learning API response
      if (!isSimulating) {
        // Check if this is an asynchronous response with a task_id
        // Check if we have a learning_task_id in the response (primary method)
        if (learningResponse && learningResponse.learning_task_id) {
          const taskId = learningResponse.learning_task_id;
          console.log("TASK ID RECEIVED:", taskId);

          // Add an initial loading message
          const loadingMessageId = generateUniqueId();
          setMessages((prev) => [
            ...prev,
            {
              id: loadingMessageId,
              sender: "learning-agent",
              agentName: "Learning Assistant",
              agentColor: "#8B5CF6",
              agentType: "learning",
              content: "Processing your request... ⏳",
              isLoading: true,
              timestamp: new Date().toISOString(),
            },
          ]);

          // Fetch the response using the dynamic learning_task_id
          fetchLearningResponse(taskId);
        }
        // Fallback to the old format if learning_task_id is not available
        else if (
          learningResponse &&
          learningResponse.success &&
          learningResponse.isAsync &&
          learningResponse.task_id
        ) {
          const taskId = learningResponse.task_id;
          console.log("FALLBACK TASK ID RECEIVED:", taskId);

          // Add an initial loading message
          const loadingMessageId = generateUniqueId();
          setMessages((prev) => [
            ...prev,
            {
              id: loadingMessageId,
              sender: "learning-agent",
              agentName: "Learning Assistant",
              agentColor: "#8B5CF6",
              agentType: "learning",
              content: "Processing your request... ⏳",
              isLoading: true,
              timestamp: new Date().toISOString(),
            },
          ]);

          // Fetch the response using the dynamic task_id
          fetchLearningResponse(taskId);
        }
        // Handle synchronous response or immediate result
        else if (learningResponse && learningResponse.response) {
          // Extract the response content from the API response
          const responseContent = learningResponse.response;

          console.log("Displaying learning API response:", responseContent);

          // Add the learning API response as a message from the "learning" agent
          setMessages((prev) => [
            ...prev,
            {
              id: generateUniqueId() + 1,
              sender: "learning-agent",
              agentName: "Learning Assistant",
              agentColor: "#8B5CF6", // Purple color for learning agent
              agentType: "learning",
              content: responseContent,
              timestamp: new Date().toISOString(),
            },
          ]);
        } else if (learningResponse && learningResponse.error) {
          // If there was an error, show an error message
          console.warn(
            "Warning: Learning endpoint returned an error:",
            learningResponse.error
          );

          // Add an error message
          setMessages((prev) => [
            ...prev,
            {
              id: generateUniqueId() + 1,
              sender: "system",
              content: `Sorry, I couldn't process your request. ${learningResponse.error}`,
              timestamp: new Date().toISOString(),
            },
          ]);
        } else {
          // If no valid response, show a generic message
          setMessages((prev) => [
            ...prev,
            {
              id: generateUniqueId() + 1,
              sender: "system",
              content:
                "Your message has been received, but I couldn't generate a response. Please try again.",
              timestamp: new Date().toISOString(),
            },
          ]);
        }
        return;
      }

      // Handle learning endpoint response
      if (learningResponse.success || learningResponse.response) {
        // Successfully sent message to learning endpoint
      } else {
        // Learning endpoint returned an error
      }
    } catch (error) {
      // Error sending message to learning endpoint
      console.error("Learning endpoint error:", error);

      // If simulation is not running, check if this might be a wellnessBot message
      // If so, continue to wellnessBot handling instead of showing error
      const wellnessBotAgent = agents.find((a) => a.type === "wellness");
      if (!isSimulating && wellnessBotAgent) {
        console.log("Learning endpoint failed, but wellnessBot exists - continuing to wellnessBot handling");
        // Continue to wellnessBot handling below instead of showing error
      } else if (!isSimulating) {
        setMessages((prev) => [
          ...prev,
          {
            id: generateUniqueId() + 1,
            sender: "system",
            content:
              "Sorry, there was an error processing your message. Please try again later.",
            timestamp: new Date().toISOString(),
          },
        ]);
        return;
      }
    }
    } // End of learning endpoint call (skipped for wellnessBot)

    // Get the active agent (should be the selected one)
    const activeAgent = agents.find((a) => a.status === "active");

    // For wellnessBot, handle it directly even if not marked as active but exists in agents
    if (!activeAgent && isWellnessBotActive) {
      // If wellnessBot was detected but not active, try to find it in agents
      const wellnessBotAgent = agents.find((a) => a.type === "wellness");
      if (wellnessBotAgent) {
        // Set it as active temporarily for this message
        setAgents((prev) =>
          prev.map((agent) =>
            agent.id === wellnessBotAgent.id
              ? { ...agent, status: "active" }
              : agent
          )
        );
      }
    }

    if (!activeAgent && !isWellnessBotActive) {
      // If no active agent is found and it's not wellnessBot, show an error
      toast.error("No active agent found. Please restart the simulation.");
      return;
    }

    // Use the active agent as the responding agent (or wellnessBot if it was just activated)
    const respondingAgent = activeAgent || agents.find((a) => a.type === "wellness");

    // Safety check - if no responding agent found, show error and return
    if (!respondingAgent) {
      toast.error("No agent available. Please select an agent and start the simulation.");
      return;
    }

    // Generate a confidence score with slight variation
    const baseConfidence = respondingAgent.confidence;
    const confidenceVariation = Math.random() * 0.1 - 0.05; // -0.05 to +0.05
    const newConfidence = Math.min(
      0.99,
      Math.max(0.5, baseConfidence + confidenceVariation)
    );

    // Update the agent's confidence score
    setAgents((prev) =>
      prev.map((agent) =>
        agent.id === respondingAgent.id
          ? { ...agent, confidence: newConfidence }
          : agent
      )
    );

    // Try to send the message to the API
    try {
      // Prepare payload
      const payload = {
        message: messageText,
        agentId: respondingAgent.id,
        userId: userId, // Use the userId we already determined above
      };

      // Skip message sending for financial, wellness, and education agents
      // These bots should only be used through their dedicated forms/buttons
      if (respondingAgent.type === "financial" || 
          respondingAgent.type === "wellness" || 
          respondingAgent.type === "education") {
        toast.info(t("Please use the dedicated form/button for this agent instead of the chat."), {
            duration: 3000,
          });
          return;
        }


      // For non-wellness agents, use the standard agent message API
      // Add loading message for better UX
      const loadingMessageId = generateUniqueId() + 1;
      const loadingMessage = {
        id: loadingMessageId,
        sender: respondingAgent.id,
        agentName: respondingAgent.name,
        agentColor: respondingAgent.color,
        agentType: respondingAgent.type,
        content: "",
        isLoading: true,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, loadingMessage]);

      // Call the API to send the message
      const response = await sendAgentMessage(payload).unwrap();

      // Remove loading message
      setMessages((prev) => prev.filter((msg) => msg.id !== loadingMessageId));

      // Extract response content (handle different response formats)
      let responseContent = "";
      if (response && response.content) {
        responseContent = response.content;
      } else if (response && response.message) {
        responseContent = response.message;
      } else if (response && response.response) {
        responseContent = typeof response.response === "string" ? response.response : response.response.message || JSON.stringify(response.response);
      } else if (response && typeof response === "string") {
        responseContent = response;
      } else {
        console.warn("Unexpected agent API response format:", response);
        responseContent = `I received your message about "${messageText}", but I'm having trouble processing it right now. Please try again.`;
      }

      // Validate that we have actual content
      if (!responseContent || responseContent.trim().length === 0) {
        throw new Error("Empty response received from agent API");
      }

      const trimmedContent = responseContent.trim();

      // If we get a response from the API, use it
      if (trimmedContent) {
        // Create the agent message with the API response
        const agentMessage = {
          id: generateUniqueId() + 1,
          sender: respondingAgent.id,
          agentName: respondingAgent.name,
          agentColor: respondingAgent.color,
          agentType: respondingAgent.type,
          content: trimmedContent,
          timestamp: new Date().toISOString(),
          confidence: response?.confidence || newConfidence,
          audioUrl: response?.audioUrl || null,
          isLoading: false,
        };

        // Update messages
        setMessages((prev) => [...prev, agentMessage]);

        return;
      }
    } catch (error) {
      console.error("Error in agent message handling:", error);
      
      // Remove any loading messages on error
      setMessages((prev) => prev.filter((msg) => !msg.isLoading || (msg.sender !== respondingAgent.id && msg.sender !== "wellness-agent")));
      
      // Check for 404 error
      if (error?.status === 404) {
        // Add a system message about the error (only once per session)
        if (!sessionStorage.getItem("api_404_shown")) {
          setMessages((prev) => [
            ...prev,
            {
              id: generateUniqueId(),
              sender: "system",
              content:
                "The agent server is currently unavailable. Running in local mode.",
              timestamp: new Date().toISOString(),
            },
          ]);
          sessionStorage.setItem("api_404_shown", "true");
        }

        // Agent server unavailable. Running in local mode.
      } else {
        // Show user-friendly error message for other errors
        toast.error(t("Failed to get agent response. Please try again."), {
          duration: 5000,
        });
        
        // Add error message to chat
        setMessages((prev) => [
          ...prev,
          {
            id: generateUniqueId() + 1,
            sender: "system",
            agentName: "System",
            agentColor: "#EF4444",
            agentType: "system",
            content: t("I apologize, but I couldn't process your message. Please try again or check your connection."),
            timestamp: new Date().toISOString(),
            isLoading: false,
          },
        ]);
      }
      // Continue with local simulation if API call fails
    }

    // Fallback to local simulation if API call fails or returns invalid data
    setTimeout(() => {
      // Create the agent message with audio URL (simulated)
      const agentMessage = {
        id: generateUniqueId() + 1,
        sender: respondingAgent.id,
        agentName: respondingAgent.name,
        agentColor: respondingAgent.color,
        agentType: respondingAgent.type,
        content: generateAgentResponse(messageText, respondingAgent),
        timestamp: new Date().toISOString(),
        confidence: newConfidence,
        // In a real app, this would be a real audio URL from the API
        audioUrl:
          Math.random() > 0.3
            ? `${API_BASE_URL}/simulated-audio-${respondingAgent.id}.mp3`
            : null,
      };

      // Update messages
      setMessages((prev) => [...prev, agentMessage]);
    }, 1000);
  };

  // Generate a simulated agent response based on agent type
  const generateAgentResponse = (input, agent) => {
    // Different response templates based on agent type
    const responsesByType = {
      education: [
        `From an educational perspective, I can help with "${input}". Let me break this down into key learning concepts.`,
        `I've analyzed your question about "${input}" and can provide a structured learning path.`,
        `This is an interesting educational topic. For "${input}", I recommend starting with fundamental concepts first.`,
        `I can create a learning module about "${input}" with practice exercises and assessments.`,
        `Let me connect this query "${input}" to our existing educational resources and curriculum.`,
      ],
      financial: [
        `From a financial analysis standpoint, "${input}" involves several key considerations.`,
        `I've run the numbers on "${input}" and can provide a detailed financial projection.`,
        `For your query about "${input}", I recommend the following financial strategy...`,
        `Let me break down the cost-benefit analysis of "${input}" with both short and long-term projections.`,
        `I can help optimize your financial approach to "${input}" while minimizing potential risks.`,
      ],
      wellness: [
        `From a wellness perspective, "${input}" can be approached with these balanced lifestyle adjustments.`,
        `I've analyzed your wellness query about "${input}" and have some holistic recommendations.`,
        `For optimal wellbeing regarding "${input}", consider these evidence-based practices...`,
        `Let me suggest a personalized wellness plan for "${input}" that fits your lifestyle.`,
        `I can recommend mindfulness techniques specifically tailored to address "${input}".`,
      ],
      custom: [
        `I've analyzed your request: "${input}" and I'm working on a solution.`,
        `Based on my understanding of "${input}", I recommend the following approach...`,
        `I'm processing your input: "${input}". This will require further analysis.`,
        `I've identified several ways to address your request: "${input}".`,
        `Let me collaborate with other agents to solve: "${input}".`,
      ],
    };

    // Get responses for the agent type or use default responses
    const agentType = agent?.type || "custom";
    const typeResponses = responsesByType[agentType] || responsesByType.custom;

    return typeResponses[Math.floor(Math.random() * typeResponses.length)];
  };

  // Audio player functions
  const playAudio = (audioUrl) => {
    if (!audioUrl) return;

    // If audio is disabled in settings, show a toast and return
    if (!audioEnabled) {
      toast(
        "Audio is disabled in settings. Enable it to play audio responses.",
        { icon: "🔇" }
      );
      return;
    }

    // Stop any currently playing audio
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.src = "";
    }

    // Create new audio element
    const audio = new Audio(audioUrl);
    audio.volume = audioVolume;
    audio.muted = isMuted;

    // Set current audio and play
    audioRef.current = audio;
    setCurrentAudio(audioUrl);
    setIsPlaying(true);

    // Play the audio
    audio.play().catch((err) => {
      console.error("Error playing audio:", err);
      toast.error("Could not play audio");
    });

    // Add event listeners
    audio.addEventListener("ended", () => {
      setIsPlaying(false);
      setCurrentAudio(null);
    });
  };

  const toggleAudioPlay = (audioUrl) => {
    if (isPlaying && currentAudio === audioUrl) {
      // Pause current audio
      if (audioRef.current) {
        audioRef.current.pause();
      }
      setIsPlaying(false);
    } else if (audioUrl) {
      // Play new audio
      playAudio(audioUrl);
    }
  };

  // Format confidence score as percentage
  const formatConfidence = (confidence) => {
    return `${Math.round(confidence * 100)}%`;
  };

  // Get available months from simulation results
  const getAvailableMonths = (results) => {
    if (!results) return [];

    // Collect all months from different data sections
    const months = new Set();

    // Helper function to process each data section
    const processSection = (section) => {
      if (Array.isArray(section)) {
        section.forEach((item) => {
          if (item.month && !isNaN(Number(item.month))) {
            months.add(Number(item.month)); // Convert to number to ensure proper sorting
          }
        });
      }
    };

    // Process all data sections
    processSection(results.simulated_cashflow);
    processSection(results.discipline_report);
    processSection(results.goal_status);
    processSection(results.financial_strategy);
    processSection(results.karmic_tracker);
    processSection(results.behavior_tracker);
    processSection(results.reflections);
    // Keep these for backward compatibility
    processSection(results.persona_history);
    processSection(results.reflection_month);

    // If no months found, default to month 1
    if (months.size === 0) {
      months.add(1);
    }

    // Convert to array and sort numerically
    const sortedMonths = Array.from(months).sort((a, b) => a - b);

    // Ensure we have at least one month
    return sortedMonths.length > 0 ? sortedMonths : [1];
  };

  // Filter simulation results for a specific month
  const getMonthData = (results, month) => {
    if (!results) return null;

    const filteredData = {
      simulated_cashflow: Array.isArray(results.simulated_cashflow)
        ? results.simulated_cashflow.filter((item) => item.month === month)
        : [],
      discipline_report: Array.isArray(results.discipline_report)
        ? results.discipline_report.filter((item) => item.month === month)
        : [],
      goal_status: Array.isArray(results.goal_status)
        ? results.goal_status.filter((item) => item.month === month)
        : [],
      financial_strategy: Array.isArray(results.financial_strategy)
        ? results.financial_strategy.filter((item) => item.month === month)
        : [],
      karmic_tracker: Array.isArray(results.karmic_tracker)
        ? results.karmic_tracker.filter((item) => item.month === month)
        : [],
      behavior_tracker: Array.isArray(results.behavior_tracker)
        ? results.behavior_tracker.filter((item) => item.month === month)
        : [],
      reflections: Array.isArray(results.reflections)
        ? results.reflections.filter((item) => item.month === month)
        : [],
      // Keep these for backward compatibility
      persona_history: Array.isArray(results.persona_history)
        ? results.persona_history.filter((item) => item.month === month)
        : [],
      reflection_month: Array.isArray(results.reflection_month)
        ? results.reflection_month.filter((item) => item.month === month)
        : [],
    };

    return filteredData;
  };

  // Render financial simulation results
  const renderSimulationResults = () => {
    if (!simulationResults) return null;

    // Get available months
    const availableMonths = getAvailableMonths(simulationResults);

    // If no months available, show message
    if (availableMonths.length === 0) {
      return (
        <div className="bg-blue-900/20 rounded-lg p-4 my-4 border border-blue-500/30">
          <div className="text-center py-4 text-white/70">
            <p>No simulation results available yet.</p>
            <p className="text-sm mt-1">
              Try sending a message to the financial agent to generate results.
            </p>
          </div>
        </div>
      );
    }

    // Ensure currentMonth is valid
    if (!availableMonths.includes(currentMonth)) {
      setCurrentMonth(availableMonths[0]);
    }

    // Get data for the current month
    const monthData = getMonthData(simulationResults, currentMonth);

    return (
      <div className="bg-blue-900/20 rounded-lg p-4 my-4 border border-blue-500/30">
        {/* Header with user name */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center">
            <h3 className="text-lg font-semibold text-white flex items-center">
              <DollarSign size={18} className="mr-2 text-blue-400" />
              Month {currentMonth} Details
            </h3>

            {isLoadingResults && (
              <div className="animate-pulse w-3 h-3 rounded-full bg-blue-400 ml-3"></div>
            )}
            {isProcessingSimulation && !isLoadingResults && (
              <div className="flex items-center ml-3">
                <div className="animate-pulse w-2 h-2 rounded-full bg-green-400 mr-1"></div>
                <div
                  className="animate-pulse w-2 h-2 rounded-full bg-green-400 mr-1"
                  style={{ animationDelay: "0.3s" }}
                ></div>
                <div
                  className="animate-pulse w-2 h-2 rounded-full bg-green-400"
                  style={{ animationDelay: "0.6s" }}
                ></div>
              </div>
            )}
          </div>

          {/* User name display */}
          {(simulationResults.user_name || financialProfile.name) && (
            <div className="flex items-center bg-blue-500/20 px-3 py-1 rounded-lg">
              <User size={14} className="mr-2 text-blue-300" />
              <span className="text-sm font-medium text-blue-100">
                {simulationResults.user_name || financialProfile.name}
              </span>
            </div>
          )}
        </div>

        {/* Month tabs removed as requested */}

        {/* Cashflow Summary */}
        {monthData.simulated_cashflow.length > 0 && (
          <div className="mb-4">
            <h4 className="text-sm font-medium text-white/90 mb-2 flex items-center">
              <Wallet size={14} className="mr-1.5 text-blue-400" />
              Cashflow Summary
            </h4>
            <div className="bg-black/20 rounded-md p-3 border border-white/10">
              {monthData.simulated_cashflow.map((cashflow, index) => (
                <div key={`cashflow-${index}`} className="mb-3 last:mb-0">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-2">
                    <div className="bg-black/30 rounded p-2">
                      <div className="text-xs text-white/60 mb-1">
                        Total Income
                      </div>
                      <div className="text-sm font-medium text-green-400">
                        ₹{cashflow.income?.total || 0}
                      </div>
                    </div>
                    <div className="bg-black/30 rounded p-2">
                      <div className="text-xs text-white/60 mb-1">
                        Total Expenses
                      </div>
                      <div className="text-sm font-medium text-red-400">
                        ₹{cashflow.expenses?.total || 0}
                      </div>
                    </div>
                    <div className="bg-black/30 rounded p-2">
                      <div className="text-xs text-white/60 mb-1">Savings</div>
                      <div className="text-sm font-medium text-blue-400">
                        ₹
                        {typeof cashflow.savings === "object" &&
                        cashflow.savings !== null
                          ? cashflow.savings.amount || 0
                          : cashflow.savings || 0}
                      </div>
                    </div>
                    <div className="bg-black/30 rounded p-2">
                      <div className="text-xs text-white/60 mb-1">Debt</div>
                      <div className="text-sm font-medium text-orange-400">
                        ₹{cashflow.debt_taken || 0}
                      </div>
                    </div>
                  </div>

                  {/* Income Breakdown */}
                  <div className="mt-3">
                    <div className="text-xs font-medium text-white/80 mb-1">
                      Income Breakdown
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                      {cashflow.income?.salary > 0 && (
                        <div className="flex justify-between items-center bg-black/20 rounded px-2 py-1">
                          <span className="text-xs text-white/70">Salary</span>
                          <span className="text-xs text-green-400">
                            ₹{cashflow.income.salary}
                          </span>
                        </div>
                      )}
                      {cashflow.income?.freelance > 0 && (
                        <div className="flex justify-between items-center bg-black/20 rounded px-2 py-1">
                          <span className="text-xs text-white/70">
                            Freelance
                          </span>
                          <span className="text-xs text-green-400">
                            ₹{cashflow.income.freelance}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Expense Breakdown */}
                  <div className="mt-3">
                    <div className="text-xs font-medium text-white/80 mb-1">
                      Expense Breakdown
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                      {cashflow.expenses?.needs > 0 && (
                        <div className="flex justify-between items-center bg-black/20 rounded px-2 py-1">
                          <span className="text-xs text-white/70">Needs</span>
                          <span className="text-xs text-red-400">
                            ₹{cashflow.expenses.needs}
                          </span>
                        </div>
                      )}
                      {cashflow.expenses?.wants > 0 && (
                        <div className="flex justify-between items-center bg-black/20 rounded px-2 py-1">
                          <span className="text-xs text-white/70">Wants</span>
                          <span className="text-xs text-red-400">
                            ₹{cashflow.expenses.wants}
                          </span>
                        </div>
                      )}
                      {cashflow.expenses?.luxury > 0 && (
                        <div className="flex justify-between items-center bg-black/20 rounded px-2 py-1">
                          <span className="text-xs text-white/70">Luxury</span>
                          <span className="text-xs text-red-400">
                            ₹{cashflow.expenses.luxury}
                          </span>
                        </div>
                      )}
                      {cashflow.expenses?.emergency > 0 && (
                        <div className="flex justify-between items-center bg-black/20 rounded px-2 py-1">
                          <span className="text-xs text-white/70">
                            Emergency
                          </span>
                          <span className="text-xs text-red-400">
                            ₹{cashflow.expenses.emergency}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Simulation Output */}
                  {cashflow.simulation_output && (
                    <div className="mt-3">
                      <div className="text-xs font-medium text-white/80 mb-1">
                        Simulation Output
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                        {cashflow.simulation_output.balance && (
                          <div className="flex justify-between items-center bg-black/20 rounded px-2 py-1">
                            <span className="text-xs text-white/70">
                              Balance
                            </span>
                            <span className="text-xs text-green-400">
                              ₹
                              {typeof cashflow.simulation_output.balance ===
                              "number"
                                ? cashflow.simulation_output.balance
                                : JSON.stringify(
                                    cashflow.simulation_output.balance
                                  )}
                            </span>
                          </div>
                        )}
                        {cashflow.simulation_output.savings_rate && (
                          <div className="flex justify-between items-center bg-black/20 rounded px-2 py-1">
                            <span className="text-xs text-white/70">
                              Savings Rate
                            </span>
                            <span className="text-xs text-blue-400">
                              {typeof cashflow.simulation_output
                                .savings_rate === "number"
                                ? `${(
                                    cashflow.simulation_output.savings_rate *
                                    100
                                  ).toFixed(0)}%`
                                : JSON.stringify(
                                    cashflow.simulation_output.savings_rate
                                  )}
                            </span>
                          </div>
                        )}
                      </div>

                      {/* Notes */}
                      {cashflow.simulation_output.notes && (
                        <div className="mt-2 text-xs text-white/70 bg-black/20 p-2 rounded border border-blue-400/30">
                          <div className="font-medium text-white/80 mb-1">
                            Notes:
                          </div>
                          {typeof cashflow.simulation_output.notes === "string"
                            ? cashflow.simulation_output.notes
                            : JSON.stringify(cashflow.simulation_output.notes)}
                        </div>
                      )}

                      {/* Investment Recommendation */}
                      {cashflow.simulation_output.investment_recommendation && (
                        <div className="mt-2 text-xs text-white/70 bg-black/20 p-2 rounded border border-green-400/30">
                          <div className="font-medium text-white/80 mb-1">
                            Investment Recommendation:
                          </div>
                          {typeof cashflow.simulation_output
                            .investment_recommendation === "string"
                            ? cashflow.simulation_output
                                .investment_recommendation
                            : JSON.stringify(
                                cashflow.simulation_output
                                  .investment_recommendation
                              )}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Notes (fallback for old format) */}
                  {!cashflow.simulation_output && cashflow.notes && (
                    <div className="mt-3 text-xs text-white/70 bg-black/20 p-2 rounded border border-blue-400/30">
                      <div className="font-medium text-white/80 mb-1">
                        Notes:
                      </div>
                      {cashflow.notes}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Discipline Report */}
        {monthData.discipline_report.length > 0 && (
          <div className="mb-4">
            <h4 className="text-sm font-medium text-white/90 mb-2 flex items-center">
              <Target size={14} className="mr-1.5 text-blue-400" />
              Discipline Report
            </h4>
            <div className="bg-black/20 rounded-md p-3 border border-white/10">
              {monthData.discipline_report.map((report, index) => (
                <div key={`discipline-${index}`} className="mb-2 last:mb-0">
                  <div className="flex flex-col md:flex-row md:justify-between md:items-center">
                    <div className="mb-2 md:mb-0">
                      <div className="flex items-center">
                        <span
                          className={`inline-block w-3 h-3 rounded-full mr-2 ${
                            (report.discipline_score ||
                              report.financial_discipline_score) >= 0.8
                              ? "bg-green-500"
                              : (report.discipline_score ||
                                  report.financial_discipline_score) >= 0.5
                              ? "bg-yellow-500"
                              : "bg-red-500"
                          }`}
                        ></span>
                        <span className="text-sm font-medium text-white/90">
                          Discipline Score
                        </span>
                      </div>
                      <div className="mt-1 ml-5">
                        <div className="w-full bg-black/30 h-2 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full ${
                              (report.discipline_score ||
                                report.financial_discipline_score) >= 0.8
                                ? "bg-green-500"
                                : (report.discipline_score ||
                                    report.financial_discipline_score) >= 0.5
                                ? "bg-yellow-500"
                                : "bg-red-500"
                            }`}
                            style={{
                              width: `${
                                (report.discipline_score ||
                                  report.financial_discipline_score) * 100
                              }%`,
                            }}
                          ></div>
                        </div>
                        <div className="flex justify-between text-xs text-white/60 mt-1">
                          <span>0</span>
                          <span
                            className={
                              (report.discipline_score ||
                                report.financial_discipline_score) >= 0.8
                                ? "text-green-400"
                                : (report.discipline_score ||
                                    report.financial_discipline_score) >= 0.5
                                ? "text-yellow-400"
                                : "text-red-400"
                            }
                          >
                            {report.discipline_score
                              ? `${report.discipline_score}/10`
                              : report.financial_discipline_score
                              ? `${(
                                  report.financial_discipline_score * 100
                                ).toFixed(0)}%`
                              : "0/10"}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Rules checked */}
                    {report.rules_checked && (
                      <div className="bg-black/30 rounded p-2 md:w-1/3">
                        <div className="text-xs font-medium text-white/80 mb-1">
                          Rules Checked
                        </div>
                        <div className="space-y-1">
                          {Object.entries(report.rules_checked).map(
                            ([rule, passed], ruleIndex) => (
                              <div
                                key={`rule-${index}-${ruleIndex}`}
                                className="flex items-center"
                              >
                                {passed ? (
                                  <span className="text-green-400 mr-1.5">
                                    ✓
                                  </span>
                                ) : (
                                  <span className="text-red-400 mr-1.5">✗</span>
                                )}
                                <span className="text-xs text-white/70">
                                  {rule
                                    .split("_")
                                    .map(
                                      (word) =>
                                        word.charAt(0).toUpperCase() +
                                        word.slice(1)
                                    )
                                    .join(" ")}
                                </span>
                              </div>
                            )
                          )}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Improvement Areas */}
                  {Array.isArray(report.improvement_areas) &&
                    report.improvement_areas.length > 0 && (
                      <div className="mt-3 bg-yellow-900/20 p-2 rounded border border-yellow-500/30">
                        <div className="text-xs font-medium text-white/80 mb-1">
                          Improvement Areas:
                        </div>
                        <ul className="list-disc list-inside pl-1 text-xs text-white/70">
                          {report.improvement_areas.map((area, areaIndex) => (
                            <li key={`area-${index}-${areaIndex}`}>
                              {typeof area === "string"
                                ? area
                                : typeof area === "object" && area !== null
                                ? area.title
                                  ? `${area.title}: ${area.description || ""}`
                                  : JSON.stringify(area)
                                : "No improvement area available"}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                  {/* Violations */}
                  {Array.isArray(report.violations) &&
                    report.violations.length > 0 && (
                      <div className="mt-3 bg-red-900/20 p-2 rounded border border-red-500/30">
                        <div className="text-xs font-medium text-white/80 mb-1">
                          Violations:
                        </div>
                        <ul className="list-disc list-inside pl-1 text-xs text-white/70">
                          {report.violations.map(
                            (violation, violationIndex) => (
                              <li key={`violation-${index}-${violationIndex}`}>
                                {typeof violation === "string"
                                  ? violation
                                  : typeof violation === "object" &&
                                    violation !== null
                                  ? violation.title
                                    ? `${violation.title}: ${
                                        violation.description || ""
                                      }`
                                    : JSON.stringify(violation)
                                  : "No violation available"}
                              </li>
                            )
                          )}
                        </ul>
                      </div>
                    )}

                  {/* Discipline Metrics */}
                  {report.discipline_metrics && (
                    <div className="mt-3 bg-blue-900/20 p-2 rounded border border-blue-500/30">
                      <div className="text-xs font-medium text-white/80 mb-1">
                        Discipline Metrics:
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-2 mt-2">
                        {Object.entries(report.discipline_metrics).map(
                          ([metric, value], metricIndex) => (
                            <div
                              key={`metric-${index}-${metricIndex}`}
                              className="bg-black/20 rounded p-2"
                            >
                              <div className="flex justify-between items-center">
                                <span className="text-xs text-white/70">
                                  {metric
                                    .replace(/_/g, " ")
                                    .replace(/\b\w/g, (l) => l.toUpperCase())}
                                </span>
                                <span
                                  className={`text-xs font-medium ${
                                    value >= 0.8
                                      ? "text-green-400"
                                      : value >= 0.5
                                      ? "text-blue-400"
                                      : "text-yellow-400"
                                  }`}
                                >
                                  {(value * 100).toFixed(0)}%
                                </span>
                              </div>
                            </div>
                          )
                        )}
                      </div>
                    </div>
                  )}

                  {/* Recommendations */}
                  {Array.isArray(report.recommendations) &&
                    report.recommendations.length > 0 && (
                      <div className="mt-3 bg-blue-900/20 p-2 rounded border border-blue-500/30">
                        <div className="text-xs font-medium text-white/80 mb-1">
                          Recommendations:
                        </div>
                        <ul className="list-disc list-inside pl-1 text-xs text-white/70">
                          {report.recommendations.map((rec, recIndex) => (
                            <li key={`rec-${index}-${recIndex}`}>
                              {typeof rec === "string"
                                ? rec
                                : typeof rec === "object" && rec !== null
                                ? rec.title
                                  ? `${rec.title}: ${rec.description || ""}`
                                  : JSON.stringify(rec)
                                : "No recommendation available"}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                </div>
              ))}
            </div>
          </div>
        )}


        {/* Financial Strategy */}
        {monthData.financial_strategy.length > 0 && (
          <div className="mb-4">
            <h4 className="text-sm font-medium text-white/90 mb-2 flex items-center">
              <BrainCircuit size={14} className="mr-1.5 text-blue-400" />
              Financial Strategy
            </h4>
            <div className="bg-black/20 rounded-md p-3 border border-white/10">
              <div className="bg-gradient-to-r from-blue-900/30 to-purple-900/30 rounded-lg p-3 mb-3">
                <div className="flex items-center mb-2">
                  <div className="w-8 h-8 rounded-full bg-blue-500/30 flex items-center justify-center mr-2">
                    <BrainCircuit size={18} className="text-blue-400" />
                  </div>
                  <h5 className="text-sm font-medium text-white/90">
                    Strategic Recommendations
                  </h5>
                </div>

                <div className="space-y-2">
                  {/* Check for old format (traits.recommendations) */}
                  {monthData.financial_strategy[0]?.traits?.recommendations ? (
                    Array.isArray(
                      monthData.financial_strategy[0].traits.recommendations
                    ) ? (
                      monthData.financial_strategy[0].traits.recommendations.map(
                        (rec, index) => (
                          <div
                            key={`strategy-${index}`}
                            className="bg-black/30 rounded-md p-2 flex items-start"
                          >
                            <span className="w-5 h-5 rounded-full bg-blue-500/30 flex-shrink-0 flex items-center justify-center mr-2 mt-0.5">
                              <span className="text-xs text-blue-400 font-medium">
                                {index + 1}
                              </span>
                            </span>
                            <span className="text-sm text-white/80">{rec}</span>
                          </div>
                        )
                      )
                    ) : (
                      <div className="bg-black/30 rounded-md p-2">
                        <span className="text-sm text-white/80">
                          No recommendations available
                        </span>
                      </div>
                    )
                  ) : /* Check for new format (recommendations array) */
                  monthData.financial_strategy[0]?.recommendations ? (
                    Array.isArray(
                      monthData.financial_strategy[0].recommendations
                    ) ? (
                      monthData.financial_strategy[0].recommendations.map(
                        (rec, index) => (
                          <div
                            key={`strategy-${index}`}
                            className="bg-black/30 rounded-md p-2 flex items-start"
                          >
                            <span className="w-5 h-5 rounded-full bg-blue-500/30 flex-shrink-0 flex items-center justify-center mr-2 mt-0.5">
                              <span className="text-xs text-blue-400 font-medium">
                                {index + 1}
                              </span>
                            </span>
                            <span className="text-sm text-white/80">
                              {typeof rec === "string"
                                ? rec
                                : rec.type
                                ? `${rec.type
                                    .replace(/_/g, " ")
                                    .replace(/\b\w/g, (l) =>
                                      l.toUpperCase()
                                    )}: ${rec.reason || rec.amount || ""}`
                                : JSON.stringify(rec)}
                            </span>
                          </div>
                        )
                      )
                    ) : (
                      <div className="bg-black/30 rounded-md p-2">
                        <span className="text-sm text-white/80">
                          No recommendations available
                        </span>
                      </div>
                    )
                  ) : (
                    <div className="bg-black/30 rounded-md p-2">
                      <span className="text-sm text-white/80">
                        No recommendations available
                      </span>
                    </div>
                  )}
                </div>

                {/* Reasoning */}
                {(monthData.financial_strategy[0]?.traits?.reasoning ||
                  monthData.financial_strategy[0]?.reasoning) && (
                  <div className="mt-3 bg-black/30 p-2 rounded border border-blue-500/30">
                    <div className="text-xs font-medium text-white/80 mb-1">
                      Reasoning:
                    </div>
                    <div className="text-xs text-white/70">
                      {monthData.financial_strategy[0]?.traits?.reasoning ||
                        monthData.financial_strategy[0]?.reasoning}
                    </div>
                  </div>
                )}
              </div>

              {/* Karmic Tracker */}
              {monthData.karmic_tracker.length === 0 && simulationResults?.karmic_tracker?.length > 0 && (
                <div className="bg-gradient-to-r from-purple-900/30 to-indigo-900/30 rounded-lg p-3">
                  <div className="flex items-center justify-between mb-2">
                    <h5 className="text-sm font-medium text-white/90">
                      Karmic Analysis
                    </h5>
                  </div>
                  {/* Karma Score (fallback latest) */}
                  <div className="mb-3">
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-xs text-white/70">Karma Score</span>
                      <span className="text-xs font-medium text-purple-400">
                        {(
                          simulationResults.karmic_tracker[
                            simulationResults.karmic_tracker.length - 1
                          ]?.traits?.karma_score ||
                          simulationResults.karmic_tracker[
                            simulationResults.karmic_tracker.length - 1
                          ]?.karma_score || 0
                        )}
                      </span>
                    </div>
                  </div>
                  {/* Trend (fallback latest) */}
                  {(
                    simulationResults.karmic_tracker[
                      simulationResults.karmic_tracker.length - 1
                    ]?.traits?.trend ||
                    simulationResults.karmic_tracker[
                      simulationResults.karmic_tracker.length - 1
                    ]?.karma_trend
                  ) && (
                    <div className="mt-1 flex items-center">
                      <span
                        className={`text-xs font-medium ${
                          simulationResults.karmic_tracker[
                            simulationResults.karmic_tracker.length - 1
                          ]?.traits?.trend === "Positive" ||
                          simulationResults.karmic_tracker[
                            simulationResults.karmic_tracker.length - 1
                          ]?.karma_trend === "Positive" ||
                          simulationResults.karmic_tracker[
                            simulationResults.karmic_tracker.length - 1
                          ]?.karma_trend === "Improving"
                            ? "text-green-400"
                            : (
                                simulationResults.karmic_tracker[
                                  simulationResults.karmic_tracker.length - 1
                                ]?.traits?.trend === "Negative" ||
                                simulationResults.karmic_tracker[
                                  simulationResults.karmic_tracker.length - 1
                                ]?.karma_trend === "Negative" ||
                                simulationResults.karmic_tracker[
                                  simulationResults.karmic_tracker.length - 1
                                ]?.karma_trend === "Declining"
                              )
                            ? "text-red-400"
                            : "text-yellow-400"
                        }`}
                      >
                        {
                          simulationResults.karmic_tracker[
                            simulationResults.karmic_tracker.length - 1
                          ]?.traits?.trend ||
                          simulationResults.karmic_tracker[
                            simulationResults.karmic_tracker.length - 1
                          ]?.karma_trend
                        }
                      </span>
                    </div>
                  )}
                </div>
              )}
              {monthData.karmic_tracker.length > 0 && (
                <div className="bg-gradient-to-r from-purple-900/30 to-indigo-900/30 rounded-lg p-3">
                  <div className="flex items-center mb-2">
                    <div className="w-8 h-8 rounded-full bg-purple-500/30 flex items-center justify-center mr-2">
                      <Target size={18} className="text-purple-400" />
                    </div>
                    <h5 className="text-sm font-medium text-white/90">
                      Karmic Analysis
                    </h5>
                  </div>

                  {/* Karma Score */}
                  <div className="mb-3">
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-xs text-white/70">Karma Score</span>
                      <span className="text-xs font-medium text-purple-400">
                        {monthData.karmic_tracker[0]?.traits?.karma_score ||
                          monthData.karmic_tracker[0]?.karma_score ||
                          0}
                        /100
                      </span>
                    </div>
                    <div className="h-2 bg-black/30 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-red-500 via-yellow-500 to-green-500"
                        style={{
                          width: `${
                            monthData.karmic_tracker[0]?.traits?.karma_score ||
                            monthData.karmic_tracker[0]?.karma_score ||
                            0
                          }%`,
                        }}
                      ></div>
                    </div>
                    <div className="flex justify-between text-xs text-white/50 mt-1">
                      <span>0</span>
                      <span>50</span>
                      <span>100</span>
                    </div>
                  </div>

                  {/* Traits */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
                    {((monthData.karmic_tracker[0]?.traits?.sattvic_traits &&
                      monthData.karmic_tracker[0]?.traits?.sattvic_traits
                        .length > 0) ||
                      (monthData.karmic_tracker[0]?.sattvic_traits &&
                        monthData.karmic_tracker[0]?.sattvic_traits > 0)) && (
                      <div className="bg-green-900/20 rounded p-2">
                        <div className="text-xs font-medium text-green-400 mb-1">
                          Sattvic Traits
                        </div>
                        <ul className="list-disc list-inside pl-1 text-xs text-white/70">
                          {Array.isArray(
                            monthData.karmic_tracker[0]?.traits?.sattvic_traits
                          ) ? (
                            monthData.karmic_tracker[0].traits.sattvic_traits.map(
                              (trait, idx) => (
                                <li key={`sattvic-${idx}`}>{trait}</li>
                              )
                            )
                          ) : monthData.karmic_tracker[0]?.sattvic_traits ? (
                            <li>
                              {monthData.karmic_tracker[0].sattvic_traits}
                            </li>
                          ) : (
                            <li>No sattvic traits available</li>
                          )}
                        </ul>
                      </div>
                    )}

                    {((monthData.karmic_tracker[0]?.traits?.rajasic_traits &&
                      monthData.karmic_tracker[0]?.traits?.rajasic_traits
                        .length > 0) ||
                      (monthData.karmic_tracker[0]?.rajasic_traits &&
                        monthData.karmic_tracker[0]?.rajasic_traits > 0)) && (
                      <div className="bg-yellow-900/20 rounded p-2">
                        <div className="text-xs font-medium text-yellow-400 mb-1">
                          Rajasic Traits
                        </div>
                        <ul className="list-disc list-inside pl-1 text-xs text-white/70">
                          {Array.isArray(
                            monthData.karmic_tracker[0]?.traits?.rajasic_traits
                          ) ? (
                            monthData.karmic_tracker[0].traits.rajasic_traits.map(
                              (trait, idx) => (
                                <li key={`rajasic-${idx}`}>{trait}</li>
                              )
                            )
                          ) : monthData.karmic_tracker[0]?.rajasic_traits ? (
                            <li>
                              {monthData.karmic_tracker[0].rajasic_traits}
                            </li>
                          ) : (
                            <li>No rajasic traits available</li>
                          )}
                        </ul>
                      </div>
                    )}

                    {((monthData.karmic_tracker[0]?.traits?.tamasic_traits &&
                      monthData.karmic_tracker[0]?.traits?.tamasic_traits
                        .length > 0) ||
                      (monthData.karmic_tracker[0]?.tamasic_traits &&
                        monthData.karmic_tracker[0]?.tamasic_traits > 0)) && (
                      <div className="bg-red-900/20 rounded p-2">
                        <div className="text-xs font-medium text-red-400 mb-1">
                          Tamasic Traits
                        </div>
                        <ul className="list-disc list-inside pl-1 text-xs text-white/70">
                          {Array.isArray(
                            monthData.karmic_tracker[0]?.traits?.tamasic_traits
                          ) ? (
                            monthData.karmic_tracker[0].traits.tamasic_traits.map(
                              (trait, idx) => (
                                <li key={`tamasic-${idx}`}>{trait}</li>
                              )
                            )
                          ) : monthData.karmic_tracker[0]?.tamasic_traits ? (
                            <li>
                              {monthData.karmic_tracker[0].tamasic_traits}
                            </li>
                          ) : (
                            <li>No tamasic traits available</li>
                          )}
                        </ul>
                      </div>
                    )}
                  </div>

                  {/* Trend */}
                  {(monthData.karmic_tracker[0]?.traits?.trend ||
                    monthData.karmic_tracker[0]?.karma_trend) && (
                    <div className="mt-3 flex items-center">
                      <span className="text-xs text-white/70 mr-2">Trend:</span>
                      <span
                        className={`text-xs font-medium ${
                          monthData.karmic_tracker[0]?.traits?.trend ===
                            "Positive" ||
                          monthData.karmic_tracker[0]?.karma_trend ===
                            "Positive" ||
                          monthData.karmic_tracker[0]?.karma_trend ===
                            "Improving"
                            ? "text-green-400"
                            : monthData.karmic_tracker[0]?.traits?.trend ===
                                "Negative" ||
                              monthData.karmic_tracker[0]?.karma_trend ===
                                "Negative" ||
                              monthData.karmic_tracker[0]?.karma_trend ===
                                "Declining"
                            ? "text-red-400"
                            : "text-yellow-400"
                        }`}
                      >
                        {monthData.karmic_tracker[0]?.traits?.trend ||
                          monthData.karmic_tracker[0]?.karma_trend}
                      </span>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Persona History */}
        {monthData.persona_history.length > 0 && (
          <div className="mb-4">
            <h4 className="text-sm font-medium text-white/90 mb-2 flex items-center">
              <User size={14} className="mr-1.5 text-blue-400" />
              Financial Persona
            </h4>
            <div className="bg-black/20 rounded-md p-3 border border-white/10">
              {monthData.persona_history.map((persona, index) => (
                <div
                  key={`persona-${index}`}
                  className="bg-gradient-to-r from-orange-900/30 to-red-900/30 rounded-lg p-3"
                >
                  <div className="flex items-center mb-3">
                    <div className="w-10 h-10 rounded-full bg-orange-500/30 flex items-center justify-center mr-3">
                      <User size={20} className="text-orange-400" />
                    </div>
                    <div>
                      <h5 className="text-sm font-medium text-white/90">
                        {persona.persona_title}
                      </h5>
                      <div className="text-xs text-white/70">
                        {persona.behavior_pattern}
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-2 mb-2">
                    <div className="bg-black/30 rounded p-2">
                      <div className="text-xs text-white/60 mb-1">
                        Karmic Score
                      </div>
                      <div className="text-sm font-medium text-purple-400">
                        {persona.avg_karmic_score}/100
                      </div>
                    </div>
                    <div className="bg-black/30 rounded p-2">
                      <div className="text-xs text-white/60 mb-1">Change</div>
                      <div className="text-sm font-medium">
                        {persona.change_flag ? (
                          <span className="text-green-400">Improving</span>
                        ) : (
                          <span className="text-yellow-400">Stable</span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Reflection Month */}
        {monthData.reflection_month.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-white/90 mb-2 flex items-center">
              <BrainCircuit size={14} className="mr-1.5 text-blue-400" />
              Monthly Reflection
            </h4>
            <div className="bg-black/20 rounded-md p-3 border border-white/10">
              {monthData.reflection_month.map((reflection, index) => (
                <div
                  key={`reflection-${index}`}
                  className="bg-gradient-to-r from-blue-900/30 to-indigo-900/30 rounded-lg p-3"
                >
                  {reflection.summary_message && (
                    <div className="bg-black/30 p-3 rounded-lg mb-3 border border-blue-500/30">
                      <div className="text-sm text-white/90">
                        {reflection.summary_message}
                      </div>
                    </div>
                  )}

                  {reflection.transition_note &&
                    reflection.transition_note !== "No transition noted" && (
                      <div className="mt-2">
                        <div className="text-xs font-medium text-white/80 mb-1">
                          Transition Note:
                        </div>
                        <div className="text-xs text-white/70 bg-black/20 p-2 rounded">
                          {reflection.transition_note}
                        </div>
                      </div>
                    )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Behavior Tracker */}
        {monthData.behavior_tracker.length > 0 && (
          <div className="mb-4">
            <h4 className="text-sm font-medium text-white/90 mb-2 flex items-center">
              <Activity size={14} className="mr-1.5 text-blue-400" />
              Spending Behavior
            </h4>
            <div className="bg-black/20 rounded-md p-3 border border-white/10">
              {monthData.behavior_tracker.map((behavior, index) => (
                <div key={`behavior-${index}`} className="mb-3 last:mb-0">
                  <div className="bg-black/30 rounded-lg p-3">
                    {/* Display spending pattern */}
                    {behavior.spending_pattern && (
                      <div className="mb-3">
                        <h5 className="text-sm font-medium text-white/90 mb-2">
                          Spending Pattern
                        </h5>
                        <div className="bg-black/20 rounded p-2">
                          <div className="flex justify-between items-center">
                            <span className="text-xs text-white/70">
                              Pattern
                            </span>
                            <span className="text-xs font-medium text-blue-400">
                              {behavior.spending_pattern
                                .replace(/-/g, " ")
                                .replace(/\b\w/g, (l) => l.toUpperCase())}
                            </span>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Display goal adherence */}
                    {behavior.goal_adherence && (
                      <div className="mb-3">
                        <h5 className="text-sm font-medium text-white/90 mb-2">
                          Goal Adherence
                        </h5>
                        <div className="bg-black/20 rounded p-2">
                          <div className="flex justify-between items-center">
                            <span className="text-xs text-white/70">
                              Status
                            </span>
                            <span
                              className={`text-xs font-medium ${
                                behavior.goal_adherence === "on-track"
                                  ? "text-green-400"
                                  : behavior.goal_adherence === "off-track"
                                  ? "text-red-400"
                                  : "text-yellow-400"
                              }`}
                            >
                              {behavior.goal_adherence
                                .replace(/-/g, " ")
                                .replace(/\b\w/g, (l) => l.toUpperCase())}
                            </span>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Display saving consistency */}
                    {behavior.saving_consistency && (
                      <div className="mb-3">
                        <h5 className="text-sm font-medium text-white/90 mb-2">
                          Saving Consistency
                        </h5>
                        <div className="bg-black/20 rounded p-2">
                          <div className="flex justify-between items-center">
                            <span className="text-xs text-white/70">
                              Status
                            </span>
                            <span
                              className={`text-xs font-medium ${
                                behavior.saving_consistency === "consistent"
                                  ? "text-green-400"
                                  : behavior.saving_consistency ===
                                    "inconsistent"
                                  ? "text-yellow-400"
                                  : "text-blue-400"
                              }`}
                            >
                              {behavior.saving_consistency
                                .replace(/-/g, " ")
                                .replace(/\b\w/g, (l) => l.toUpperCase())}
                            </span>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Display labels */}
                    {behavior.labels && behavior.labels.length > 0 && (
                      <div className="mb-3">
                        <h5 className="text-sm font-medium text-white/90 mb-2">
                          Behavior Labels
                        </h5>
                        <div className="flex flex-wrap gap-2">
                          {behavior.labels.map((label, labelIndex) => (
                            <span
                              key={`label-${index}-${labelIndex}`}
                              className="text-xs px-2 py-1 rounded-full bg-black/30 border border-white/10 text-white/80"
                            >
                              {label
                                .replace(/-/g, " ")
                                .replace(/\b\w/g, (l) => l.toUpperCase())}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Display budget limits if available */}
                    {behavior.budget_limits && (
                      <div>
                        <h5 className="text-sm font-medium text-white/90 mb-2">
                          Budget Limits
                        </h5>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                          {Array.isArray(behavior.budget_limits) ? (
                            behavior.budget_limits.map(
                              (budgetItem, budgetIndex) => (
                                <div
                                  key={`budget-${index}-${budgetIndex}`}
                                  className="bg-black/20 rounded p-2"
                                >
                                  <div className="flex justify-between items-center">
                                    <span className="text-xs text-white/70">
                                      {typeof budgetItem.category === "string"
                                        ? budgetItem.category
                                        : "Category"}
                                    </span>
                                    <span className="text-xs font-medium text-blue-400">
                                      ₹
                                      {typeof budgetItem.limit === "number"
                                        ? budgetItem.limit
                                        : typeof budgetItem.limit === "object"
                                        ? JSON.stringify(budgetItem.limit)
                                        : 0}
                                    </span>
                                  </div>
                                </div>
                              )
                            )
                          ) : (
                            <div className="text-xs text-white/70">
                              No budget limits defined
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Fallback message if no data sections are available */}
        {monthData.simulated_cashflow.length === 0 &&
          monthData.discipline_report.length === 0 &&
          monthData.goal_status.length === 0 &&
          monthData.financial_strategy.length === 0 &&
          monthData.karmic_tracker.length === 0 &&
          monthData.persona_history.length === 0 &&
          monthData.behavior_tracker.length === 0 &&
          monthData.reflection_month.length === 0 && (
            <div className="text-center py-4 text-white/70">
              <p className="text-lg font-medium">
                Agent unavailable. No simulation results.
              </p>
              <p className="text-sm mt-2">
                Please try again or contact support if the issue persists.
              </p>
            </div>
          )}

      </div>
    );
  };

  // Render message based on sender type
  const renderMessage = (message) => {
    if (message.sender === "system") {
      return (
        <div className="bg-gray-800/50 rounded-lg p-3 my-2 text-gray-300 text-sm border border-gray-700/50">
          <div className="flex items-center">
            <Cpu size={16} className="mr-2 text-gray-400" />
            <span>System</span>
          </div>
          <p className="mt-1">{message.content}</p>
        </div>
      );
    } else if (message.sender === "user") {
      return (
        <div className="bg-indigo-900/30 rounded-lg p-3 my-2 text-white border border-indigo-700/30">
          <div className="flex items-center">
            <MessageSquare size={16} className="mr-2 text-indigo-400" />
            <span>You</span>
          </div>
          <p className="mt-1">{message.content}</p>
        </div>
      );
    } else if (message.sender === "learning-agent") {
      // Learning agent message with enhanced visibility
      return (
        <div
          className="rounded-lg p-4 my-3 text-white border relative"
          style={{
            backgroundColor: `rgba(139, 92, 246, 0.3)`, // More visible purple background
            borderColor: `rgba(139, 92, 246, 0.7)`, // More visible border
            boxShadow: `0 4px 15px rgba(139, 92, 246, 0.25)`, // Enhanced glow
          }}
        >
          {/* New response indicator - only show for non-loading messages */}
          {!message.isLoading && (
            <div
              className="absolute -top-1 -right-1 w-4 h-4 rounded-full animate-ping"
              style={{
                backgroundColor: `rgba(139, 92, 246, 0.7)`,
                animationDuration: "2s",
                animationIterationCount: "3",
              }}
            ></div>
          )}

          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <div
                className="w-7 h-7 rounded-full flex items-center justify-center mr-2"
                style={{
                  backgroundColor: `rgba(139, 92, 246, 0.4)`,
                  border: `2px solid rgba(139, 92, 246, 0.6)`,
                  boxShadow: `0 0 10px rgba(139, 92, 246, 0.3)`,
                }}
              >
                <BrainCircuit
                  size={16}
                  style={{ color: "#e9d5ff" }} // Lighter purple for better visibility
                />
              </div>
              <span
                className="font-medium text-base"
                style={{ color: "#e9d5ff" }} // Lighter purple for better visibility
              >
                {message.agentName}
              </span>
            </div>

            {/* Show loading indicator when message is still being processed */}
            {message.isLoading && (
              <div className="flex items-center bg-purple-900/30 px-2 py-1 rounded-full">
                <div className="animate-pulse w-2.5 h-2.5 rounded-full bg-purple-300 mr-1.5"></div>
                <div
                  className="animate-pulse w-2.5 h-2.5 rounded-full bg-purple-300 mr-1.5"
                  style={{ animationDelay: "0.3s" }}
                ></div>
                <div
                  className="animate-pulse w-2.5 h-2.5 rounded-full bg-purple-300"
                  style={{ animationDelay: "0.6s" }}
                ></div>
                <span className="ml-1.5 text-xs text-purple-200">
                  Processing...
                </span>
              </div>
            )}
          </div>

          <div
            className="mt-3 mb-1 text-white leading-relaxed p-2 rounded-md"
            style={{
              backgroundColor: "rgba(255, 255, 255, 0.1)",
              border: "1px solid rgba(255, 255, 255, 0.15)",
            }}
          >
            {message.content}
          </div>

          {/* Timestamp */}
          <div className="text-xs text-purple-300/70 mt-2 flex items-center">
            <Clock size={10} className="mr-1.5" />
            {new Date(message.timestamp).toLocaleTimeString()}
          </div>
        </div>
      );
    } else if (message.sender === "wellness-agent") {
      // Wellness agent message with specialized display
      return (
        <div className="bg-orange-900/20 rounded-lg p-4 my-3 text-white border border-orange-500/30">
          <div className="flex items-center mb-3">
            <div className="w-7 h-7 rounded-full bg-orange-500/20 flex items-center justify-center mr-2 border border-orange-500/40">
              <Heart size={16} className="text-orange-400" />
            </div>
            <span className="font-medium text-orange-400">WellnessBot</span>
            <span className="ml-2 text-xs bg-orange-500/20 px-2 py-1 rounded-full text-orange-300">
              {message.wellnessType === "emotional" ? "Emotional Support" : "Financial Wellness"}
            </span>
          </div>

          {/* Main advice or content */}
          {message.advice ? (
            <div className="mb-4">
              <h4 className="text-orange-400 font-medium mb-2">Guidance</h4>
              <p className="text-white/90 leading-relaxed">{message.advice.main_advice}</p>

              {message.advice.practical_steps && message.advice.practical_steps.length > 0 && (
                <div className="mt-3">
                  <h5 className="text-orange-400/80 font-medium mb-2 text-sm">Action Steps:</h5>
                  <ul className="space-y-1">
                    {message.advice.practical_steps.map((step, index) => (
                      <li key={index} className="text-white/80 text-sm flex items-start">
                        <span className="text-orange-400 mr-2 mt-0.5">•</span>
                        {step}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {message.advice.tips && message.advice.tips.length > 0 && (
                <div className="mt-3">
                  <h5 className="text-orange-400/80 font-medium mb-2 text-sm">Tips:</h5>
                  <ul className="space-y-1">
                    {message.advice.tips.map((tip, index) => (
                      <li key={index} className="text-white/80 text-sm flex items-start">
                        <span className="text-orange-400 mr-2 mt-0.5">💡</span>
                        {tip}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ) : message.content ? (
            <div className="mb-4">
              <h4 className="text-orange-400 font-medium mb-2">Guidance</h4>
              <p className="text-white/90 leading-relaxed whitespace-pre-wrap">{message.content}</p>
            </div>
          ) : null}

          {/* Emotional support */}
          {message.emotional_nudge && (
            <div className="mb-4 bg-orange-900/10 p-3 rounded-lg border border-orange-500/20">
              <h4 className="text-orange-400 font-medium mb-2 flex items-center">
                <Heart size={14} className="mr-1" />
                Emotional Support
              </h4>

              {message.emotional_nudge.encouragement && (
                <p className="text-white/90 mb-2 text-sm">{message.emotional_nudge.encouragement}</p>
              )}

              {message.emotional_nudge.affirmation && (
                <div className="bg-orange-500/10 p-2 rounded border-l-2 border-orange-500/50 mb-2">
                  <p className="text-orange-200 text-sm font-medium">{message.emotional_nudge.affirmation}</p>
                </div>
              )}

              {message.emotional_nudge.mindfulness_tip && (
                <div className="text-white/80 text-sm">
                  <span className="text-orange-400 font-medium">Mindfulness Tip: </span>
                  {message.emotional_nudge.mindfulness_tip}
                </div>
              )}
            </div>
          )}

          {/* Triggers detected */}
          {message.triggers_detected && message.triggers_detected.length > 0 && (
            <div className="mb-3 bg-yellow-900/20 p-3 rounded-lg border border-yellow-500/30">
              <h4 className="text-yellow-400 font-medium mb-2 text-sm flex items-center">
                <AlertTriangle size={14} className="mr-1" />
                Wellness Alerts
              </h4>
              {message.triggers_detected.map((trigger, index) => (
                <div key={index} className="text-yellow-200 text-sm mb-1">
                  <span className="font-medium">{trigger.type}:</span> {trigger.message}
                </div>
              ))}
            </div>
          )}

          {/* Timestamp */}
          <div className="text-xs text-orange-300/70 mt-2 flex items-center">
            <Clock size={10} className="mr-1.5" />
            {new Date(message.timestamp).toLocaleTimeString()}
          </div>
        </div>
      );
    } else {
      // Agent message
      const agentIcon = () => {
        switch (message.agentType) {
          case "education":
            return (
              <BookOpen
                size={16}
                className="mr-2"
                style={{ color: message.agentColor }}
              />
            );
          case "financial":
            return (
              <DollarSign
                size={16}
                className="mr-2"
                style={{ color: message.agentColor }}
              />
            );
          case "wellness":
            return (
              <Heart
                size={16}
                className="mr-2"
                style={{ color: message.agentColor }}
              />
            );
          case "learning":
            return (
              <BrainCircuit
                size={16}
                className="mr-2"
                style={{ color: message.agentColor }}
              />
            );
          default:
            return (
              <Bot
                size={16}
                className="mr-2"
                style={{ color: message.agentColor }}
              />
            );
        }
      };

      return (
        <div
          className="rounded-lg p-3 my-2 text-white border border-opacity-30"
          style={{
            backgroundColor: `${message.agentColor}20`,
            borderColor: `${message.agentColor}50`,
          }}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              {agentIcon()}
              <span style={{ color: message.agentColor }}>
                {message.agentName}
              </span>
            </div>

            {message.confidence && (
              <div
                className="text-xs px-2 py-1 rounded-full"
                style={{
                  backgroundColor: `${message.agentColor}30`,
                  color: message.agentColor,
                }}
              >
                Confidence: {formatConfidence(message.confidence)}
              </div>
            )}
          </div>

          <p className="mt-2 mb-2">{message.content}</p>

          {message.audioUrl && (
            <div className="mt-2 pt-2 border-t border-white/10 flex items-center">
              <button
                onClick={() => toggleAudioPlay(message.audioUrl)}
                className="p-2 rounded-full hover:bg-white/10 transition-colors"
                title={
                  isPlaying && currentAudio === message.audioUrl
                    ? "Pause"
                    : "Play"
                }
              >
                {isPlaying && currentAudio === message.audioUrl ? (
                  <Pause size={16} className="text-white/80" />
                ) : (
                  <Play size={16} className="text-white/80" />
                )}
              </button>
              <div className="text-xs text-white/60 ml-2">
                Audio response available
              </div>
            </div>
          )}
        </div>
      );
    }
  };

  // Format relative time for timeline
  const formatRelativeTime = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHour = Math.floor(diffMin / 60);

    if (diffSec < 60) return `${diffSec}s ago`;
    if (diffMin < 60) return `${diffMin}m ago`;
    if (diffHour < 24) return `${diffHour}h ago`;
    return date.toLocaleDateString();
  };

  // Render a timeline item
  const renderTimelineItem = (message) => {
    if (message.sender === "user") {
      return (
        <div className="timeline-item">
          <div className="bg-indigo-900/30 rounded-lg p-3 border border-indigo-700/30 mb-3">
            <div className="flex items-center mb-1">
              <MessageSquare size={14} className="mr-2 text-indigo-400" />
              <span className="text-xs font-medium text-indigo-300">User</span>
            </div>
            <div className="text-sm text-white/90">{message.content}</div>
            <div className="text-xs text-white/60 mt-1 flex items-center">
              <Clock size={10} className="mr-1 text-white/40" />
              {formatRelativeTime(message.timestamp)}
            </div>
          </div>
        </div>
      );
    } else if (message.sender === "learning-agent") {
      // Learning agent message in timeline
      return (
        <div className="timeline-item">
          <div
            className="rounded-lg p-3 border mb-3"
            style={{
              backgroundColor: `rgba(139, 92, 246, 0.25)`,
              borderColor: `rgba(139, 92, 246, 0.5)`,
              boxShadow: `0 2px 8px rgba(139, 92, 246, 0.2)`,
            }}
          >
            <div className="flex items-center mb-1">
              <BrainCircuit
                size={14}
                className="mr-2"
                style={{ color: "#d8b4fe" }}
              />
              <span
                className="text-xs font-medium"
                style={{ color: "#d8b4fe" }}
              >
                {message.agentName}
              </span>
            </div>
            <div className="text-sm text-white/90">
              {message.content.length > 60
                ? `${message.content.substring(0, 60)}...`
                : message.content}
            </div>
            <div className="text-xs text-white/60 mt-1 flex items-center">
              <Clock size={10} className="mr-1 text-white/40" />
              {formatRelativeTime(message.timestamp)}
            </div>
          </div>
        </div>
      );
    } else if (typeof message.sender === "number") {
      // Agent message
      const agentType = message.agentType || "default";
      const agentColor = message.agentColor || "#FF9933";

      // Get the appropriate icon based on agent type
      const getAgentIcon = () => {
        switch (agentType) {
          case "education":
            return (
              <BookOpen size={14} className="mr-2" style={{ color: "white" }} />
            );
          case "financial":
            return (
              <DollarSign
                size={14}
                className="mr-2"
                style={{ color: "white" }}
              />
            );
          case "wellness":
            return (
              <Heart size={14} className="mr-2" style={{ color: "white" }} />
            );
          default:
            return (
              <Bot size={14} className="mr-2" style={{ color: "white" }} />
            );
        }
      };

      return (
        <div className={`timeline-item ${agentType}`}>
          <div
            className="rounded-lg p-3 mb-3 border border-opacity-30"
            style={{
              backgroundColor: `${agentColor}20`,
              borderColor: `${agentColor}50`,
            }}
          >
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center">
                <div
                  className="w-5 h-5 rounded-full flex items-center justify-center mr-1.5"
                  style={{
                    backgroundColor: `${agentColor}60`,
                  }}
                >
                  {getAgentIcon()}
                </div>
                <span
                  className="text-xs font-medium"
                  style={{ color: "white" }}
                >
                  {message.agentName}
                </span>
              </div>
              {message.confidence && (
                <span
                  className="text-xs px-1.5 py-0.5 rounded-full"
                  style={{
                    backgroundColor: `${agentColor}40`,
                    color: "white",
                    border: `1px solid ${agentColor}60`,
                  }}
                >
                  {formatConfidence(message.confidence)}
                </span>
              )}
            </div>
            <div className="text-sm text-white/90 ml-6">
              {message.content.substring(0, 60)}...
            </div>
            <div className="text-xs text-white/60 mt-1 ml-6 flex items-center">
              <Clock size={10} className="mr-1 text-white/40" />
              {formatRelativeTime(message.timestamp)}
            </div>
          </div>
        </div>
      );
    }
    return null;
  };



  return (
    <div className="h-full">
      <GlassContainer>
        <div ref={containerRef} className="flex flex-col h-full">
          <h1 className="text-3xl font-bold text-white mb-4 flex items-center">
            <BrainCircuit className="mr-3 text-orange-500" />
            {t("Agent Simulator")}
          </h1>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 h-[calc(100%-3rem)] overflow-hidden">
            {/* Agent Configuration Panel */}
            <div className="lg:col-span-3 h-full overflow-hidden">
              <div className="bg-white/5 backdrop-blur-sm rounded-xl border border-white/10 shadow-lg h-full p-4 flex flex-col overflow-auto">
                <div className="flex justify-between items-center mb-6">
                  <div className="flex items-center">
                    <div className="w-8 h-8 rounded-full bg-orange-500/20 flex items-center justify-center mr-2">
                      <Settings size={18} className="text-orange-400" />
                    </div>
                    <h2 className="text-xl font-bold text-white">
                      {t("Agent Configuration")}
                    </h2>
                  </div>
                  <button
                    onClick={() => setIsTimelineOpen(!isTimelineOpen)}
                    className="p-2 bg-gray-700/50 rounded-full hover:bg-gray-700/70 transition-colors"
                  >
                    <Settings size={16} className="text-white" />
                  </button>
                </div>



                {/* Financial Simulation Form - Always show when Financial Agent is selected */}
                {selectedAgent &&
                  agents.find((a) => a.id === selectedAgent)?.type ===
                    "financial" && (
                    <div className="mb-4 bg-blue-900/20 rounded-lg p-4 border border-blue-500/30 h-[calc(100%-8rem)] overflow-y-auto custom-scrollbar">
                      <h3 className="text-lg font-semibold text-white mb-3 flex items-center">
                        <DollarSign size={18} className="mr-2 text-blue-400" />
                        {t("Financial Agent Simulation")}
                      </h3>
                      <p className="text-sm text-white/80 mb-4">
                        {t("Welcome to your Personal Financial Simulation. Simulate months of financial life, get guidance, and improve your money habits with AI agents!")}
                      </p>

                      {/* Basic Financial Profile */}
                      <div className="mb-4">
                        <h4 className="text-sm font-medium text-white/90 mb-2 flex items-center">
                          <User size={14} className="mr-1.5 text-blue-400" />
                          {t("Basic Financial Profile")}
                        </h4>

                        <div className="mb-2">
                          <label className="block text-xs text-white/70 mb-1">
                            {t("Your Name")}
                          </label>
                          <input
                            type="text"
                            value={financialProfile.name}
                            onChange={(e) =>
                              handleFinancialProfileChange(
                                "name",
                                e.target.value
                              )
                            }
                            className="w-full bg-blue-600/30 border border-blue-500/40 rounded-lg py-2 px-3 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/60"
                          />
                        </div>

                        <div>
                          <label className="block text-xs text-white/70 mb-1">
                            {t("Monthly Income")} (₹)
                          </label>
                          <input
                            type="text"
                            value={financialProfile.monthlyIncome}
                            onChange={(e) =>
                              handleFinancialProfileChange(
                                "monthlyIncome",
                                e.target.value
                              )
                            }
                            className="w-full bg-blue-600/30 border border-blue-500/40 rounded-lg py-2 px-3 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/60"
                          />
                        </div>
                      </div>

                      {/* Monthly Expenses */}
                      <div className="mb-4">
                        <h4 className="text-sm font-medium text-white/90 mb-2 flex items-center">
                          <ShoppingBag
                            size={14}
                            className="mr-1.5 text-blue-400"
                          />
                          {t("Monthly Expenses")}
                        </h4>

                        <div className="mb-2">
                          <label className="block text-xs text-white/70 mb-1">
                            {t("Number of Expense Categories")}
                          </label>
                          <div className="flex items-center">
                            <input
                              type="text"
                              value={financialProfile.expenses.length}
                              readOnly
                              className="w-16 bg-blue-600/30 border border-blue-500/40 rounded-lg py-2 px-3 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/60"
                            />
                            <button
                              type="button"
                              onClick={addExpense}
                              className="ml-2 p-1.5 bg-blue-500/30 hover:bg-blue-500/50 rounded-lg text-white"
                            >
                              <Plus size={14} />
                            </button>
                          </div>
                        </div>

                        {financialProfile.expenses.map((expense, index) => (
                          <div
                            key={expense.id}
                            className="grid grid-cols-5 gap-2 mb-2"
                          >
                            <div className="col-span-2">
                              <label className="block text-xs text-white/70 mb-1">
                                {t("Expense")} {index + 1} {t("Name")}
                              </label>
                              <input
                                type="text"
                                value={expense.name}
                                onChange={(e) =>
                                  handleExpenseChange(
                                    expense.id,
                                    "name",
                                    e.target.value
                                  )
                                }
                                className="w-full bg-blue-600/30 border border-blue-500/40 rounded-lg py-2 px-3 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/60"
                              />
                            </div>

                            <div className="col-span-2">
                              <label className="block text-xs text-white/70 mb-1">
                                {t("Amount")} (₹)
                              </label>
                              <input
                                type="text"
                                value={expense.amount}
                                onChange={(e) =>
                                  handleExpenseChange(
                                    expense.id,
                                    "amount",
                                    e.target.value
                                  )
                                }
                                className="w-full bg-blue-600/30 border border-blue-500/40 rounded-lg py-2 px-3 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/60"
                              />
                            </div>

                            <div className="flex items-end">
                              <button
                                type="button"
                                onClick={() => removeExpense(expense.id)}
                                className="mb-0.5 p-1.5 bg-red-500/30 hover:bg-red-500/50 rounded-lg text-white"
                                disabled={financialProfile.expenses.length <= 1}
                              >
                                <Minus size={14} />
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>

                      {/* Financial Goal */}
                      <div className="mb-4">
                        <h4 className="text-sm font-medium text-white/90 mb-2 flex items-center">
                          <Target size={14} className="mr-1.5 text-blue-400" />
                          {t("Financial Goal")}
                        </h4>

                        <div>
                          <label className="block text-xs text-white/70 mb-1">
                            {t("What's your financial goal? (e.g., 'Save ₹50,000 for emergency fund')")}
                          </label>
                          <input
                            type="text"
                            value={financialProfile.financialGoal}
                            onChange={(e) =>
                              handleFinancialProfileChange(
                                "financialGoal",
                                e.target.value
                              )
                            }
                            className="w-full bg-blue-600/30 border border-blue-500/40 rounded-lg py-2 px-3 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/60"
                          />
                        </div>
                      </div>

                      {/* Financial Type */}
                      <div className="mb-4">
                        <h4 className="text-sm font-medium text-white/90 mb-2 flex items-center">
                          <Wallet size={14} className="mr-1.5 text-blue-400" />
                          Financial Type
                        </h4>

                        <div>
                          <label className="block text-xs text-white/70 mb-1">
                            Choose your financial type:
                          </label>
                          <select
                            value={financialProfile.financialType}
                            onChange={(e) =>
                              handleFinancialProfileChange(
                                "financialType",
                                e.target.value
                              )
                            }
                            className="w-full bg-blue-600/30 border border-blue-500/40 rounded-lg py-2 px-3 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 appearance-none"
                            style={{
                              backgroundImage:
                                "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%23ffffff' stroke-width='2'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' d='M19 9l-7 7-7-7' /%3E%3C/svg%3E\")",
                              backgroundRepeat: "no-repeat",
                              backgroundPosition: "right 0.5rem center",
                              backgroundSize: "1.5em 1.5em",
                              paddingRight: "2.5rem",
                            }}
                          >
                            <option
                              value="Conservative"
                              className="bg-blue-800"
                            >
                              Conservative
                            </option>
                            <option value="Moderate" className="bg-blue-800">
                              Moderate
                            </option>
                            <option value="Aggressive" className="bg-blue-800">
                              Aggressive
                            </option>
                          </select>
                        </div>
                      </div>

                      {/* Risk Level */}
                      <div className="mb-2">
                        <h4 className="text-sm font-medium text-white/90 mb-2 flex items-center">
                          <AlertTriangle
                            size={14}
                            className="mr-1.5 text-blue-400"
                          />
                          Risk Level
                        </h4>

                        <div>
                          <label className="block text-xs text-white/70 mb-1">
                            Select your risk tolerance:
                          </label>
                          <div className="mt-2 mb-1">
                            <div className="relative pt-1">
                              <div className="flex justify-between mb-2">
                                <span className="text-xs text-orange-400 font-medium">
                                  Low
                                </span>
                                <span className="text-xs text-orange-400 font-medium">
                                  Moderate
                                </span>
                                <span className="text-xs text-orange-400 font-medium">
                                  High
                                </span>
                              </div>
                              <input
                                type="range"
                                min="0"
                                max="2"
                                step="1"
                                value={
                                  financialProfile.riskLevel === "Low"
                                    ? 0
                                    : financialProfile.riskLevel === "Moderate"
                                    ? 1
                                    : 2
                                }
                                onChange={(e) => {
                                  const value = parseInt(e.target.value);
                                  const riskLevel =
                                    value === 0
                                      ? "Low"
                                      : value === 1
                                      ? "Moderate"
                                      : "High";
                                  handleFinancialProfileChange(
                                    "riskLevel",
                                    riskLevel
                                  );
                                }}
                                className="w-full cursor-pointer"
                              />
                              <style>{`
                                input[type="range"] {
                                  -webkit-appearance: none;
                                  appearance: none;
                                  background: linear-gradient(
                                    to right,
                                    #1e40af,
                                    #3b82f6,
                                    #60a5fa
                                  );
                                  outline: none;
                                  border-radius: 8px;
                                  height: 8px;
                                }

                                input[type="range"]:hover {
                                  background: linear-gradient(
                                    to right,
                                    #1e40af,
                                    #3b82f6,
                                    #f97316
                                  );
                                }

                                input[type="range"]:focus {
                                  box-shadow: 0 0 0 2px rgba(249, 115, 22, 0.4);
                                }

                                /* Force the thumb to always be blue or orange, never yellow */
                                input[type="range"]::-webkit-slider-thumb {
                                  -webkit-appearance: none !important;
                                  appearance: none !important;
                                  width: 20px !important;
                                  height: 20px !important;
                                  border-radius: 50% !important;
                                  background: #3b82f6 !important;
                                  border: 2px solid white !important;
                                  cursor: pointer !important;
                                  box-shadow: 0 0 5px rgba(59, 130, 246, 0.5) !important;
                                  transition: all 0.2s ease !important;
                                }

                                input[type="range"]:hover::-webkit-slider-thumb {
                                  background: #f97316 !important; /* Orange color on hover */
                                  box-shadow: 0 0 8px rgba(249, 115, 22, 0.7) !important;
                                }

                                input[type="range"]:active::-webkit-slider-thumb {
                                  background: #f97316 !important; /* Orange color when active */
                                  box-shadow: 0 0 10px rgba(249, 115, 22, 0.8) !important;
                                  transform: scale(
                                    1.1
                                  ) !important; /* Slightly larger when clicked */
                                }

                                input[type="range"]::-webkit-slider-thumb:hover {
                                  background: #f97316 !important; /* Orange color on hover */
                                  box-shadow: 0 0 8px rgba(249, 115, 22, 0.7) !important;
                                }

                                input[type="range"]::-webkit-slider-thumb:active {
                                  background: #f97316 !important; /* Orange color when active */
                                  box-shadow: 0 0 10px rgba(249, 115, 22, 0.8) !important;
                                  transform: scale(
                                    1.1
                                  ) !important; /* Slightly larger when clicked */
                                }

                                input[type="range"]::-moz-range-track {
                                  background: linear-gradient(
                                    to right,
                                    #1e40af,
                                    #3b82f6,
                                    #60a5fa
                                  );
                                  height: 8px;
                                  border-radius: 8px;
                                }

                                input[type="range"]:hover::-moz-range-track {
                                  background: linear-gradient(
                                    to right,
                                    #1e40af,
                                    #3b82f6,
                                    #f97316
                                  );
                                }

                                /* Force the thumb to always be blue or orange, never yellow */
                                input[type="range"]::-moz-range-thumb {
                                  width: 20px !important;
                                  height: 20px !important;
                                  border-radius: 50% !important;
                                  background: #3b82f6 !important;
                                  border: 2px solid white !important;
                                  cursor: pointer !important;
                                  box-shadow: 0 0 5px rgba(59, 130, 246, 0.5) !important;
                                  transition: all 0.2s ease !important;
                                }

                                input[type="range"]:hover::-moz-range-thumb {
                                  background: #f97316 !important; /* Orange color on hover */
                                  box-shadow: 0 0 8px rgba(249, 115, 22, 0.7) !important;
                                }

                                input[type="range"]:active::-moz-range-thumb {
                                  background: #f97316 !important; /* Orange color when active */
                                  box-shadow: 0 0 10px rgba(249, 115, 22, 0.8) !important;
                                  transform: scale(
                                    1.1
                                  ) !important; /* Slightly larger when clicked */
                                }

                                input[type="range"]::-moz-range-thumb:hover {
                                  background: #f97316 !important; /* Orange color on hover */
                                  box-shadow: 0 0 8px rgba(249, 115, 22, 0.7) !important;
                                }

                                input[type="range"]::-moz-range-thumb:active {
                                  background: #f97316 !important; /* Orange color when active */
                                  box-shadow: 0 0 10px rgba(249, 115, 22, 0.8) !important;
                                  transform: scale(
                                    1.1
                                  ) !important; /* Slightly larger when clicked */
                                }
                              `}</style>
                              <div className="flex justify-between mt-2">
                                <div
                                  className={`w-3 h-3 rounded-full ${
                                    financialProfile.riskLevel === "Low"
                                      ? "bg-orange-500"
                                      : "bg-blue-900/50"
                                  }`}
                                ></div>
                                <div
                                  className={`w-3 h-3 rounded-full ${
                                    financialProfile.riskLevel === "Moderate"
                                      ? "bg-orange-500"
                                      : "bg-blue-900/50"
                                  }`}
                                ></div>
                                <div
                                  className={`w-3 h-3 rounded-full ${
                                    financialProfile.riskLevel === "High"
                                      ? "bg-orange-500"
                                      : "bg-blue-900/50"
                                  }`}
                                ></div>
                              </div>
                            </div>
                            <div className="text-center mt-2">
                              <span className="text-sm text-white font-medium">
                                Selected:{" "}
                                <span className="text-orange-400">
                                  {financialProfile.riskLevel}
                                </span>
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>

                      <div className="mt-4 text-center">
                        <div className="inline-flex items-center justify-center px-4 py-2 bg-blue-500/20 border border-blue-500/30 rounded-lg text-blue-300">
                          <Clock size={16} className="mr-2" />
                          <span>
                            {t("Fill in your financial details and press Start to begin simulation")}
                          </span>
                        </div>
                      </div>
                    </div>
                  )}

                {/* EduMentor Form - Always show when EduMentor Agent is selected */}
                {selectedAgent &&
                  agents.find((a) => a.id === selectedAgent)?.type ===
                    "education" && (
                    <div className="mb-4 bg-green-900/20 rounded-lg p-4 border border-green-500/30 h-[calc(100%-8rem)] overflow-y-auto custom-scrollbar">
                      <h3 className="text-lg font-semibold text-white mb-3 flex items-center">
                        <BookOpen size={18} className="mr-2 text-green-400" />
                        {t("EduMentor Learning Assistant")}
                      </h3>
                      <p className="text-sm text-white/80 mb-4">
                        {t("Welcome to your Personal Learning Assistant. Select a subject and topic to begin your educational journey with AI-powered guidance!")}
                      </p>

                      {/* Subject Selection */}
                      <div className="mb-4">
                        <h4 className="text-sm font-medium text-white/90 mb-2 flex items-center">
                          <Book size={14} className="mr-1.5 text-green-400" />
                          {t("Learning Profile")}
                        </h4>

                        <div className="mb-2">
                          <label className="block text-xs text-white/70 mb-1">
                            {t("Subject")}
                          </label>
                          <input
                            type="text"
                            placeholder={t("Type any subject (e.g. Mathematics, Physics, History)")}
                            value={eduMentorProfile.selectedSubject}
                            onChange={(e) =>
                              handleEduMentorProfileChange(
                                "selectedSubject",
                                e.target.value
                              )
                            }
                            className="w-full bg-green-600/30 border border-green-500/40 rounded-lg py-2 px-3 text-white text-sm focus:outline-none focus:ring-2 focus:ring-green-500/50 focus:border-green-500/60"
                          />
                        </div>

                        <div>
                          <label className="block text-xs text-white/70 mb-1">
                            {t("Topic")}
                          </label>
                          <input
                            type="text"
                            placeholder={t("Enter a topic to explore")}
                            value={eduMentorProfile.topic}
                            onChange={(e) =>
                              handleEduMentorProfileChange(
                                "topic",
                                e.target.value
                              )
                            }
                            className="w-full bg-green-600/30 border border-green-500/40 rounded-lg py-2 px-3 text-white text-sm focus:outline-none focus:ring-2 focus:ring-green-500/50 focus:border-green-500/60"
                          />
                        </div>
                      </div>

                      {/* Learning Options */}
                      <div className="mb-4">
                        <h4 className="text-sm font-medium text-white/90 mb-2 flex items-center">
                          <Settings size={14} className="mr-1.5 text-green-400" />
                          {t("Learning Options")}
                        </h4>

                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <label className="text-xs text-white/70">
                              {t("Include Wikipedia Sources")}
                            </label>
                            <input
                              type="checkbox"
                              checked={eduMentorProfile.includeWikipedia}
                              onChange={(e) =>
                                handleEduMentorProfileChange(
                                  "includeWikipedia",
                                  e.target.checked
                                )
                              }
                              className="w-4 h-4 text-green-600 bg-green-600/30 border-green-500/40 rounded focus:ring-green-500/50 focus:ring-2"
                            />
                          </div>

                          <div className="flex items-center justify-between">
                            <label className="text-xs text-white/70">
                              {t("Use Knowledge Store")}
                            </label>
                            <input
                              type="checkbox"
                              checked={eduMentorProfile.useKnowledgeStore}
                              onChange={(e) =>
                                handleEduMentorProfileChange(
                                  "useKnowledgeStore",
                                  e.target.checked
                                )
                              }
                              className="w-4 h-4 text-green-600 bg-green-600/30 border-green-500/40 rounded focus:ring-green-500/50 focus:ring-2"
                            />
                          </div>

                          <div className="flex items-center justify-between">
                            <label className="text-xs text-white/70">
                              {t("Use Orchestration Engine")}
                            </label>
                            <input
                              type="checkbox"
                              checked={eduMentorProfile.useOrchestration}
                              onChange={(e) =>
                                handleEduMentorProfileChange(
                                  "useOrchestration",
                                  e.target.checked
                                )
                              }
                              className="w-4 h-4 text-green-600 bg-green-600/30 border-green-500/40 rounded focus:ring-green-500/50 focus:ring-2"
                            />
                          </div>
                        </div>
                      </div>

                      <div className="mt-4 text-center">
                        <div className="inline-flex items-center justify-center px-4 py-2 bg-green-500/20 border border-green-500/30 rounded-lg text-green-300">
                          <Clock size={16} className="mr-2" />
                          <span>
                            {t("Fill in your learning preferences and use the \"Generate Lesson\" button below to create personalized educational content")}
                          </span>
                        </div>
                      </div>
                    </div>
                  )}

                {/* Financial Simulation Running Message */}
                {selectedAgent &&
                  agents.find((a) => a.id === selectedAgent)?.type ===
                    "financial" &&
                  isSimulating && (
                    <div className="mb-4 bg-blue-900/20 rounded-lg p-4 border border-blue-500/30">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center">
                          <div className="animate-pulse mr-2 w-3 h-3 rounded-full bg-blue-400"></div>
                          <p className="text-blue-300 font-medium">
                            {t("Financial simulation in progress...")}
                          </p>
                        </div>
                        {isProcessingSimulation && (
                          <span className="text-xs text-blue-300">
                            {simulationProgress}% {t("complete")}
                          </span>
                        )}
                      </div>

                      {/* Progress bar */}
                      {isProcessingSimulation && (
                        <div className="w-full h-2 bg-blue-900/50 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-blue-500 rounded-full transition-all duration-500 ease-out"
                            style={{ width: `${simulationProgress}%` }}
                          ></div>
                        </div>
                      )}
                    </div>
                  )}

                {/* Wellness Bot Form - Always show when Wellness Agent is selected */}
                {selectedAgent &&
                  agents.find((a) => a.id === selectedAgent)?.type ===
                    "wellness" && (
                    <div className="mb-4 bg-orange-900/20 rounded-lg p-4 border border-orange-500/30 h-[calc(100%-8rem)] overflow-y-auto custom-scrollbar">
                        <h3 className="text-lg font-semibold text-white mb-3 flex items-center">
                        <Heart size={18} className="mr-2 text-orange-400" />
                        {t("Wellness Assistant")}
                      </h3>





                      {/* Wellness Type Selector */}
                      <div className="mb-4">
                        <div className="flex gap-2 mb-3">
                          <button
                            onClick={() => handleWellnessProfileChange("wellnessType", "emotional")}
                            className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                              wellnessProfile.wellnessType === "emotional"
                                ? "bg-orange-500 text-white"
                                : "bg-gray-700/50 text-white/70 hover:bg-gray-700/70"
                            }`}
                          >
                            <Heart size={16} className="inline mr-1" />
                            {t("Emotional Wellness")}
                          </button>
                          <button
                            onClick={() => handleWellnessProfileChange("wellnessType", "financial")}
                            className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                              wellnessProfile.wellnessType === "financial"
                                ? "bg-orange-500 text-white"
                                : "bg-gray-700/50 text-white/70 hover:bg-gray-700/70"
                            }`}
                          >
                            <DollarSign size={16} className="inline mr-1" />
                            {t("Financial Wellness")}
                          </button>
                        </div>
                      </div>

                      {/* Emotional Wellness Controls */}
                      {wellnessProfile.wellnessType === "emotional" && (
                        <div className="mb-4 space-y-3">
                          <div>
                            <label className="block text-sm font-medium text-white/80 mb-2">
                              {t("Current Mood Score")}: {wellnessProfile.moodScore}/10
                            </label>
                            <input
                              type="range"
                              min="1"
                              max="10"
                              value={wellnessProfile.moodScore}
                              onChange={(e) => handleWellnessProfileChange("moodScore", parseInt(e.target.value))}
                              className="w-full h-2 bg-orange-200 rounded-lg appearance-none cursor-pointer"
                            />
                            <div className="flex justify-between text-xs text-white/60 mt-1">
                              <span>{t("Very Low")}</span>
                              <span>{t("Excellent")}</span>
                            </div>
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-white/80 mb-2">
                              {t("Stress Level")}: {wellnessProfile.stressLevel}/10
                            </label>
                            <input
                              type="range"
                              min="1"
                              max="10"
                              value={wellnessProfile.stressLevel}
                              onChange={(e) => handleWellnessProfileChange("stressLevel", parseInt(e.target.value))}
                              className="w-full h-2 bg-orange-200 rounded-lg appearance-none cursor-pointer"
                            />
                            <div className="flex justify-between text-xs text-white/60 mt-1">
                              <span>{t("Very Low")}</span>
                              <span>{t("Very High")}</span>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Wellness Query Input */}
                      <div className="mb-4">
                        <label className="block text-sm font-medium text-white/80 mb-2">
                          {t("Your Wellness Question or Concern")}
                        </label>
                        <textarea
                          value={wellnessQuery || ""}
                          onChange={(e) => setWellnessQuery(e.target.value)}
                          placeholder={t("Describe your wellness concern or ask for guidance...")}
                          className="w-full bg-gray-800/50 border border-gray-700/50 rounded-lg px-4 py-3 text-white placeholder-white/50 focus:outline-none focus:border-orange-500/50 resize-none"
                          rows="4"
                        />
                      </div>

                      {/* Get Wellness Guidance Button */}
                      <button
                        onClick={handleWellnessQuery}
                        disabled={!wellnessQuery?.trim() || isWellnessLoading}
                        className={`w-full py-3 px-4 rounded-lg font-medium transition-all ${
                          wellnessQuery?.trim() && !isWellnessLoading
                            ? "bg-orange-500 hover:bg-orange-600 text-white"
                            : "bg-gray-700/50 text-white/50 cursor-not-allowed"
                        }`}
                      >
                        {isWellnessLoading ? t("Getting guidance...") : t("Get Wellness Guidance")}
                      </button>

                      <div className="mt-4 text-center">
                        <div className="inline-flex items-center justify-center px-4 py-2 bg-orange-500/20 border border-orange-500/30 rounded-lg text-orange-300">
                          <Clock size={16} className="mr-2" />
                          <span>
                            {t("Fill in your wellness details and press Get Wellness Guidance to begin your wellness session")}
                          </span>
                        </div>
                      </div>
                    </div>
                  )}

                {/* Wellness Bot Simulation Running Message */}
                {selectedAgent &&
                  agents.find((a) => a.id === selectedAgent)?.type ===
                    "wellness" &&
                  isSimulating && (
                    <div className="mb-4 bg-orange-900/20 rounded-lg p-4 border border-orange-500/30">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center">
                          <div className="animate-pulse mr-2 w-3 h-3 rounded-full bg-orange-400"></div>
                          <p className="text-orange-300 font-medium">
                            {isWellnessLoading ? t("Getting wellness guidance...") : t("Wellness session in progress...")}
                          </p>
                        </div>
                        <span className="text-xs text-orange-300">
                          {isWellnessLoading ? t("AI processing your request") : t("Ready for wellness queries")}
                        </span>
                      </div>

                      <div className="text-xs text-orange-200/70 mt-2">
                        {t("Type")}: {wellnessProfile.wellnessType === "emotional" ? t("Emotional Wellness") : t("Financial Wellness")}
                        {wellnessProfile.wellnessType === "emotional" && (
                          <span className="ml-2">
                            • {t("Mood")}: {wellnessProfile.moodScore}/10 • {t("Stress")}: {wellnessProfile.stressLevel}/10
                          </span>
                        )}
                      </div>


                    </div>
                  )}

                {/* Session Activity Log - Only show when not showing agent forms or when simulating */}
                {(!selectedAgent ||
                  (agents.find((a) => a.id === selectedAgent)?.type !==
                    "financial" &&
                   agents.find((a) => a.id === selectedAgent)?.type !==
                    "education" &&
                   agents.find((a) => a.id === selectedAgent)?.type !==
                    "wellness") ||
                  isSimulating) && (
                  <div>
                    {messages.length > 0 ? (
                      <div className="overflow-y-auto custom-scrollbar px-1 h-[calc(100%-35rem)] timeline-list-container" style={{ minHeight: "120px" }}>
                        <div className="timeline-container" ref={timelineRef}>
                          {messages.map((message) => (
                            <div key={`timeline-${message.id}`}>
                              {renderTimelineItem(message)}
                            </div>
                          ))}
                        </div>
                      </div>
                    ) : !selectedAgent ? (
                      <div className="flex-1 flex items-center justify-center">
                        <div className="text-center text-white/60 text-sm">
                          {t("Your agent inputs will be shown here to configure")}
                        </div>
                      </div>
                    ) : (
                      <div className="text-center text-white/60 text-sm">
                        {t("Start your session to see activity")}
                      </div>
                    )}
                  </div>
                )}

                {/* Agent Controls */}
                <div className="mt-4 space-y-2">
                  <div className="flex space-x-2">
                    {/* Show different controls based on selected agent */}
                    {selectedAgent && agents.find((a) => a.id === selectedAgent)?.type === "education" ? (
                      /* Education Agent Controls */
                      <>
                        <button
                          onClick={generateEduMentorLesson}
                          disabled={isGeneratingLesson || !eduMentorProfile.selectedSubject.trim() || !eduMentorProfile.topic.trim()}
                          className={`flex-1 py-2 px-4 rounded-lg flex items-center justify-center transition-colors font-medium ${
                            isGeneratingLesson || !eduMentorProfile.selectedSubject.trim() || !eduMentorProfile.topic.trim()
                              ? 'bg-gray-600/50 text-gray-400 cursor-not-allowed'
                              : 'bg-emerald-600 hover:bg-emerald-700 text-white'
                          }`}
                        >
                          {isGeneratingLesson ? (
                            <>
                              <div className="animate-spin rounded-full h-4 w-4 border-2 border-white/30 border-t-white mr-2"></div>
                              {t("Generating...")}
                            </>
                          ) : (
                            <>
                              <BookOpen size={16} className="mr-2" />
                              {t("Generate Lesson")}
                            </>
                          )}
                        </button>
                        {lessonData && (
                          <button
                            onClick={() => {
                              setLessonData(null);
                              setLessonTaskId(null);
                              toast.success(t("Lesson cleared. Ready to generate new content."));
                            }}
                            className="bg-gray-600 hover:bg-gray-700 text-white py-2 px-4 rounded-lg flex items-center justify-center transition-colors"
                          >
                            <RotateCcw size={16} className="mr-2" />
                            {t("New Lesson")}
                          </button>
                        )}
                      </>
                    ) : selectedAgent && agents.find((a) => a.id === selectedAgent)?.type === "wellness" ? (
                      /* Wellness Agent Controls */
                      <>
                        <button
                          type="button"
                          onClick={(e) => {
                            e.preventDefault();
                            e.stopPropagation();
                            console.log("Get Wellness Guidance button clicked", { 
                              wellnessQuery: wellnessQuery.trim(), 
                              wellnessQueryLength: wellnessQuery.trim().length,
                              isWellnessLoading,
                              wellnessProfile 
                            });
                            if (!isWellnessLoading && wellnessQuery.trim()) {
                              handleWellnessQuery();
                            } else {
                              console.warn("Button click ignored:", { 
                                isWellnessLoading, 
                                hasQuery: !!wellnessQuery.trim() 
                              });
                            }
                          }}
                          disabled={isWellnessLoading || !wellnessQuery.trim()}
                          className={`flex-1 py-2 px-4 rounded-lg flex items-center justify-center transition-colors font-medium ${
                            isWellnessLoading || !wellnessQuery.trim()
                              ? 'bg-gray-600/50 text-gray-400 cursor-not-allowed'
                              : 'bg-orange-600 hover:bg-orange-700 text-white cursor-pointer'
                          }`}
                        >
                          {isWellnessLoading ? (
                            <>
                              <div className="animate-spin rounded-full h-4 w-4 border-2 border-white/30 border-t-white mr-2"></div>
                              {t("Getting Guidance...")}
                            </>
                          ) : (
                            <>
                              <Sparkles size={16} className="mr-2" />
                              {t("Get Wellness Guidance")}
                            </>
                          )}
                        </button>
                        <button
                          onClick={() => {
                            setWellnessQuery("");
                            setWellnessResponse(null);
                            toast.success(t("Wellness query cleared. Ready for new input."));
                          }}
                          className="bg-gray-600 hover:bg-gray-700 text-white py-2 px-4 rounded-lg flex items-center justify-center transition-colors"
                        >
                          <RotateCcw size={16} className="mr-2" />
                          {t("Clear")}
                        </button>
                      </>
                    ) : selectedAgent ? (
                      /* Default Agent Controls - Only show when an agent is selected */
                      <>
                        {!isSimulating ? (
                          <button
                            onClick={startSimulation}
                            className="flex-1 bg-orange-500 hover:bg-orange-600 text-white py-2 px-4 rounded-lg flex items-center justify-center transition-colors"
                          >
                            <Play size={16} className="mr-2" />
                            {t("Start")}
                          </button>
                        ) : (
                          <button
                            onClick={stopSimulation}
                            className="flex-1 bg-gray-600 hover:bg-gray-700 text-white py-2 px-4 rounded-lg flex items-center justify-center transition-colors"
                          >
                            <Pause size={16} className="mr-2" />
                            {t("Pause")}
                          </button>
                        )}
                        <button
                          onClick={resetSimulation}
                          className="bg-gray-700 hover:bg-gray-800 text-white py-2 px-4 rounded-lg flex items-center justify-center transition-colors"
                        >
                          <RotateCcw size={16} />
                        </button>
                      </>
                    ) : null}
                  </div>
                </div>
              </div>
            </div>

            {/* Main Interaction Panel - Expands when agent is active */}
            <div
              className={`${
                isSimulating ? "lg:col-span-9" : "lg:col-span-6"
              } h-full overflow-hidden transition-all duration-300`}
            >
              <div className="bg-white/5 backdrop-blur-sm rounded-xl border border-white/10 shadow-lg h-full p-4 flex flex-col overflow-hidden">
                <div className="flex justify-between items-center mb-6">
                  <div className="flex items-center">
                    <div className="w-8 h-8 rounded-full bg-orange-500/20 flex items-center justify-center mr-2">
                      <MessageSquare size={18} className="text-orange-400" />
                    </div>
                    <h2 className="text-xl font-bold text-white">
                      {selectedAgent && isSimulating
                        ? (() => {
                            const activeAgent = agents.find(
                              (a) => a.id === selectedAgent
                            );
                            if (!activeAgent) return t("Agent Interaction");

                            // Return appropriate title based on agent type
                            switch (activeAgent.type) {
                              case "financial":
                                return simulationResults
                                  ? t("Financial Simulation Results")
                                  : t("Financial Agent");
                              case "education":
                                return t("Education Resources");
                              case "wellness":
                                return t("Wellness Insights");
                              default:
                                return `${activeAgent.name} ${t("Interaction")}`;
                            }
                          })()
                        : t("Agent Interaction")}
                    </h2>

                    {/* Agent-specific badges */}
                    {selectedAgent &&
                      isSimulating &&
                      (() => {
                        const activeAgent = agents.find(
                          (a) => a.id === selectedAgent
                        );
                        if (!activeAgent) return null;

                        switch (activeAgent.type) {
                          case "financial":
                            return (
                              simulationResults && (
                                <div className="ml-4 flex items-center">
                                  <div className="flex items-center bg-black/30 rounded-lg overflow-hidden">
                                    <button
                                      onClick={() => {
                                        const availableMonths =
                                          getAvailableMonths(simulationResults);
                                        const currentIndex =
                                          availableMonths.indexOf(currentMonth);
                                        if (currentIndex > 0) {
                                          setCurrentMonth(
                                            availableMonths[currentIndex - 1]
                                          );
                                        }
                                      }}
                                      disabled={
                                        getAvailableMonths(
                                          simulationResults
                                        ).indexOf(currentMonth) === 0
                                      }
                                      className="p-1.5 text-white/70 hover:text-white/100 hover:bg-black/20 disabled:opacity-50 disabled:cursor-not-allowed"
                                    >
                                      <ArrowLeft size={14} />
                                    </button>

                                    <div className="px-2 py-1 text-sm font-medium text-white/90">
                                      {currentMonth <= 12
                                        ? `${t("Month")} ${currentMonth}`
                                        : `${t("Future")} ${currentMonth - 12}`}
                                    </div>

                                    <button
                                      onClick={() => {
                                        const availableMonths =
                                          getAvailableMonths(simulationResults);
                                        const currentIndex =
                                          availableMonths.indexOf(currentMonth);
                                        if (
                                          currentIndex <
                                          availableMonths.length - 1
                                        ) {
                                          setCurrentMonth(
                                            availableMonths[currentIndex + 1]
                                          );
                                        }
                                      }}
                                      disabled={
                                        getAvailableMonths(
                                          simulationResults
                                        ).indexOf(currentMonth) ===
                                        getAvailableMonths(simulationResults)
                                          .length -
                                          1
                                      }
                                      className="p-1.5 text-white/70 hover:text-white/100 hover:bg-black/20 disabled:opacity-50 disabled:cursor-not-allowed"
                                    >
                                      <ArrowRight size={14} />
                                    </button>
                                  </div>
                                </div>
                              )
                            );
                          case "education":
                            return (
                              <div className="ml-4 flex items-center">
                                <span className="text-sm text-emerald-300 bg-emerald-500/20 px-3 py-1 rounded-full">
                                  {t("Learning Resources")}
                                </span>
                              </div>
                            );
                          case "wellness":
                            return (
                              <div className="ml-4 flex items-center">
                                <span className="text-sm text-orange-300 bg-orange-500/20 px-3 py-1 rounded-full">
                                  {t("Wellness Plan")}
                                </span>
                              </div>
                            );
                          default:
                            return null;
                        }
                      })()}
                  </div>

                  {/* Agent-specific action buttons */}
                  <div>
                    {selectedAgent &&
                      (() => {
                        const activeAgent = agents.find(
                          (a) => a.id === selectedAgent
                        );
                        if (!activeAgent || !isSimulating) return null;

                        switch (activeAgent.type) {
                          case "financial":
                            return (
                              <button
                                onClick={fetchSimulationResults}
                                disabled={isLoadingResults}
                                className="flex items-center px-3 py-1.5 bg-blue-500/20 hover:bg-blue-500/30 text-blue-300 rounded-lg text-sm transition-colors"
                                title={t("Refresh financial simulation results")}
                              >
                                {isLoadingResults ? (
                                  <div className="animate-pulse w-2 h-2 rounded-full bg-blue-400 mr-2"></div>
                                ) : (
                                  <RotateCcw size={14} className="mr-2" />
                                )}
                                <span>{t("Refresh")}</span>
                              </button>
                            );
                          case "education":
                            return (
                              <button className="flex items-center px-3 py-1.5 bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 rounded-lg text-sm transition-colors">
                                <BookOpen size={14} className="mr-2" />
                                <span>{t("Resources")}</span>
                              </button>
                            );
                          case "wellness":
                            return (
                              <button className="flex items-center px-3 py-1.5 bg-orange-500/20 hover:bg-orange-500/30 text-orange-300 rounded-lg text-sm transition-colors">
                                <Heart size={14} className="mr-2" />
                                <span>{t("Plan")}</span>
                              </button>
                            );
                          default:
                            return null;
                        }
                      })()}
                  </div>
                </div>

                {/* Messages Area */}
                <div className="overflow-y-auto custom-scrollbar px-1 h-[calc(100%-8rem)] message-list-container">
                  {messages.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-gray-400">
                      {!selectedAgent ? (
                        <>
                          <div className="w-16 h-16 rounded-full bg-orange-500/20 flex items-center justify-center mb-4">
                            <MessageSquare size={32} className="text-orange-400" />
                          </div>
                          <p className="text-center font-medium text-lg mb-2 text-white">{t("Welcome to Agent Simulator")}</p>
                          <p className="text-center text-sm text-gray-300 max-w-md mb-6">
                            {t("Select an agent from the right panel to begin your interactive session. Each agent specializes in different areas to help you achieve your goals.")}
                          </p>

                        </>
                      ) : (
                        <>
                          <Sparkles size={40} className="mb-4 text-orange-500/50" />
                          <p className="text-center">
                            {isSimulating
                              ? t("Start the simulation to begin agent interaction")
                              : t("Upload a PDF or send a message to start learning")}
                          </p>
                          <p className="text-center text-sm mt-2">
                            {isSimulating
                              ? "Agents will collaborate to solve tasks"
                              : "Our AI will analyze your documents and answer your questions"}
                          </p>
                        </>
                      )}
                    </div>
                  ) : (
                    <div>
                      {messages.map((message) => (
                        <div key={message.id}>{renderMessage(message)}</div>
                      ))}

                      {/* Show agent-specific content based on agent type */}
                      {selectedAgent &&
                        (() => {
                          const activeAgent = agents.find(
                            (a) => a.id === selectedAgent
                          );
                          if (!activeAgent) return null;

                          switch (activeAgent.type) {
                            case "financial":
                              // Show simulation results if available
                              return simulationResults ? renderSimulationResults() : null;
                            case "education":
                              return (
                                <div className="bg-emerald-900/20 rounded-lg p-4 my-4 border border-emerald-500/30">
                                  <div className="flex items-center mb-4">
                                    <h3 className="text-lg font-semibold text-white flex items-center">
                                      <BookOpen
                                        size={18}
                                        className="mr-2 text-emerald-400"
                                      />
                                      {lessonData ? lessonData.title || `${eduMentorProfile.selectedSubject}: ${eduMentorProfile.topic}` : "EduMentor Learning Assistant"}
                                    </h3>
                                    {lessonData && (
                                      <div className="ml-auto">
                                        <span className="bg-emerald-500/20 text-emerald-300 px-2 py-1 rounded-full text-xs font-medium">
                                          ✅ Lesson Generated
                                        </span>
                                      </div>
                                    )}
                                  </div>

                                  {lessonData ? (
                                    <div className="space-y-4">
                                      {/* Subject and Topic Info */}
                                      <div className="bg-emerald-800/20 rounded-lg p-3 border border-emerald-600/30">
                                        <div className="text-emerald-300 text-sm font-medium mb-1">Learning Session</div>
                                        <div className="text-white/90">
                                          <span className="font-medium">Subject:</span> {eduMentorProfile.selectedSubject}
                                        </div>
                                        <div className="text-white/90">
                                          <span className="font-medium">Topic:</span> {eduMentorProfile.topic}
                                        </div>
                                      </div>

                                      {/* Lesson Content - Handle multiple possible field names */}
                                      {(lessonData.explanation || lessonData.content || lessonData.text) && (
                                        <div className="bg-white/10 p-4 rounded-lg border border-amber-500/30">
                                          <h4 className="text-amber-400 font-semibold mb-2 flex items-center">
                                            <span className="bg-amber-500 w-6 h-6 rounded-full flex items-center justify-center mr-2 text-white text-sm font-bold">1</span>
                                            Explanation
                                          </h4>
                                          <p className="text-white/90 leading-relaxed whitespace-pre-wrap">
                                            {lessonData.explanation || lessonData.content || lessonData.text}
                                          </p>
                                        </div>
                                      )}

                                      {/* Activity - Handle both object and other formats */}
                                      {(lessonData.activity || lessonData.enhanced_features?.activity) && (
                                        <div className="bg-indigo-900/30 p-4 rounded-lg border border-indigo-500/30">
                                          <h4 className="text-indigo-400 font-semibold mb-2 flex items-center">
                                            <span className="bg-indigo-500 w-6 h-6 rounded-full flex items-center justify-center mr-2 text-white text-sm font-bold">2</span>
                                            Activity
                                          </h4>
                                          {renderActivityContent(lessonData.activity || lessonData.enhanced_features?.activity)}
                                        </div>
                                      )}

                                      {/* Question */}
                                      {lessonData.question && (
                                        <div className="bg-amber-900/30 p-4 rounded-lg border border-amber-500/30">
                                          <h4 className="text-amber-400 font-semibold mb-2 flex items-center">
                                            <span className="bg-amber-500 w-6 h-6 rounded-full flex items-center justify-center mr-2 text-white text-sm font-bold">3</span>
                                            Question to Consider
                                          </h4>
                                          {renderQuestionContent(lessonData.question)}
                                        </div>
                                      )}

                                      {/* Show raw content if no structured fields exist */}
                                      {!lessonData.explanation && !lessonData.content && !lessonData.text && 
                                       !lessonData.activity && !lessonData.enhanced_features?.activity && 
                                       !lessonData.question && (
                                        <div className="bg-white/10 p-4 rounded-lg border border-amber-500/30">
                                          <h4 className="text-amber-400 font-semibold mb-2 flex items-center">
                                            <span className="bg-amber-500 w-6 h-6 rounded-full flex items-center justify-center mr-2 text-white text-sm font-bold">📚</span>
                                            Lesson Content
                                          </h4>
                                          <div className="text-white/90 leading-relaxed">
                                            <p className="mb-2">Lesson data received but content structure is unexpected.</p>
                                            <details className="mt-2">
                                              <summary className="cursor-pointer text-amber-300 hover:text-amber-200 text-sm">
                                                View raw data (for debugging)
                                              </summary>
                                              <pre className="mt-2 text-xs bg-black/30 p-2 rounded overflow-auto max-h-40">
                                                {JSON.stringify(lessonData, null, 2)}
                                              </pre>
                                            </details>
                                          </div>
                                        </div>
                                      )}

                                      {/* Quiz if available */}
                                      {lessonData.quiz && lessonData.quiz.length > 0 && (
                                        <div className="bg-purple-900/30 p-4 rounded-lg border border-purple-500/30">
                                          <h4 className="text-purple-400 font-semibold mb-3 flex items-center">
                                            <span className="bg-purple-500 w-6 h-6 rounded-full flex items-center justify-center mr-2 text-white text-sm font-bold">Q</span>
                                            Quiz Questions
                                          </h4>
                                          <div className="space-y-3">
                                            {lessonData.quiz.slice(0, 3).map((quizItem, index) => (
                                              <div key={index} className="bg-purple-800/20 p-3 rounded-lg">
                                                <p className="text-white/90 font-medium mb-2">{index + 1}. {quizItem.question}</p>
                                                {quizItem.options && (
                                                  <div className="space-y-1">
                                                    {quizItem.options.map((option, optIndex) => (
                                                      <div key={optIndex} className="text-white/70 text-sm">
                                                        {String.fromCharCode(65 + optIndex)}. {option}
                                                      </div>
                                                    ))}
                                                  </div>
                                                )}
                                              </div>
                                            ))}
                                          </div>
                                        </div>
                                      )}

                                      {/* Generation Info */}
                                      <div className="bg-emerald-800/20 rounded-lg p-3 border border-emerald-600/30">
                                        <div className="flex items-center justify-between text-xs text-emerald-300">
                                          <span>
                                            Generated using {integrationStatus?.integration_status?.overall_valid && eduMentorProfile.useOrchestration ? 'Enhanced AI Orchestration' : 'Basic Lesson Generation'}
                                          </span>
                                          {lessonTaskId && (
                                            <span>Task: {lessonTaskId.substring(0, 8)}...</span>
                                          )}
                                        </div>
                                      </div>
                                    </div>
                                  ) : (
                                    <div className="text-center py-6">
                                      <div className="text-white/70 mb-4">
                                        <BookOpen size={48} className="mx-auto mb-3 text-emerald-400/50" />
                                        <p className="text-lg font-medium mb-2">Ready to Generate Your Lesson</p>
                                        <p className="text-sm">
                                          Fill in the subject and topic in the form above, then click "Generate Lesson" to create personalized educational content.
                                        </p>
                                      </div>

                                      {eduMentorProfile.selectedSubject && eduMentorProfile.topic && (
                                        <div className="bg-emerald-800/20 rounded-lg p-3 border border-emerald-600/30 mb-4">
                                          <div className="text-emerald-300 text-sm font-medium mb-1">Ready to Generate:</div>
                                          <div className="text-white/90">
                                            <span className="font-medium">Subject:</span> {eduMentorProfile.selectedSubject}
                                          </div>
                                          <div className="text-white/90">
                                            <span className="font-medium">Topic:</span> {eduMentorProfile.topic}
                                          </div>
                                        </div>
                                      )}

                                      <button
                                        onClick={generateEduMentorLesson}
                                        disabled={isGeneratingLesson || !eduMentorProfile.selectedSubject.trim() || !eduMentorProfile.topic.trim()}
                                        className={`px-6 py-3 rounded-lg font-medium transition-all duration-300 ${
                                          isGeneratingLesson || !eduMentorProfile.selectedSubject.trim() || !eduMentorProfile.topic.trim()
                                            ? 'bg-gray-600/30 text-gray-400 cursor-not-allowed'
                                            : 'bg-emerald-600/40 hover:bg-emerald-600/60 text-emerald-200 hover:text-white border border-emerald-500/40 hover:border-emerald-400/60'
                                        }`}
                                      >
                                        {isGeneratingLesson ? (
                                          <div className="flex items-center">
                                            <div className="animate-spin rounded-full h-5 w-5 border-2 border-emerald-300/30 border-t-emerald-300 mr-2"></div>
                                            Generating Lesson...
                                          </div>
                                        ) : (
                                          <div className="flex items-center">
                                            <BookOpen size={18} className="mr-2" />
                                            Generate Lesson
                                          </div>
                                        )}
                                      </button>
                                    </div>
                                  )}
                                </div>
                              );
                            case "wellness":
                              // Only show wellness guidance component at the very start when there are no messages
                              // Once any message appears (user or bot), hide this component completely
                              // Filter out system messages to check for actual conversation messages
                              const hasAnyMessages = messages.some(msg => 
                                msg.sender === "user" || 
                                msg.sender === "wellness-agent" || 
                                msg.agentType === "wellness" ||
                                (msg.sender !== "system" && msg.sender !== "learning-agent")
                              );
                              
                              // Hide the component once any conversation has started
                              if (hasAnyMessages) {
                                return null; // Don't show after conversation starts
                              }
                              
                              // Only show at the very beginning when no messages exist
                              return (
                                <div className="bg-orange-900/20 rounded-lg p-4 my-4 border border-orange-500/30">
                                  <div className="flex items-center justify-between mb-4">
                                    <h3 className="text-lg font-semibold text-white flex items-center">
                                      <Heart
                                        size={18}
                                        className="mr-2 text-orange-400"
                                      />
                                      Wellness Guidance
                                    </h3>
                                  </div>

                                  <div className="text-center py-6">
                                    <div className="text-white/70 mb-4">
                                      <Heart size={48} className="mx-auto mb-3 text-orange-400/50" />
                                      <p className="text-lg font-medium mb-2">Ready for Wellness Guidance</p>
                                      <p className="text-sm">
                                        Fill in your wellness details in the timeline form and click "Get Wellness Guidance" to receive personalized support.
                                      </p>
                                    </div>
                                  </div>
                                </div>
                              );
                            default:
                              return null;
                          }
                        })()}

                      <div ref={messagesEndRef} />
                    </div>
                  )}
                </div>

                {/* Input Area - ChatBot Style - Only show when agent is selected and not wellness/education/financial */}
                {selectedAgent && (() => {
                  const activeAgent = agents.find((a) => a.id === selectedAgent);
                  // Hide input area for wellness, education, and financial bots
                  if (activeAgent && (activeAgent.type === "wellness" || activeAgent.type === "education" || activeAgent.type === "financial")) {
                    return false;
                  }
                  return true;
                })() && (
                <div className="mt-4 relative">
                  {/* PDF display area - only show when PDFs are selected */}
                  {!isSimulating && selectedPdfs.length > 0 && (
                    <div className="mb-2 pdf-upload-area overflow-x-auto whitespace-nowrap pb-2 custom-scrollbar">
                      <div className="flex gap-2 px-1">
                        {selectedPdfs.map((pdf) => (
                          <div
                            key={pdf.id}
                            className={`inline-flex items-center rounded-lg px-2 py-1.5 text-sm cursor-pointer pdf-item flex-shrink-0 ${
                              activePdfId === pdf.id
                                ? "bg-purple-900/40 border border-purple-500/50 active"
                                : "bg-gray-800/40 border border-gray-700/50 hover:bg-gray-700/40"
                            }`}
                            onClick={() => setActivePdfId(pdf.id)}
                          >
                            <FileText
                              size={14}
                              className="mr-1.5 text-purple-400"
                            />
                            <span className="text-white truncate max-w-[120px]">
                              {pdf.name}
                            </span>
                            <span className="text-white/50 text-xs ml-1.5">
                              {(pdf.size / 1024).toFixed(1)} KB
                            </span>
                            <button
                              onClick={(e) => {
                                e.stopPropagation(); // Prevent triggering the parent onClick
                                handleRemovePdf(pdf.id);
                              }}
                              className="ml-2 p-1 rounded-full pdf-remove-button"
                            >
                              <X size={12} className="text-white/70" />
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  <div
                    className="flex items-center p-2 rounded-2xl"
                    style={{
                      background: "rgba(255, 255, 255, 0.1)",
                      backdropFilter: "blur(10px)",
                      border: "1px solid rgba(255, 255, 255, 0.18)",
                    }}
                  >
                    {/* PDF Upload button - only show when not simulating */}
                    {!isSimulating && (
                      <>
                        <input
                          type="file"
                          ref={fileInputRef}
                          onChange={handleFileChange}
                          accept=".pdf"
                          className="hidden"
                        />
                        <button
                          onClick={() => fileInputRef.current?.click()}
                          className={`p-2 mx-1 rounded-lg hover:bg-white/10 transition-colors relative ${
                            activePdfId ? "bg-purple-900/20" : ""
                          }`}
                          title={t("Pin a PDF for chat")}
                        >
                          <Pin
                            size={20}
                            className="text-purple-400 pdf-upload-icon"
                          />
                          {activePdfId && (
                            <span className="absolute top-0 right-0 w-2 h-2 bg-purple-500 rounded-full"></span>
                          )}
                        </button>
                      </>
                    )}

                    {/* Textarea with fixed height */}
                    <div className="flex-grow mx-2 min-w-0">
                      <textarea
                        value={userInput}
                        onChange={(e) => {
                          setUserInput(e.target.value);
                          // Auto-resize the textarea
                          e.target.style.height = "46px";
                        }}
                        onKeyDown={(e) => {
                          // Submit on Enter (without Shift)
                          if (e.key === "Enter" && !e.shiftKey) {
                            e.preventDefault();
                            handleSubmit(e);
                          }
                        }}
                        placeholder={
                          activePdfId
                            ? t("Ask questions about your PDF...")
                            : t("Send a message to learn...")
                        }
                        className="w-full bg-transparent text-white px-2 py-3 outline-none resize-none"
                        style={{
                          height: "46px", // Fixed height
                          lineHeight: "1.5",
                          overflowY: "auto",
                          overflowX: "hidden",
                          wordBreak: "break-word",
                          whiteSpace: "pre-wrap",
                        }}
                        rows="1"
                      />
                    </div>

                    {/* Send button */}
                    <button
                      onClick={handleSubmit}
                      type="button"
                      disabled={!userInput.trim()}
                      className="px-6 py-3 rounded-xl transition-all hover:scale-105 disabled:opacity-50 disabled:hover:scale-100 flex-shrink-0"
                      style={{
                        background: "rgba(255, 153, 51, 0.7)",
                        backdropFilter: "blur(10px)",
                        boxShadow: "0 4px 15px rgba(255, 153, 51, 0.3)",
                        color: "white",
                      }}
                    >
                      {t("Send")}
                    </button>
                  </div>
                  <div className="mt-2 text-center">
                    <p className="text-white/40 text-xs">
                      {t("Tip: Use Shift+Enter for a new line")}
                    </p>
                  </div>
                </div>
                )}
              </div>
            </div>

            {/* Agents Panel - Hidden when agent is active */}
            <div
              className={`lg:col-span-3 h-full overflow-hidden ${
                isSimulating ? "hidden lg:hidden" : "block"
              }`}
            >
              <div className="bg-white/5 backdrop-blur-sm rounded-xl border border-white/10 shadow-lg h-full p-4 flex flex-col overflow-hidden">
                <div className="flex justify-between items-center mb-6">
                  <div className="flex items-center">
                    <div className="w-8 h-8 rounded-full bg-orange-500/20 flex items-center justify-center mr-2">
                      <Cpu size={18} className="text-orange-400" />
                    </div>
                    <h2 className="text-xl font-bold text-white">
                      {t("Available Agents")}
                    </h2>
                  </div>
                </div>

                <div className="overflow-y-auto custom-scrollbar px-1 h-[calc(100%-4rem)] agent-list-container">
                  {agents.map((agent, index) => (
                    <div
                      key={agent.id}
                      className={`${
                        index === agents.length - 1 ? "mb-0" : "mb-4"
                      } mx-2 p-4 rounded-lg cursor-pointer transition-all transform hover:scale-[1.005] origin-center agent-card ${
                        agent.type
                      } ${selectedAgent === agent.id ? "selected-agent" : ""} ${
                        selectedAgent === agent.id
                          ? `bg-gradient-to-br from-${
                              agent.type === "education"
                                ? "emerald"
                                : agent.type === "financial"
                                ? "blue"
                                : "orange"
                            }-900/30 to-${
                              agent.type === "education"
                                ? "emerald"
                                : agent.type === "financial"
                                ? "blue"
                                : "orange"
                            }-800/10 border border-${
                              agent.type === "education"
                                ? "emerald"
                                : agent.type === "financial"
                                ? "blue"
                                : "orange"
                            }-500/30 shadow-lg`
                          : "bg-white/5 hover:bg-white/10 border border-white/5 hover:border-white/20"
                      }`}
                      style={{
                        boxShadow:
                          selectedAgent === agent.id
                            ? `0 4px 20px -2px ${agent.color}20`
                            : "",
                      }}
                      onClick={async () => {
                        // Check if switching to a different agent
                        const isSwitchingAgent = selectedAgent !== agent.id;
                        
                        // Always clear messages and start fresh when clicking an agent
                        setMessages([]);
                        
                        // Clear agent-specific state
                        setWellnessResponse(null);
                        setLessonData(null);
                        setLessonTaskId(null);
                        
                        // Set the selected agent first
                        setSelectedAgent(agent.id);
                        
                        // Update agent statuses - activate clicked agent, deactivate others
                        setAgents(
                          agents.map((a) => ({
                            ...a,
                            status: a.id === agent.id ? "active" : "idle",
                          }))
                        );

                        // Start simulation for the selected agent
                        setIsSimulating(true);
                        
                        // Add fresh start message for the new agent
                        const startMessage = {
                          id: generateUniqueId(),
                          sender: "system",
                          content: `${t("Agent simulation started.")} ${agent.name} ${t("is active and ready to assist.")}`,
                          timestamp: new Date().toISOString(),
                        };
                        setMessages([startMessage]);
                        
                        // Log agent start in Supabase
                        try {
                          const userId = user?.id || "anonymous-user";
                          await agentLogsService.logAgentStart({
                            userId,
                            agentId: agent.id,
                            agentName: agent.name,
                            agentType: agent.type,
                          });
                        } catch (error) {
                          console.error("Error logging agent start:", error);
                        }
                        
                        // Call the API to start the simulation
                        try {
                          const payload = {
                            agentId: agent.id,
                            userId: user?.id || "anonymous-user",
                          };
                          
                          // Add agent-specific profile data
                          if (agent.type === "financial") {
                            const { uniqueId: _uniqueId, ...financialProfileData } = financialProfile;
                            payload.financialProfile = financialProfileData;
                          } else if (agent.type === "education") {
                            payload.eduMentorProfile = eduMentorProfile;
                          } else if (agent.type === "wellness") {
                            payload.wellnessProfile = {
                              wellnessType: wellnessProfile.wellnessType,
                              moodScore: wellnessProfile.moodScore,
                              stressLevel: wellnessProfile.stressLevel,
                              wellnessGoals: wellnessProfile.wellnessGoals,
                              preferredActivities: wellnessProfile.preferredActivities,
                              stressTriggers: wellnessProfile.stressTriggers,
                              copingStrategies: wellnessProfile.copingStrategies,
                            };
                          }
                          
                          await startAgentSimulation(payload).unwrap();
                          toast.success(`${agent.name} ${t("is now active")}`);
                        } catch (error) {
                          console.error("Failed to start simulation:", error);
                          // Continue with local simulation even if API call fails
                          toast.success(`${agent.name} ${t("is now active")} (local mode)`);
                        }
                      }}
                    >
                      <div className="flex justify-between items-center">
                        <div className="flex items-center">
                          <div
                            className="w-10 h-10 rounded-full flex items-center justify-center mr-3 shadow-lg"
                            style={{
                              backgroundColor: `${agent.color}60`,
                              border: `2px solid ${agent.color}90`,
                              boxShadow: `0 0 10px ${agent.color}30`,
                            }}
                          >
                            {agent.icon && (
                              <agent.icon
                                size={22}
                                style={{ color: "white" }}
                                className="drop-shadow-lg"
                              />
                            )}
                          </div>
                          <div>
                            <h3 className="font-semibold text-white text-lg">
                              {t(agent.name)}
                            </h3>
                            <span
                              className="text-xs px-2 py-1 rounded-full font-medium"
                              style={{
                                backgroundColor: `${agent.color}50`,
                                color: "white",
                                border: `1px solid ${agent.color}80`,
                                boxShadow: `0 2px 4px ${agent.color}20`,
                              }}
                            >
                              {t(agent.type)}
                            </span>
                          </div>
                        </div>

                        <div className="flex">
                          <div
                            className={`px-3 py-1 rounded-full text-xs font-medium flex items-center ${
                              agent.status === "active"
                                ? "bg-green-500/40 text-white border border-green-500/60"
                                : "bg-gray-500/40 text-white border border-gray-500/60"
                            }`}
                          >
                            <span
                              className={`w-2.5 h-2.5 rounded-full mr-1.5 ${
                                agent.status === "active"
                                  ? "bg-green-400 shadow-[0_0_6px_rgba(74,222,128,0.6)]"
                                  : "bg-gray-400 shadow-[0_0_4px_rgba(156,163,175,0.4)]"
                              }`}
                            ></span>
                            {t(agent.status)}
                          </div>
                        </div>
                      </div>

                      {/* Agent description */}
                      <div className="mt-2 p-2 rounded-md bg-black/20 border border-white/5">
                        <p className="text-xs text-white/80 italic leading-tight">
                          "{t(agent.description)}"
                        </p>
                      </div>

                      {/* Confidence bar */}
                      <div className="mt-3">
                        <div className="flex justify-between items-center text-xs font-medium">
                          <span className="text-white/80">{t("Confidence")}</span>
                          <span
                            className="px-2 py-1 rounded-full font-medium"
                            style={{
                              backgroundColor: `${agent.color}50`,
                              color: "white",
                              border: `1px solid ${agent.color}80`,
                            }}
                          >
                            {formatConfidence(agent.confidence)}
                          </span>
                        </div>
                        <div className="confidence-bar mt-1.5 h-1.5 bg-white/10 rounded-full overflow-hidden">
                          <div
                            className="h-full rounded-full shadow-md"
                            style={{
                              width: `${agent.confidence * 100}%`,
                              background: `linear-gradient(90deg, ${agent.color}70, ${agent.color})`,
                              transition: "width 0.5s ease-in-out",
                            }}
                          ></div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </GlassContainer>
    </div>
  );
}
