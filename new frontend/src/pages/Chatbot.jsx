import React, { useState, useRef, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { useSelector, useDispatch } from "react-redux";
import GlassContainer from "../components/GlassContainer";
import ChatHistoryControls from "../components/ChatHistoryControls";
import { FiFile } from "react-icons/fi";
import { Volume2, VolumeX, Play, Send, Paperclip, MoreVertical, Menu } from "lucide-react";
import { toast } from "react-hot-toast";
import "../styles/chatbot.css";
import chatLogsService from "../services/chatLogsService";
import { CHAT_API_BASE_URL } from "../config";
import { useChatHistory } from "../hooks/useChatHistory";
import { useNavigationPersistence, useAuthPersistence } from "../hooks/useNavigationPersistence";
import { selectIsSpeaking, setIsSpeaking } from "../store/avatarSlice";
import { processChatbotMessage } from "../utils/karmaManager";
import { selectUser } from "../store/authSlice";
import MessageContent from "../components/MessageContent";

export default function Chatbot() {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const isSpeaking = useSelector(selectIsSpeaking);
  const user = useSelector(selectUser);

  // Use the chat history hook with session management
  const {
    messages,
    isLoading: historyLoading,
    userId,
    isInitialized,
    chatStats,
    addMessage,
    updateMessages,
    clearCurrentSession,
    clearAllHistory,
    getAllSessions,
    switchToSession,
    createNewSession,
    deleteSession,
    getCurrentSessionInfo,
  } = useChatHistory();

  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [currentStreamingMessage, setCurrentStreamingMessage] = useState("");
  const [selectedModel, setSelectedModel] = useState("grok"); // Default to grok model
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Mobile detection
  const [isMobile, setIsMobile] = useState(false);
  const [showMobileMenu, setShowMobileMenu] = useState(false);

  // TTS state management
  const [isTTSMuted, setIsTTSMuted] = useState(() => {
    return localStorage.getItem('chatbotTTSMuted') === 'true';
  });
  const [serviceHealthy, setServiceHealthy] = useState(false);
  const [ttsInitialized, setTtsInitialized] = useState(false);
  const [isGeneratingTTS, setIsGeneratingTTS] = useState(false);
  const [lastProcessedMessageId, setLastProcessedMessageId] = useState("");
  const [playingMessageId, setPlayingMessageId] = useState(null); // Track which individual message is playing

  // Navigation and auth persistence
  useNavigationPersistence();
  useAuthPersistence();

  // Mobile detection effect
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth <= 767);
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Check TTS service health on mount and when mute state changes
  useEffect(() => {
    const checkTTSHealth = async () => {
      try {
        // Check both TTS services - dedicated chatbot service and regular TTS service
        const dedicatedTTSService = (await import('../services/dedicatedChatbotTTSService')).default;
        const regularTTSService = (await import('../services/ttsService')).default;

        // Try dedicated chatbot service first (port 8002)
        let healthy = await dedicatedTTSService.checkServiceHealth();

        if (!healthy) {
          // Fallback to regular TTS service (port 8007)
          healthy = await regularTTSService.checkServiceHealth();
        }

        setServiceHealthy(healthy);

        if (healthy) {
          // Always enable auto-play on the service
          dedicatedTTSService.autoPlayEnabled = true;
          setTtsInitialized(true);

          // If not muted, ensure we're ready for auto-play
          if (!isTTSMuted) {
            // Force a small interaction to enable autoplay if needed
            try {
              const audio = new Audio();
              audio.volume = 0;
              const playPromise = audio.play();
              if (playPromise) {
                playPromise.catch(() => {
                  // Autoplay blocked, will be enabled after user interaction
                });
              }
            } catch (e) {
              // Ignore audio creation errors
            }
          }
        } else {
          setTtsInitialized(false);
        }
      } catch (error) {
        setServiceHealthy(false);
        setTtsInitialized(false);
      }
    };

    checkTTSHealth();

    // Re-check health periodically to handle service restarts
    const healthCheckInterval = setInterval(checkTTSHealth, 30000); // Check every 30 seconds

    return () => clearInterval(healthCheckInterval);
  }, [isTTSMuted]); // Re-run when mute state changes

  // Direct TTS function for speaking text
  const speakText = useCallback(async (text, messageId) => {
    if (!serviceHealthy || isTTSMuted || !text || !text.trim()) {
      return;
    }

    try {
      // Import TTS services dynamically
      const dedicatedTTSService = (await import('../services/dedicatedChatbotTTSService')).default;
      const regularTTSService = (await import('../services/ttsService')).default;

      // Clean the text for better speech
      const cleanText = text
        .replace(/\*\*(.*?)\*\*/g, '$1') // Remove bold markdown
        .replace(/\*(.*?)\*/g, '$1') // Remove italic markdown
        .replace(/`(.*?)`/g, '$1') // Remove code markdown
        .replace(/#{1,6}\s/g, '') // Remove headers
        .replace(/\n+/g, '. ') // Replace newlines with periods
        .replace(/\s+/g, ' ') // Normalize whitespace
        .trim();

      if (!cleanText) return;

      // Show TTS generation indicator
      setIsGeneratingTTS(true);

      // Try dedicated chatbot service first, fallback to regular TTS service
      let ttsService = dedicatedTTSService;
      let serviceHealthyCheck = await dedicatedTTSService.checkServiceHealth();

      if (!serviceHealthyCheck) {
        ttsService = regularTTSService;
        serviceHealthyCheck = await regularTTSService.checkServiceHealth();
      }

      if (!serviceHealthyCheck) {
        setIsGeneratingTTS(false);
        return;
      }

      // Play the TTS with visual feedback
      await ttsService.playTTS(cleanText, {
        volume: 0.8,
        onPlayStart: () => {
          setIsGeneratingTTS(false); // Hide generation indicator
          dispatch(setIsSpeaking(true)); // Show speaking animation
        },
        onPlayEnd: () => {
          dispatch(setIsSpeaking(false)); // Hide speaking animation
        },
        onError: () => {
          setIsGeneratingTTS(false); // Hide generation indicator on error
          dispatch(setIsSpeaking(false)); // Hide speaking animation on error
        }
      });

      // Mark this message as processed
      setLastProcessedMessageId(messageId);

    } catch (error) {
      // Silently handle TTS errors to avoid disrupting UX
      setIsGeneratingTTS(false);
      dispatch(setIsSpeaking(false));
    }
  }, [serviceHealthy, isTTSMuted, dispatch]);

  // Function to speak individual message
  const speakIndividualMessage = useCallback(async (text, messageId) => {
    if (!serviceHealthy || isTTSMuted || !text || !text.trim()) {
      return;
    }

    // Stop any currently playing message
    if (playingMessageId) {
      try {
        const dedicatedTTSService = (await import('../services/dedicatedChatbotTTSService')).default;
        dedicatedTTSService.stopTTS();
        setPlayingMessageId(null);
        dispatch(setIsSpeaking(false));
      } catch (error) {
        // Ignore errors when stopping
      }
    }

    try {
      // Import TTS services dynamically
      const dedicatedTTSService = (await import('../services/dedicatedChatbotTTSService')).default;
      const regularTTSService = (await import('../services/ttsService')).default;

      // Clean the text for better speech
      const cleanText = text
        .replace(/\*\*(.*?)\*\*/g, '$1') // Remove bold markdown
        .replace(/\*(.*?)\*/g, '$1') // Remove italic markdown
        .replace(/`(.*?)`/g, '$1') // Remove code markdown
        .replace(/#{1,6}\s/g, '') // Remove headers
        .replace(/\n+/g, '. ') // Replace newlines with periods
        .replace(/\s+/g, ' ') // Normalize whitespace
        .trim();

      if (!cleanText) return;

      // Set this message as playing
      setPlayingMessageId(messageId);

      // Try dedicated chatbot service first, fallback to regular TTS service
      let ttsService = dedicatedTTSService;
      let serviceHealthyCheck = await dedicatedTTSService.checkServiceHealth();

      if (!serviceHealthyCheck) {
        ttsService = regularTTSService;
        serviceHealthyCheck = await regularTTSService.checkServiceHealth();
      }

      if (!serviceHealthyCheck) {
        setPlayingMessageId(null);
        return;
      }

      // Play the TTS with visual feedback
      await ttsService.playTTS(cleanText, {
        volume: 0.8,
        onPlayStart: () => {
          dispatch(setIsSpeaking(true)); // Show speaking animation
        },
        onPlayEnd: () => {
          setPlayingMessageId(null); // Clear playing state
          dispatch(setIsSpeaking(false)); // Hide speaking animation
        },
        onError: () => {
          setPlayingMessageId(null); // Clear playing state on error
          dispatch(setIsSpeaking(false)); // Hide speaking animation on error
        }
      });

    } catch (error) {
      // Silently handle TTS errors to avoid disrupting UX
      setPlayingMessageId(null);
      dispatch(setIsSpeaking(false));
    }
  }, [serviceHealthy, isTTSMuted, dispatch, playingMessageId]);

  // Handle TTS mute/unmute
  const toggleTTSMute = useCallback(async () => {
    const newMutedState = !isTTSMuted;
    setIsTTSMuted(newMutedState);
    localStorage.setItem('chatbotTTSMuted', newMutedState.toString());

    // Stop current TTS if muting
    if (newMutedState) {
      dispatch(setIsSpeaking(false));
    } else {
      // When unmuting, ensure TTS service is properly initialized
      try {
        const dedicatedTTSService = (await import('../services/dedicatedChatbotTTSService')).default;
        dedicatedTTSService.autoPlayEnabled = true;

        // Re-check service health
        const healthy = await dedicatedTTSService.checkServiceHealth();
        setServiceHealthy(healthy);
      } catch (error) {
        setServiceHealthy(false);
      }
    }
  }, [isTTSMuted, dispatch]);

  // Direct API functions
  const sendChatMessage = async (userQuery, userId, llmModel = "grok") => {
    // Debug: Log the actual CHAT_API_BASE_URL being used
    console.log(`DEBUG - CHAT_API_BASE_URL from config:`, CHAT_API_BASE_URL);
    console.log(`DEBUG - Sending chat message to ${CHAT_API_BASE_URL}/chatpost`);
    console.log(`DEBUG - User ID: ${userId}, Model: ${llmModel}`);
    console.log(`DEBUG - Message: ${userQuery}`);

    // Check network connectivity
    if (!navigator.onLine) {
      const error = new Error("No internet connection. Please check your network.");
      console.error("DEBUG - Network offline:", error);
      throw error;
    }

    try {
      // Add timeout controller
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout

      // Determine language
      const currentLanguage = i18n.language && i18n.language.toLowerCase().startsWith("ar") ? "arabic" : "english";
      console.log("🌐 [Chatbot] Language detection:", {
        i18nLanguage: i18n.language,
        currentLanguage: currentLanguage,
        isArabic: currentLanguage === "arabic"
      });
      
      const response = await fetch(`${CHAT_API_BASE_URL}/chatpost?user_id=${userId}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "ngrok-skip-browser-warning": "true", // Add ngrok header for POST too
        },
        body: JSON.stringify({
          message: userQuery,
          llm: llmModel,
          language: currentLanguage,
          type: "chat_message",
        }),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        console.error(`HTTP error! status: ${response.status}`);
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log("DEBUG - Chat message sent successfully:", data);
      return data;
    } catch (error) {
      console.error("DEBUG - Error sending chat message:", error);
      
      // Provide better error messages
      if (error.name === "AbortError") {
        throw new Error("Request timeout: The server took too long to respond. Please try again.");
      } else if (error.message?.includes("Failed to fetch") || error.name === "TypeError") {
        throw new Error("Network error: Unable to connect to the chatbot server. Please ensure the backend server is running and the ngrok tunnel is active.");
      }
      
      throw error;
    }
  };

  const fetchChatbotResponse = async (userId, timeoutMs = 30000) => {
    console.log(`DEBUG - Fetching chatbot response from ${CHAT_API_BASE_URL}/chatbot`);
    console.log(`DEBUG - User ID: ${userId}`);
    console.log(`DEBUG - Timeout: ${timeoutMs}ms`);

    // Check network connectivity
    if (!navigator.onLine) {
      const error = new Error("No internet connection. Please check your network.");
      console.error("DEBUG - Network offline:", error);
      throw error;
    }

    try {
      // Add timeout controller
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

      // Add timestamp to prevent caching
      const timestamp = new Date().getTime();
      const response = await fetch(`${CHAT_API_BASE_URL}/chatbot?user_id=${userId}&timestamp=${timestamp}`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          "ngrok-skip-browser-warning": "true",
          "Cache-Control": "no-cache, no-store, must-revalidate",
          "Pragma": "no-cache",
          "Expires": "0"
        },
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        console.error(`HTTP error! status: ${response.status}`);
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log("DEBUG - Chatbot response received:", data);
      return data;
    } catch (error) {
      console.error("DEBUG - Error fetching chatbot response:", error);
      
      // Provide better error messages
      if (error.name === "AbortError") {
        throw new Error("Request timeout: The server took too long to respond. Please try again.");
      } else if (error.message?.includes("Failed to fetch") || error.name === "TypeError") {
        throw new Error("Network error: Unable to connect to the chatbot server. Please ensure the backend server is running and the ngrok tunnel is active.");
      }
      
      throw error;
    }
  };

  // Function to navigate to Summarizer page
  const handleNavigateToLearn = () => {
    navigate("/learn");
  };

  // Load the selected model from localStorage if available
  useEffect(() => {
    const savedModel = localStorage.getItem("selectedAIModel");
    if (savedModel) {
      setSelectedModel(savedModel);
    }
  }, []);

  // Auto-scroll to bottom when new messages arrive - DESKTOP ONLY
  useEffect(() => {
    // Only auto-scroll on desktop, not mobile
    if (!isMobile && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, currentStreamingMessage, isMobile]);

  // Focus input and initialize textarea height on mount
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
      // Initialize textarea height
      adjustTextareaHeight(inputRef.current);
    }
  }, []);

  // Ensure input is focused and ready when loading state changes
  useEffect(() => {
    if (!isLoading && inputRef.current) {
      // Small delay to ensure DOM updates are complete
      setTimeout(() => {
        if (inputRef.current) {
          inputRef.current.focus();
          inputRef.current.style.height = "46px";
          inputRef.current.scrollTop = 0;
        }
      }, 200);
    }
  }, [isLoading]);

  const handleSendMessage = async (e) => {
    if (e) e.preventDefault();
    if (!input.trim() || isLoading || !isInitialized) return;

    // Store the user's query before clearing input
    const userQuery = input.trim();

    // Add user message to chat history
    const userMessage = {
      role: "user",
      content: userQuery,
      model: selectedModel,
      timestamp: new Date().toISOString(),
    };
    await addMessage(userMessage);

    setInput("");
    setIsLoading(true);
    setCurrentStreamingMessage("");

    // Ensure input is ready for next interaction
    const ensureInputReady = () => {
      if (inputRef.current) {
        inputRef.current.focus();
        inputRef.current.style.height = "46px"; // Reset height
        inputRef.current.scrollTop = 0; // Reset scroll position
      }
    };

    try {
      // Enhanced debugging for user ID and query
      console.log("DEBUG - Sending message with user ID:", userId);
      console.log("DEBUG - User query:", userQuery);
      console.log("DEBUG - Query length:", userQuery.length);

      try {
        // Make sure userId is always defined
        const effectiveUserId = userId || user?.id || "guest-user";
        console.log("DEBUG - Using effective user ID:", effectiveUserId);

        // Process karma based on message content
        const karmaResult = processChatbotMessage(effectiveUserId, userQuery);
        if (karmaResult) {
          // Dispatch custom event for karma widget to listen
          window.dispatchEvent(new CustomEvent('karmaChanged', {
            detail: karmaResult
          }));
          
          // Show toast notification
          if (karmaResult.change > 0) {
            toast.success(`+${karmaResult.change} Karma: ${karmaResult.reason}`, {
              position: "top-right",
              duration: 3000,
            });
          } else {
            toast.error(`${karmaResult.change} Karma: ${karmaResult.reason}`, {
              position: "top-right",
              duration: 3000,
            });
          }
        }

        // STEP 1: First send the user's query to the chatpost endpoint
        console.log("DEBUG - Sending user query to chatpost");

        try {
          // Send the user's query to the chatpost endpoint with the selected model
          const chatpostResult = await sendChatMessage(userQuery, effectiveUserId, selectedModel);
          console.log("DEBUG - Initial chatpost result:", chatpostResult);
        } catch (error) {
          console.error("DEBUG - Error sending chat message:", error);
          
          // Show user-friendly error message
          const errorMessage = error.message || "Failed to send message to server";
          toast.error(errorMessage, {
            position: "bottom-right",
            duration: 5000,
          });
          
          // If it's a network error, don't continue - the backend isn't reachable
          if (error.message?.includes("Network error") || error.message?.includes("Failed to fetch")) {
            setIsLoading(false);
            const errorMsg = {
              role: "assistant",
              content: `⚠️ Connection Error: ${errorMessage}\n\nPlease ensure:\n1. The backend server is running\n2. The ngrok tunnel is active\n3. Your internet connection is working`,
              timestamp: new Date().toISOString(),
            };
            await addMessage(errorMsg);
            return;
          }
          
          // Continue anyway for other errors - the message might still be processed
        }

        // STEP 2: Now fetch the response from the chatbot endpoint
        console.log("DEBUG - Now fetching response from chatbot endpoint");

        // Wait a moment to allow the backend to process the query
        await new Promise((resolve) => setTimeout(resolve, 1000));

        // Initialize variables
        let response = null;
        let aiMessage = "";
        let maxRetries = 5;
        let retryCount = 0;
        let retryDelay = 2000; // Start with 2 seconds

        // Keep trying until we get a response or reach max retries
        // Use longer timeout for Arabic model (needs time to load model + generate)
        const timeoutMs = selectedModel === "arabic" ? 120000 : 30000; // 120s for Arabic, 30s for others
        console.log(`DEBUG - Using timeout: ${timeoutMs}ms for model: ${selectedModel}`);
        
        while (retryCount < maxRetries) {
          try {
            response = await fetchChatbotResponse(effectiveUserId, timeoutMs);
            console.log("DEBUG - Got response:", response);

            // If we got a valid response with no "No queries yet" error, break out of the loop
            if (response && (!response.error || response.error !== "No queries yet")) {
              break;
            }

            // If we got a "No queries yet" error, wait and retry
            console.log(`DEBUG - Got 'No queries yet' error, retrying (${retryCount + 1}/${maxRetries})...`);
            retryCount++;

            // Exponential backoff - increase delay with each retry
            await new Promise((resolve) => setTimeout(resolve, retryDelay));
            retryDelay = Math.min(retryDelay * 1.5, 10000); // Cap at 10 seconds
          } catch (error) {
            console.error("DEBUG - Error fetching response:", error);
            
            // If it's a network error, don't retry - the backend isn't reachable
            if (error.message?.includes("Network error") || error.message?.includes("Failed to fetch")) {
              console.error("DEBUG - Network error detected, stopping retries");
              throw error; // Re-throw to be caught by outer catch
            }
            
            retryCount++;
            await new Promise((resolve) => setTimeout(resolve, retryDelay));
            retryDelay = Math.min(retryDelay * 1.5, 10000);
          }
        }

        // If we've exhausted all retries and still have no valid response
        if (!response || (response.error && response.error === "No queries yet")) {
          aiMessage = "I'm processing your message. Please wait a moment and try again.";
          console.log("DEBUG - No valid response after all retries, using fallback");
        }

        // If we don't have an aiMessage yet, process the response
        if (!aiMessage) {
          // Expected structure from dedicated chatbot service:
          // {
          //   "_id": "...",
          //   "query": "user message",
          //   "response": {
          //     "message": "AI response",
          //     "timestamp": "...",
          //     "type": "chat_response",
          //     "user_id": "..."
          //   }
          // }

          if (response && response.response && response.response.message) {
            // This is the expected structure from the dedicated chatbot service
            aiMessage = response.response.message;
            console.log("DEBUG - Found message in response.response.message:", aiMessage);
          } else if (response && response.message) {
            // Fallback: direct message property
            aiMessage = response.message;
            console.log("DEBUG - Found message directly:", aiMessage);
          } else if (response && typeof response === "string") {
            // Fallback: response is a string
            aiMessage = response;
            console.log("DEBUG - Response is a string:", aiMessage);
          } else if (response && response.error && response.error !== "No queries yet") {
            // Handle other error cases (but not "No queries yet" which is already handled)
            aiMessage = `I encountered an issue: ${response.error}. Please try again.`;
            console.log("DEBUG - Found error message:", response.error);
          } else {
            // Last resort fallback
            aiMessage = "I received your message but had trouble generating a response. Please try again.";
            console.log("DEBUG - Using fallback message");
            console.log("DEBUG - Full response object:", JSON.stringify(response, null, 2));
          }
        }

        // Check if this is the first query to the server
        if (response && response.isFirstQuery) {
          // Show a toast notification to inform the user
          toast(
            "This is your first query to the server. Future responses will be more personalized.",
            {
              duration: 5000,
              icon: "🔄",
            }
          );

          // Automatically retry the chatpost endpoint to initialize the chat history
          try {
            console.log(
              "DEBUG - Initializing chat history with effectiveUserId:",
              effectiveUserId
            );

            // Make sure we have both the AI message and user query
            if (!aiMessage || !userQuery) {
              console.log(
                "DEBUG - Missing aiMessage or userQuery for chat history initialization"
              );
              console.log("DEBUG - aiMessage:", aiMessage);
              console.log("DEBUG - userQuery:", userQuery);

              // For initialization, we don't need to send again since we already sent the message
              console.log("DEBUG - Chat history initialization not needed with direct API");
            } else {
              // For initialization, we don't need to send again since we already sent the message
              console.log("DEBUG - Chat history initialization not needed with direct API");
            }

            console.log("DEBUG - Chat history initialized successfully");
          } catch (err) {
            // Log error but continue - this is non-critical
            console.log("DEBUG - Failed to initialize chat history:", err);
          }
        }

        // Add the bot's response to messages
        if (aiMessage && aiMessage.trim() !== "") {
          // Get the model used for this response
          const modelUsed = response?.response?.llm || selectedModel;

          // Add assistant message to chat history
          const assistantMessage = {
            role: "assistant",
            content: aiMessage,
            model: modelUsed,
            timestamp: new Date().toISOString(),
          };
          await addMessage(assistantMessage);

          // Trigger TTS for the AI response
          if (serviceHealthy && !isTTSMuted && aiMessage) {
            // Use timestamp as unique message ID for TTS tracking
            const messageId = assistantMessage.timestamp;
            setTimeout(() => {
              speakText(aiMessage, messageId);
            }, 300); // Small delay for better UX
          }

          // Log the chat message to Supabase
          try {
            await chatLogsService.logChatMessage({
              userId: effectiveUserId,
              message: userQuery,
              model: modelUsed,
              responseLength: aiMessage.length,
            });
            // Chat message logged successfully
          } catch (logError) {
            // Continue even if logging fails
          }

          // We've already sent the user query and received the response
          // No need to do anything else here

          // Ensure input is ready for next interaction after successful response
          setTimeout(() => {
            ensureInputReady();
          }, 100);
        } else {
          throw new Error("Empty response from chatbot. Please try again.");
        }
      } catch (error) {
        // Ensure error has a message property to prevent undefined errors
        const errorMessage = error?.message || error?.toString() || "Unknown error occurred";
        console.error("Chat error details:", error);

        // Check for specific error types
        let userErrorMessage = t(
          "I apologize, but I encountered an error. Please try again later."
        );

        let toastMessage =
          "Error connecting to chatbot server. Please try again.";

        // Handle network errors specifically
        if (
          errorMessage.includes("Network error") ||
          errorMessage.includes("Failed to fetch") ||
          errorMessage.includes("Unable to connect")
        ) {
          userErrorMessage = `⚠️ Connection Error: ${errorMessage}\n\nPlease ensure:\n1. The backend server is running\n2. The ngrok tunnel is active (if using ngrok)\n3. Your internet connection is working\n\nCheck the backend terminal for server status.`;
          toastMessage = "Network error: Unable to connect to chatbot server. Please check backend server status.";
        } else if (
          errorMessage.includes("503") ||
          errorMessage.includes("unavailable")
        ) {
          userErrorMessage = t(
            "I apologize, but the server is temporarily unavailable. Please try again in a few minutes or check with support if the issue persists."
          );
          toastMessage = `Server ${API_BASE_URL} is temporarily unavailable`;
        } else if (
          errorMessage.includes("timeout") ||
          errorMessage.includes("not responding")
        ) {
          userErrorMessage = t(
            "I apologize, but the request timed out. Please check your internet connection and try again."
          );
          toastMessage = "Request timed out. Check your connection.";
        } else if (
          errorMessage.includes("network") ||
          errorMessage.includes("Failed to fetch")
        ) {
          userErrorMessage = t(
            "I apologize, but there seems to be a network issue. Please check your internet connection and try again."
          );
          toastMessage = "Network error. Check your connection.";
        } else if (errorMessage.includes("Empty response")) {
          userErrorMessage = t(
            "I apologize, but I received an empty response from the server. This might be due to a configuration issue."
          );
          toastMessage = `Empty response from ${CHAT_API_BASE_URL}. Check server configuration.`;
        } else if (
          errorMessage.includes("No queries yet") ||
          errorMessage.includes("No queries found for this user")
        ) {
          userErrorMessage = t(
            "This appears to be your first query. The system is initializing your chat history."
          );
          toastMessage =
            "First-time setup. Please try sending your message again.";
        } else if (errorMessage.includes("Server error:")) {
          userErrorMessage = t(
            "I apologize, but the server returned an error. The developers have been notified."
          );
          toastMessage = errorMessage;
        }

        // Show toast notification with error
        toast.error(toastMessage, {
          duration: 5000,
          icon: "⚠️",
        });

        // Add error message to chat history
        await addMessage({
          role: "assistant",
          content: userErrorMessage,
          model: selectedModel,
          timestamp: new Date().toISOString(),
          isError: true,
        });

        // Ensure input is ready after error
        setTimeout(() => {
          ensureInputReady();
        }, 100);
      }
    } catch (error) {
      console.error("Unexpected error in handleSendMessage:", error);

      // Add unexpected error message to chat history
      await addMessage({
        role: "assistant",
        content: t(
          "I apologize, but I encountered an unexpected error. Please try again later."
        ),
        model: selectedModel,
        timestamp: new Date().toISOString(),
        isError: true,
      });

      // Ensure input is ready after unexpected error
      setTimeout(() => {
        ensureInputReady();
      }, 100);
    } finally {
      setIsLoading(false);
      setCurrentStreamingMessage("");

      // Final ensure input is ready - this is the most important one
      setTimeout(() => {
        ensureInputReady();
      }, 150);
    }
  };

  // Handle Enter key press and auto-resize textarea
  const handleKeyDown = (e) => {
    // Submit on Enter (without Shift)
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage(e);
    }

    // Auto-resize the textarea
    adjustTextareaHeight(e.target);
  };

  // Function to maintain fixed textarea height
  const adjustTextareaHeight = (element) => {
    if (!element) return;

    // Keep a fixed height of 46px
    element.style.height = "46px";
  };

  // Handle input changes
  const handleInputChange = (e) => {
    setInput(e.target.value);
    adjustTextareaHeight(e.target);

    // Ensure input stays focused and properly formatted
    if (e.target) {
      e.target.scrollTop = 0; // Keep scroll at top for single line appearance
    }
  };

  // Simple Mobile layout component
  const MobileChatLayout = () => (
    <GlassContainer>
      <div className="mobile-container">
        {/* Simple Mobile Header */}
        <div className="mobile-header">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowMobileMenu(!showMobileMenu)}
              className="mobile-menu-btn"
            >
              <Menu className="w-5 h-5 text-white" />
            </button>
            <h1 className="mobile-title">{t("Chatbot")}</h1>
          </div>
          
          <div className="flex items-center gap-2">
            <button
              onClick={toggleTTSMute}
              className="mobile-icon-btn"
              title={isTTSMuted ? t("Unmute voice") : t("Mute voice")}
            >
              {isTTSMuted ? (
                <VolumeX className="w-4 h-4 text-white/60" />
              ) : (
                <Volume2 className="w-4 h-4 text-white/80" />
              )}
            </button>
            
            <button
              onClick={createNewSession}
              className="mobile-icon-btn"
              title={t('Start New Chat')}
            >
              <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
            </button>
          </div>
        </div>

        {/* Simple Chat Content */}
        <div className="mobile-chat-content">
          {!isInitialized ? (
            <div className="mobile-loading">
              <div className="typing-indicator mb-4">
                <span></span>
                <span></span>
                <span></span>
              </div>
              <p className="text-white/60 text-sm">{t("Loading chat history...")}</p>
            </div>
          ) : (
            <>
              {/* Simple Messages Area */}
              <div className="mobile-messages">
                {/* Loading indicator */}
                {isLoading && !currentStreamingMessage && (
                  <div className="mobile-message assistant">
                    <div className="mobile-message-bubble">
                      <div className="typing-indicator">
                        <span></span>
                        <span></span>
                        <span></span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Streaming message */}
                {currentStreamingMessage && (
                  <div className="mobile-message assistant">
                    <div className="mobile-message-bubble">
                      <p className="mobile-message-text">{currentStreamingMessage}</p>
                      {serviceHealthy && (
                        <button
                          onClick={() => speakIndividualMessage(currentStreamingMessage, 'streaming')}
                          className="mobile-tts-btn"
                          disabled={isTTSMuted}
                        >
                          {playingMessageId === 'streaming' ? (
                            <div className="w-3 h-3 rounded-full bg-green-400 animate-pulse" />
                          ) : (
                            <Play className="w-3 h-3" />
                          )}
                        </button>
                      )}
                    </div>
                  </div>
                )}

                {/* Regular messages */}
                {messages.map((message, index) => {
                  const isUser = message.role === "user";
                  const isError = message.isError;
                  
                  return (
                    <div
                      key={message.id || `message-${index}-${message.role}`}
                      className={`mobile-message ${isUser ? 'user' : isError ? 'error' : 'assistant'}`}
                    >
                      <div className="mobile-message-bubble">
                        <p className="mobile-message-text">
                          <MessageContent content={message.content} />
                        </p>
                        
                        {!isUser && !isError && serviceHealthy && (
                          <button
                            onClick={() => speakIndividualMessage(message.content, message.id || message.timestamp)}
                            className="mobile-tts-btn"
                            disabled={isTTSMuted}
                          >
                            {playingMessageId === (message.id || message.timestamp) ? (
                              <div className="w-3 h-3 rounded-full bg-green-400 animate-pulse" />
                            ) : (
                              <Play className="w-3 h-3" />
                            )}
                          </button>
                        )}
                        
                        {!isUser && message.model && (
                          <div className="mobile-model-badge">
                            {message.model.charAt(0).toUpperCase() + message.model.slice(1)}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
                
                <div ref={messagesEndRef} className="h-1" />
              </div>
              
              {/* Simple Input Area */}
              <div className="mobile-input-area">
                {/* Model selector */}
                <div className="mobile-controls">
                  <select
                    value={selectedModel}
                    onChange={(e) => {
                      setSelectedModel(e.target.value);
                      localStorage.setItem("selectedAIModel", e.target.value);
                    }}
                    className="mobile-model-select"
                    disabled={isLoading || !isInitialized}
                  >
                    <option value="grok">Grok</option>
                    <option value="llama">Llama</option>
                    <option value="uniguru">UniGuru</option>
                    <option value="arabic">Arabic Model</option>
                  </select>
                  
                  {/* Status indicators */}
                  <div className="mobile-status">
                    {isGeneratingTTS && (
                      <div className="mobile-status-item">
                        <div className="w-2 h-2 rounded-full bg-white/60 animate-pulse" />
                        <span>{t("Generating...")}</span>
                      </div>
                    )}
                    
                    {!isGeneratingTTS && isSpeaking && (
                      <div className="mobile-status-item">
                        <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
                        <span>{t("Speaking...")}</span>
                      </div>
                    )}
                  </div>
                </div>
                
                {/* Input container */}
                <div className="mobile-input-container">
                  <button
                    onClick={handleNavigateToLearn}
                    className="mobile-attach-btn"
                    title={t("Go to Summarizer page")}
                  >
                    <Paperclip className="w-4 h-4" />
                  </button>
                  
                  <textarea
                    ref={inputRef}
                    value={input}
                    onChange={(e) => {
                      setInput(e.target.value);
                    }}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        handleSendMessage(e);
                      }
                    }}
                    placeholder={t("Ask me anything...")}
                    className="mobile-textarea"
                    disabled={isLoading || !isInitialized}
                    rows="1"
                  />
                  
                  <button
                    onClick={handleSendMessage}
                    className={`mobile-send-btn ${
                      input.trim() && !isLoading && isInitialized
                        ? 'active'
                        : 'disabled'
                    }`}
                    disabled={isLoading || !input.trim() || !isInitialized}
                  >
                    <Send className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
        
        {/* Simple Mobile Menu */}
        {showMobileMenu && (
          <div className="mobile-menu-overlay" onClick={() => setShowMobileMenu(false)}>
            <div className="mobile-menu-content" onClick={(e) => e.stopPropagation()}>
              <ChatHistoryControls
                chatStats={chatStats}
                onClearSession={clearCurrentSession}
                onClearAll={clearAllHistory}
                getAllSessions={getAllSessions}
                switchToSession={switchToSession}
                createNewSession={createNewSession}
                deleteSession={deleteSession}
                getCurrentSessionInfo={getCurrentSessionInfo}
              />
              
              {serviceHealthy && !isTTSMuted && messages.length > 0 && (
                <button
                  onClick={() => {
                    const assistantMessages = messages.filter(msg => msg.role === 'assistant' && !msg.isError);
                    if (assistantMessages.length > 0) {
                      const allText = assistantMessages.map(msg => msg.content).join('. ');
                      speakText(allText, 'all-messages');
                    }
                    setShowMobileMenu(false);
                  }}
                  className="mobile-speak-all-btn"
                  disabled={isGeneratingTTS || isSpeaking}
                >
                  🔊 Speak All AI Responses
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </GlassContainer>
  );

  return isMobile ? (
    <MobileChatLayout />
  ) : (
    <GlassContainer>
      {/* Header with Chat Controls */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <h2
            className="text-4xl md:text-5xl font-extrabold drop-shadow-lg transition-all duration-300 hover:bg-gradient-to-r hover:from-white hover:to-[#FF9933] hover:bg-clip-text hover:text-transparent"
            style={{ color: "#FFFFFF", fontFamily: "Nunito, sans-serif" }}
          >
            {t("Chatbot")}
          </h2>

          {/* TTS Controls */}
          <div className="flex items-center gap-2">
            {/* TTS Generation Indicator */}
            {isGeneratingTTS && (
              <div className="flex items-center gap-1 text-xs text-white/60">
                <div className="w-2 h-2 rounded-full bg-white/60 animate-pulse" />
                <span className="hidden sm:inline">{t("Generating...")}</span>
              </div>
            )}

            {/* TTS Speaking Indicator */}
            {!isGeneratingTTS && isSpeaking && (
              <div className="flex items-center gap-1 text-xs text-green-400">
                <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
                <span className="hidden sm:inline">{t("Speaking...")}</span>
              </div>
            )}

            {/* Speak All Button */}
            {serviceHealthy && !isTTSMuted && messages.length > 0 && (
              <button
                onClick={() => {
                  // Speak all assistant messages in sequence
                  const assistantMessages = messages.filter(msg => msg.role === 'assistant' && !msg.isError);
                  if (assistantMessages.length > 0) {
                    const allText = assistantMessages.map(msg => msg.content).join('. ');
                    speakText(allText, 'all-messages');
                  }
                }}
                className="px-3 py-1.5 rounded-lg bg-[#FF9933]/20 hover:bg-[#FF9933]/30 text-white transition-colors text-sm border border-[#FF9933]/30"
                title={t("Speak all AI responses")}
                disabled={isGeneratingTTS || isSpeaking}
              >
                <span className="hidden sm:inline">{t("Speak All")}</span>
                <span className="sm:hidden">🔊</span>
              </button>
            )}

            {/* TTS Mute/Unmute Button */}
            <button
              onClick={toggleTTSMute}
              className="p-2 rounded-lg hover:bg-white/10 transition-colors"
              title={isTTSMuted ? t("Unmute voice") : t("Mute voice")}
            >
              {isTTSMuted ? (
                <VolumeX className="w-5 h-5 text-white/60" />
              ) : (
                <Volume2 className="w-5 h-5 text-white/80" />
              )}
            </button>
          </div>
        </div>

        {/* Chat History Controls and New Chat Button */}
        <div className="flex items-center gap-2 flex-shrink-0">
          {/* New Chat Button */}
          <button
            onClick={createNewSession}
            className="flex items-center gap-2 px-3 py-2 rounded-lg bg-[#FF9933]/20 hover:bg-[#FF9933]/30 text-white transition-colors border border-[#FF9933]/30"
            title={t('Start New Chat')}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            <span className="hidden sm:inline">{t('New Chat')}</span>
          </button>

          {/* Chat History Controls */}
          <ChatHistoryControls
            chatStats={chatStats}
            onClearSession={clearCurrentSession}
            onClearAll={clearAllHistory}
            getAllSessions={getAllSessions}
            switchToSession={switchToSession}
            createNewSession={createNewSession}
            deleteSession={deleteSession}
            getCurrentSessionInfo={getCurrentSessionInfo}
          />
        </div>
      </div>

      {/* Chat Container */}
      <div
        className="flex-1 mb-4 flex flex-col"
        style={{
          height: "calc(100vh - 371px)",
          background: "rgba(255, 255, 255, 0.05)",
          backdropFilter: "blur(10px)",
          borderRadius: "16px",
          border: "1px solid rgba(255, 255, 255, 0.1)",
        }}
      >
        {/* Loading state for chat history initialization */}
        {!isInitialized && (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <div className="typing-indicator mb-4">
                <span></span>
                <span></span>
                <span></span>
              </div>
              <p className="text-white/60 text-sm">{t("Loading chat history...")}</p>
            </div>
          </div>
        )}
        {/* Messages container with proper scrolling - only show when initialized */}
        {isInitialized && (
          <div
            className="flex-1 overflow-y-auto overflow-x-hidden chat-scrollbar p-4 flex flex-col-reverse"
            style={{ maxWidth: "100%" }}
          >
          {/* Scroll anchor at the "bottom" (which is actually the top in flex-col-reverse) */}
          <div ref={messagesEndRef} className="h-0" />

          {/* Loading indicator */}
          {isLoading && !currentStreamingMessage && (
            <div className="mr-auto max-w-3xl mb-4 message-animation assistant-message">
              <div className="message-bubble assistant-bubble p-4 rounded-2xl">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
              <p className="mt-1 text-xs text-white/60">
                <span>
                  {t("Guru AI")}{" "}
                  <span
                    className="inline-block px-1.5 py-0.5 rounded text-[10px] font-medium ml-1"
                    style={{
                      background:
                        selectedModel === "grok"
                          ? "linear-gradient(135deg, rgba(255, 153, 51, 0.3), rgba(255, 153, 51, 0.1))"
                          : selectedModel === "llama"
                          ? "linear-gradient(135deg, rgba(0, 128, 255, 0.3), rgba(0, 128, 255, 0.1))"
                          : selectedModel === "chatgpt"
                          ? "linear-gradient(135deg, rgba(16, 163, 127, 0.3), rgba(16, 163, 127, 0.1))"
                          : "linear-gradient(135deg, rgba(128, 0, 255, 0.3), rgba(128, 0, 255, 0.1))",
                      border:
                        selectedModel === "grok"
                          ? "1px solid rgba(255, 153, 51, 0.3)"
                          : selectedModel === "llama"
                          ? "1px solid rgba(0, 128, 255, 0.3)"
                          : selectedModel === "chatgpt"
                          ? "1px solid rgba(16, 163, 127, 0.3)"
                          : "1px solid rgba(128, 0, 255, 0.3)",
                      boxShadow: "0 1px 3px rgba(0, 0, 0, 0.1)",
                    }}
                  >
                    {selectedModel.charAt(0).toUpperCase() +
                      selectedModel.slice(1)}
                  </span>{" "}
                  {t("is thinking...")}
                </span>
              </p>
            </div>
          )}

          {/* Streaming message */}
          {currentStreamingMessage && (
            <div className="mr-auto max-w-3xl mb-4 message-animation assistant-message">
              <div
                className="message-bubble assistant-bubble p-4 rounded-2xl overflow-hidden relative group"
                style={{
                  maxWidth: "100%",
                  wordWrap: "break-word",
                  overflowWrap: "break-word",
                }}
              >
                <p
                  className="text-white break-words"
                  style={{
                    fontFamily: "Inter, Poppins, sans-serif",
                    wordBreak: "break-word",
                    overflowWrap: "break-word",
                    whiteSpace: "pre-wrap",
                    maxWidth: "100%",
                  }}
                >
                  <MessageContent content={currentStreamingMessage} />
                </p>

                {/* Individual TTS Button for Streaming Message */}
                {serviceHealthy && currentStreamingMessage && (
                  <button
                    onClick={() => speakIndividualMessage(currentStreamingMessage, 'streaming')}
                    className={`absolute top-2 right-2 p-1.5 rounded-lg transition-all duration-200 opacity-0 group-hover:opacity-100 ${
                      playingMessageId === 'streaming'
                        ? 'bg-green-500/20 text-green-400'
                        : 'bg-white/10 hover:bg-[#FF9933]/20 text-white/70 hover:text-[#FF9933]'
                    }`}
                    title={playingMessageId === 'streaming' ? t("Playing...") : t("Play this message")}
                    disabled={isTTSMuted}
                  >
                    {playingMessageId === 'streaming' ? (
                      <div className="w-3 h-3 flex items-center justify-center">
                        <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
                      </div>
                    ) : (
                      <Play className="w-3 h-3" />
                    )}
                  </button>
                )}
              </div>
              <p className="mt-1 text-xs text-white/60 text-left">
                <span>
                  {t("Guru AI")}{" "}
                  <span
                    className="inline-block px-1.5 py-0.5 rounded text-[10px] font-medium ml-1"
                    style={{
                      background:
                        selectedModel === "grok"
                          ? "linear-gradient(135deg, rgba(255, 153, 51, 0.3), rgba(255, 153, 51, 0.1))"
                          : selectedModel === "llama"
                          ? "linear-gradient(135deg, rgba(0, 128, 255, 0.3), rgba(0, 128, 255, 0.1))"
                          : selectedModel === "chatgpt"
                          ? "linear-gradient(135deg, rgba(16, 163, 127, 0.3), rgba(16, 163, 127, 0.1))"
                          : "linear-gradient(135deg, rgba(128, 0, 255, 0.3), rgba(128, 0, 255, 0.1))",
                      border:
                        selectedModel === "grok"
                          ? "1px solid rgba(255, 153, 51, 0.3)"
                          : selectedModel === "llama"
                          ? "1px solid rgba(0, 128, 255, 0.3)"
                          : selectedModel === "chatgpt"
                          ? "1px solid rgba(16, 163, 127, 0.3)"
                          : "1px solid rgba(128, 0, 255, 0.3)",
                      boxShadow: "0 1px 3px rgba(0, 0, 0, 0.1)",
                    }}
                  >
                    {selectedModel.charAt(0).toUpperCase() +
                      selectedModel.slice(1)}
                  </span>
                </span>
              </p>
            </div>
          )}

          {/* Messages in reverse order (newest at the bottom) */}
          {[...messages].reverse().map((message, index) => {
            const isUser = message.role === "user";
            const isError = message.isError;
            const bubbleClass = isUser
              ? "message-bubble user-bubble"
              : isError
                ? "message-bubble error-bubble"
                : "message-bubble assistant-bubble";
            const animationClass = isUser ? "user-message" : "assistant-message";

            return (
              <div
                key={message.id || `message-${messages.length - 1 - index}-${message.role}`}
                className={`mb-4 message-animation ${animationClass} ${
                  isUser ? "ml-auto max-w-3xl" : "mr-auto max-w-3xl"
                }`}
                style={{ animationDelay: `${index * 0.05}s` }}
              >
                <div
                  className={`${bubbleClass} p-4 rounded-2xl overflow-hidden ${
                    isUser ? "text-right" : ""
                  } relative group`}
                  style={{
                    maxWidth: "100%",
                    wordWrap: "break-word",
                    overflowWrap: "break-word",
                  }}
                >
                <p
                  className="text-white break-words"
                  style={{
                    fontFamily: "Nunito, sans-serif",
                    wordBreak: "break-word",
                    overflowWrap: "break-word",
                    whiteSpace: "pre-wrap",
                    maxWidth: "100%",
                  }}
                >
                  <MessageContent content={message.content} />
                </p>

                {/* Individual TTS Button for Assistant Messages */}
                {!isUser && !isError && serviceHealthy && (
                  <button
                    onClick={() => speakIndividualMessage(message.content, message.id || message.timestamp)}
                    className={`absolute top-2 right-2 p-1.5 rounded-lg transition-all duration-200 opacity-0 group-hover:opacity-100 ${
                      playingMessageId === (message.id || message.timestamp)
                        ? 'bg-green-500/20 text-green-400'
                        : 'bg-white/10 hover:bg-[#FF9933]/20 text-white/70 hover:text-[#FF9933]'
                    }`}
                    title={playingMessageId === (message.id || message.timestamp) ? t("Playing...") : t("Play this message")}
                    disabled={isTTSMuted}
                  >
                    {playingMessageId === (message.id || message.timestamp) ? (
                      <div className="w-3 h-3 flex items-center justify-center">
                        <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
                      </div>
                    ) : (
                      <Play className="w-3 h-3" />
                    )}
                  </button>
                )}
              </div>
              <p
                className={`mt-1 text-xs text-white/60 ${
                  message.role === "user" ? "text-right" : "text-left"
                }`}
              >
                {message.role === "user" ? (
                  t("You")
                ) : (
                  <span>
                    {t("Guru AI")}{" "}
                    {message.model && (
                      <span
                        className="inline-block px-1.5 py-0.5 rounded text-[10px] font-medium ml-1"
                        style={{
                          background:
                            message.model === "grok"
                              ? "linear-gradient(135deg, rgba(255, 153, 51, 0.3), rgba(255, 153, 51, 0.1))"
                              : message.model === "llama"
                              ? "linear-gradient(135deg, rgba(0, 128, 255, 0.3), rgba(0, 128, 255, 0.1))"
                              : message.model === "chatgpt"
                              ? "linear-gradient(135deg, rgba(16, 163, 127, 0.3), rgba(16, 163, 127, 0.1))"
                              : "linear-gradient(135deg, rgba(128, 0, 255, 0.3), rgba(128, 0, 255, 0.1))",
                          border:
                            message.model === "grok"
                              ? "1px solid rgba(255, 153, 51, 0.3)"
                              : message.model === "llama"
                              ? "1px solid rgba(0, 128, 255, 0.3)"
                              : message.model === "chatgpt"
                              ? "1px solid rgba(16, 163, 127, 0.3)"
                              : "1px solid rgba(128, 0, 255, 0.3)",
                          boxShadow: "0 1px 3px rgba(0, 0, 0, 0.1)",
                        }}
                      >
                        {message.model.charAt(0).toUpperCase() +
                          message.model.slice(1)}
                      </span>
                    )}
                  </span>
                )}
              </p>
            </div>
          );
          })}
          </div>
        )}
      </div>

      {/* Input Area - Horizontal Layout with Fixed Height */}
      <div className="relative">
        <div
          className="chat-input-container flex items-center p-2 rounded-2xl"
          style={{
            background: "rgba(255, 255, 255, 0.1)",
            backdropFilter: "blur(10px)",
            border: "1px solid rgba(255, 255, 255, 0.18)",
          }}
        >
          {/* Pin/Paperclip icon */}
          <button
            type="button"
            onClick={handleNavigateToLearn}
            className="p-2 text-white/70 hover:text-white transition-colors duration-200 hover:bg-white/10 rounded-full flex-shrink-0"
            title={t("Go to Summarizer page")}
          >
            <FiFile className="w-5 h-5 paperclip-icon" />
          </button>

          {/* AI Model Selector */}
          <div className="flex-shrink-0 mx-2 relative group">
            <div className="absolute -top-6 left-0 bg-black/80 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none z-10">
              {t("Select AI Model")}
            </div>
            <select
              value={selectedModel}
              onChange={(e) => {
                setSelectedModel(e.target.value);
                // Save the selected model to localStorage for use in other components
                localStorage.setItem("selectedAIModel", e.target.value);
              }}
              className="model-selector appearance-none bg-gradient-to-r from-[#FF9933]/30 to-[#FF9933]/10 text-white border-2 border-[#FF9933]/30 rounded-lg px-3 py-2 text-sm font-medium outline-none cursor-pointer transition-all duration-300"
              style={{
                backdropFilter: "blur(10px)",
                boxShadow: "0 2px 10px rgba(255, 153, 51, 0.2)",
                textShadow: "0 1px 2px rgba(0, 0, 0, 0.3)",
                minWidth: "110px",
              }}
              disabled={isLoading || !isInitialized}
            >
              <option value="grok" className="bg-[#1E1E28] text-white">
                Grok
              </option>
              <option value="llama" className="bg-[#1E1E28] text-white">
                Llama
              </option>
              <option value="uniguru" className="bg-[#1E1E28] text-white">
                UniGuru
              </option>
              <option value="arabic" className="bg-[#1E1E28] text-white">
                Arabic Model
              </option>
            </select>
            {/* Custom dropdown arrow */}
            <div className="absolute right-2 top-1/2 transform -translate-y-1/2 pointer-events-none">
              <svg
                width="12"
                height="6"
                viewBox="0 0 12 6"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  d="M1 1L6 5L11 1"
                  stroke="white"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </div>
          </div>

          {/* Textarea with fixed height */}
          <div
            className="flex-grow mx-2 min-w-0"
            onClick={() => {
              if (inputRef.current && !isLoading) {
                inputRef.current.focus();
              }
            }}
          >
            <textarea
              ref={inputRef}
              value={input}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              onFocus={() => {
                // Ensure proper formatting when focused
                if (inputRef.current) {
                  inputRef.current.style.height = "46px";
                  inputRef.current.scrollTop = 0;
                }
              }}
              placeholder={t("Ask about ancient Indian wisdom...")}
              className="w-full bg-transparent text-white px-2 py-3 outline-none resize-none"
              style={{
                height: "46px", // Fixed height
                lineHeight: "1.5",
                overflowY: "auto",
                overflowX: "hidden",
                wordBreak: "break-word",
                whiteSpace: "pre-wrap",
              }}
              disabled={isLoading || !isInitialized}
              rows="1"
            />
          </div>

          {/* Send button */}
          <button
            onClick={handleSendMessage}
            type="button"
            className="px-6 py-3 rounded-xl transition-all hover:scale-105 disabled:opacity-50 disabled:hover:scale-100 flex-shrink-0"
            disabled={isLoading || !input.trim() || !isInitialized}
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
      </div>

      <div className="mt-3 text-white/60 text-xs text-center">
        <p className="mt-1 text-white/40 text-xs">
          {t("Tip: Use Shift+Enter for a new line")}
        </p>
      </div>
    </GlassContainer>
  );
}
