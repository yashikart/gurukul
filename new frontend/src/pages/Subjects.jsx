import React, { useState, useEffect } from "react";
import GlassContainer from "../components/GlassContainer";
import GlassInput from "../components/GlassInput";
import GlassButton from "../components/GlassButton";
import { LessonLiveRenderer, LessonStreamRenderer } from "../components/LessonLiveRenderer";
import { useJupiterTTS } from "../hooks/useTTS";
import { useTranslation } from "react-i18next";

import {
  useGenerateEnhancedLessonMutation,
  useGetUserProgressQuery,
  useGetUserAnalyticsQuery,
  useTriggerInterventionMutation,
  useGetIntegrationStatusQuery,
  formatEnhancedLessonData,
  formatUserProgressData
} from "../api/orchestrationApiSlice";
import { useLazyGenerateLessonQuery } from "../api/subjectsApiSlice";
import { Book, BookOpen } from "lucide-react";
import { useSelector } from "react-redux";
import { selectUserId } from "../store/authSlice";
import { toast } from "react-hot-toast";
import { processSubjectsUsage, dispatchKarmaChange } from "../utils/karmaManager";
import { API_BASE_URL, AGENT_API_BASE_URL } from "../config";
import YouTubeRecommendations from "../components/YouTubeRecommendations";

export default function Subjects() {
  const { t } = useTranslation();
  // Get user ID first (needed for hooks)
  const userId = useSelector(selectUserId) || "guest-user";



  // Backend API hook for generate_lesson endpoint
  const [triggerGenerateLesson, { isLoading: isGeneratingLesson, error: generateLessonError }] = useLazyGenerateLessonQuery();

  // Orchestration API hooks
  const [
    generateEnhancedLesson,
    { data: enhancedLessonData, isLoading: isLoadingEnhanced, isError: isErrorEnhanced },
  ] = useGenerateEnhancedLessonMutation();

  const [
    triggerIntervention,
    { isLoading: isTriggeringIntervention },
  ] = useTriggerInterventionMutation();

  // Get integration status to check if orchestration is available
  const { data: integrationStatus, isLoading: isLoadingIntegration } = useGetIntegrationStatusQuery();

  // Get user progress if orchestration is available
  const { data: userProgress, isLoading: isLoadingProgress } = useGetUserProgressQuery(userId, {
    skip: !integrationStatus?.integration_status?.overall_valid || !userId || userId === "guest-user"
  });

  // Get user analytics if orchestration is available
  const { data: userAnalytics, isLoading: isLoadingAnalytics } = useGetUserAnalyticsQuery(userId, {
    skip: !integrationStatus?.integration_status?.overall_valid || !userId || userId === "guest-user"
  });


  // Component state
  const [selectedSubject, setSelectedSubject] = useState("");
  const [topic, setTopic] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showResults, setShowResults] = useState(false);

  const [lessonData, setLessonData] = useState(null);
  const [includeWikipedia, setIncludeWikipedia] = useState(true);
  const [useKnowledgeStore, setUseKnowledgeStore] = useState(true);

  // Orchestration-specific state
  const [useOrchestration, setUseOrchestration] = useState(true);
  const [lastQuizScore, setLastQuizScore] = useState(null);
  const [showInterventionPanel, setShowInterventionPanel] = useState(false);

  // Edge case handling states
  const [retryCount, setRetryCount] = useState(0);
  const [extendedWaitMode, setExtendedWaitMode] = useState(false);
  const [fallbackContentAvailable, setFallbackContentAvailable] = useState(false);
  const [isOfflineMode, setIsOfflineMode] = useState(false);
  const [lastError, setLastError] = useState(null);
  const maxRetries = 3;
  const extendedWaitThreshold = 300; // 5 minutes

  // TTS integration for Jupiter model responses
  const { handleJupiterResponse, serviceHealthy, isPlaying, stopTTS } = useJupiterTTS({
    onPlayStart: (text) => {
      console.log("🔊 Jupiter TTS: Started playing lesson content");
    },
    onPlayEnd: (text) => {
      console.log("🔊 Jupiter TTS: Finished playing lesson content");
    },
    onError: (error) => {
      console.warn("🔊 Jupiter TTS: Auto-play failed:", error.message);
    }
  });

  // Use the imported cleanContentForVideo utility for cleaning content

  // Video transformation functions removed
  // Video transformation functions removed - not implemented yet
  const transformLessonToVideoFormat = () => { return null; };
  const createNarrativeStory = () => { return ""; };
  const createBasicNarrative = () => { return ""; };
  const getStyleModifiers = () => { return {}; };

  // Safely render activity content that may be an object or string
  const renderActivityContent = (activity) => {
    if (!activity) return null;
    if (typeof activity === 'string') {
      return <p className="text-white/95 leading-relaxed text-lg font-medium">{activity}</p>;
    }
    if (Array.isArray(activity)) {
      return (
        <ul className="list-disc list-inside text-white/95 leading-relaxed text-lg font-medium">
          {activity.map((item, idx) => (
            <li key={idx}>{typeof item === 'string' ? item : JSON.stringify(item)}</li>
          ))}
        </ul>
      );
    }
    if (typeof activity === 'object') {
      const {
        title,
        description,
        instructions,
        materials_needed,
        materials,
        steps
      } = activity;

      return (
        <div className="space-y-3">
          {title && <p className="text-white font-semibold text-lg">{title}</p>}
          {description && <p className="text-white/95 leading-relaxed text-lg">{description}</p>}

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
    return <p className="text-white/95 leading-relaxed text-lg font-medium">{String(activity)}</p>;
  };

  // Safely render question content that may be an object or string
  const renderQuestionContent = (question) => {
    if (!question) return null;
    if (typeof question === 'string') {
      return <p className="text-white/95 leading-relaxed text-lg font-medium italic">"{question}"</p>;
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
            <p className="text-white/95 leading-relaxed text-lg font-medium italic">"{text}"</p>
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
    return <p className="text-white/95 leading-relaxed text-lg font-medium">{String(question)}</p>;
  };

  // Handler for triggering interventions
  const handleTriggerIntervention = async () => {
    if (!userId || userId === "guest-user") {
      toast.error(t("Please log in to access personalized interventions."));
      return;
    }

    try {
      const result = await triggerIntervention({
        user_id: userId,
        quiz_score: lastQuizScore
      }).unwrap();

      if (result.interventions && result.interventions.length > 0) {
        toast.success(
          `✅ ${result.interventions.length} intervention(s) triggered successfully!`,
          {
            duration: 4000,
            style: {
              background: 'linear-gradient(135deg, rgba(15, 15, 25, 0.95), rgba(25, 25, 35, 0.95))',
              color: '#fff',
              border: '1px solid rgba(34, 197, 94, 0.3)',
              borderRadius: '12px',
            },
          }
        );
        setShowInterventionPanel(true);
      } else {
        toast.info("No interventions needed at this time. Keep up the good work!");
      }
    } catch (error) {
      console.error("Failed to trigger intervention:", error);
      toast.error("Failed to trigger intervention. Please try again.");
    }
  };

  // Cleanup blob URLs to prevent memory leaks
  useEffect(() => {
    return () => {
      // Video cleanup removed
    };
  }, []);

  // Computed values for loading and error states
  const isLoadingData = isSubmitting || isGeneratingLesson;
  const isErrorData = generateLessonError || (lessonData?.status === "error");
  const subjectData = lessonData;

  // Reset results when subject or topic changes
  useEffect(() => {
    setShowResults(false);
    setLessonData(null);
  }, [selectedSubject, topic]);

  // Ensure isSubmitting is properly reset when API request completes
  useEffect(() => {
    if (!isLoadingData && isSubmitting) {
      // Small delay to ensure smooth transition
      const timer = setTimeout(() => {
        setIsSubmitting(false);
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [isLoadingData, isSubmitting]);

  // Helper function to check if both fields are valid (non-empty after trimming)
  const isFormValid = () => {
    return selectedSubject.trim().length > 0 && topic.trim().length > 0;
  };

  // Helper function to determine if button should be disabled
  const isButtonDisabled = () => {
    return isSubmitting || isLoadingData;
  };

  // Helper function to determine button visual state
  const getButtonVisualState = () => {
    if (isButtonDisabled()) {
      return "disabled"; // Fully disabled during submission/loading
    }
    if (!isFormValid()) {
      return "invalid"; // Visually dimmed but clickable when form is invalid
    }
    return "valid"; // Normal state when form is valid and not submitting
  };

  // Helper function to reset form and return to search
  const handleNewSearch = () => {
    setShowResults(false);
    setSelectedSubject("");
    setTopic("");
    setLessonData(null);
    setIncludeWikipedia(true);
    setUseKnowledgeStore(true);
    setRetryCount(0);
    setExtendedWaitMode(false);
    setFallbackContentAvailable(false);
    setIsOfflineMode(false);
    setLastError(null);
    // Video cleanup removed
  };

  // Retry logic with exponential backoff for lesson generation
  const retryLessonGeneration = async (apiCall, maxRetries = 3, baseDelay = 2000) => {
    for (let attempt = 0; attempt < maxRetries; attempt++) {
      try {
        return await apiCall();
      } catch (error) {
        setLastError(error.message);

        if (attempt === maxRetries - 1) {
          throw error; // Last attempt failed
        }

        const delay = baseDelay * Math.pow(2, attempt); // Exponential backoff
        console.log(`🔄 Lesson generation retry attempt ${attempt + 1}/${maxRetries} in ${delay}ms`);

        toast.loading(
          `🔄 Retrying lesson generation... (Attempt ${attempt + 2}/${maxRetries})\n⏱️ Please wait ${delay/1000} seconds`,
          {
            id: "lesson-retry-notification",
            duration: delay,
            style: {
              background: 'linear-gradient(135deg, rgba(15, 15, 25, 0.95), rgba(25, 25, 35, 0.95))',
              color: '#fff',
              border: '1px solid rgba(255, 153, 51, 0.3)',
              borderRadius: '12px',
              fontSize: '14px',
              maxWidth: '450px',
              boxShadow: '0 0 20px rgba(255, 153, 51, 0.1)',
            },
          }
        );

        // After the retry delay, update the main toast to continue showing progress
        setTimeout(() => {
          toast.loading(
            "📚 Continuing lesson generation... Please remain patient.\n🗄️ Knowledge Store processing may take 5-10 minutes.",
            {
              id: "lesson-generation",
              duration: Infinity,
              style: {
                background: 'linear-gradient(135deg, rgba(15, 15, 25, 0.95), rgba(25, 25, 35, 0.95))',
                color: '#fff',
                border: '1px solid rgba(255, 153, 51, 0.3)',
                borderRadius: '12px',
                fontSize: '14px',
                maxWidth: '450px',
                fontWeight: '500',
                boxShadow: '0 0 20px rgba(255, 153, 51, 0.1)',
              },
            }
          );
        }, delay);

        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  };

  // Check for cached lesson content
  const getCachedLessonContent = (subject, topic) => {
    try {
      const cacheKey = `lesson_${subject.toLowerCase()}_${topic.toLowerCase()}`;
      const cached = localStorage.getItem(cacheKey);
      if (cached) {
        const parsedCache = JSON.parse(cached);
        const cacheAge = Date.now() - parsedCache.timestamp;
        const maxAge = 24 * 60 * 60 * 1000; // 24 hours

        if (cacheAge < maxAge) {
          return parsedCache.data;
        }
      }
    } catch (error) {
      console.error("Error reading cached lesson content:", error);
    }
    return null;
  };

  // Save lesson content to cache
  const cacheLessonContent = (subject, topic, data) => {
    try {
      const cacheKey = `lesson_${subject.toLowerCase()}_${topic.toLowerCase()}`;
      const cacheData = {
        data: data,
        timestamp: Date.now()
      };
      localStorage.setItem(cacheKey, JSON.stringify(cacheData));
    } catch (error) {
      console.error("Error caching lesson content:", error);
    }
  };



  // Import the comprehensive content formatter from utils
  // This function is now handled by the imported formatLessonContent utility

  // Video generation removed - not implemented yet
  const sendToVisionAPI = async (subject, topic, lessonData) => {
    // Video generation functionality removed
    return;
    try {
      console.log("🎬 Sending lesson content to AnimateDiff video generation API...");

      if (!lessonData?.explanation) {
        console.log("⚠️ No explanation available to send to video generation API");
        return;
      }

      // Video generation removed
      return;

      console.log("🎬 Transformed content for video generation:", styledContent);

      // Create the final payload for the API
      const payload = styledContent;

      console.log("🎬 AnimateDiff API Payload:", payload);
      if (import.meta.env.VITE_DEBUG_PROXY === 'true') {
        console.log("🎬 Target endpoint:", import.meta.env.VITE_VISION_API_URL || 'http://localhost:8501/generate-video');
        console.log("🎬 Ngrok endpoint:", import.meta.env.VITE_VISION_NGROK_URL || '');
      }

      let response;
      let usingProxy = false;

      // Standard headers with API key for all requests
      const headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'x-api-key': 'shashank_ka_vision786'
      };

      try {
        // First attempt: Use flexible backend proxy (most reliable - avoids CORS)
        console.log("🎬 Attempting flexible backend proxy request via localhost:8001/proxy/vision-flexible...");
        const flexibleProxyResponse = await fetch(`${CHAT_API_BASE_URL}/proxy/vision-flexible`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
          },
          mode: 'cors',
          credentials: 'same-origin',
          body: JSON.stringify(payload)
        });

        // Check if flexible proxy request was successful
        if (flexibleProxyResponse.ok) {
          response = flexibleProxyResponse;
          usingProxy = true;
          console.log("🎬 Flexible backend proxy request successful");
        } else {
          console.log(`🎬 Flexible backend proxy failed with status ${flexibleProxyResponse.status}: ${flexibleProxyResponse.statusText}`);
          throw new Error(`Flexible backend proxy returned ${flexibleProxyResponse.status}`);
        }
      } catch (flexibleProxyError) {
        console.log("🎬 Flexible backend proxy failed, trying standard backend proxy...");
        console.log("🎬 Flexible proxy error:", flexibleProxyError.message);

        try {
          // Second attempt: Use standard backend proxy
          console.log("🎬 Attempting standard backend proxy request via localhost:8001/proxy/vision...");
          const backendProxyResponse = await fetch(`${CHAT_API_BASE_URL}/proxy/vision`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
          },
          mode: 'cors',
          credentials: 'same-origin',
          body: JSON.stringify({
            ...payload,
            target_endpoint: (import.meta.env.VITE_VISION_API_URL || "http://localhost:8501/generate-video")
          })
        });

        // Check if backend proxy request was successful
        if (backendProxyResponse.ok) {
          response = backendProxyResponse;
          usingProxy = true;
          console.log("🎬 Backend proxy request successful");
        } else {
          console.log(`🎬 Backend proxy failed with status ${backendProxyResponse.status}: ${backendProxyResponse.statusText}`);
          throw new Error(`Backend proxy returned ${backendProxyResponse.status}`);
        }
        } catch (backendProxyError) {
          console.log("🎬 Backend proxy failed, trying test proxy...");
          console.log("🎬 Backend proxy error:", backendProxyError.message);

          try {
            // Third attempt: Use backend test proxy
          console.log("🎬 Attempting backend test proxy via localhost:8001/test-generate-video...");
          const testProxyResponse = await fetch(`${CHAT_API_BASE_URL}/test-generate-video`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Accept': 'application/json',
            },
            mode: 'cors',
            credentials: 'same-origin',
            body: JSON.stringify(payload)
          });

          // Check if test proxy request was successful
          if (testProxyResponse.ok) {
            response = testProxyResponse;
            usingProxy = true;
            console.log("🎬 Backend test proxy request successful");
          } else {
            console.log(`🎬 Backend test proxy failed with status ${testProxyResponse.status}: ${testProxyResponse.statusText}`);
            throw new Error(`Backend test proxy returned ${testProxyResponse.status}`);
          }
        } catch (testProxyError) {
          console.log("🎬 Backend test proxy failed, trying ngrok endpoint...");
          console.log("🎬 Test proxy error:", testProxyError.message);

          try {
            // Third attempt: Use ngrok public endpoint with API key
            console.log("🎬 Attempting ngrok endpoint with API key...");
            const ngrokUrl = import.meta.env.VITE_VISION_NGROK_URL;
            const ngrokResponse = await fetch(`${ngrokUrl}/generate-video`, {
              method: 'POST',
              headers: {
                ...headers,
                'ngrok-skip-browser-warning': 'true' // Skip ngrok browser warning
              },
              mode: 'cors',
              credentials: 'omit',
              body: JSON.stringify(payload)
            });

            // Check if ngrok request was successful
            if (ngrokResponse.ok) {
              response = ngrokResponse;
              usingProxy = false;
              console.log("🎬 Ngrok endpoint request successful");
            } else {
              console.log(`🎬 Ngrok endpoint failed with status ${ngrokResponse.status}: ${ngrokResponse.statusText}`);
              throw new Error(`Ngrok endpoint returned ${ngrokResponse.status}`);
            }
          } catch (ngrokError) {
            console.log("🎬 Ngrok failed, trying Vite proxy as final fallback...");
            console.log("🎬 Ngrok error:", ngrokError.message);

            try {
              // Fourth attempt: Use Vite proxy (development only)
              console.log("🎬 Attempting Vite proxy via /api/vision...");
              const viteProxyResponse = await fetch("/api/vision", {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                  'Accept': 'application/json',
                },
                mode: 'cors',
                credentials: 'same-origin',
                body: JSON.stringify(payload)
              });

              // Check if Vite proxy request was successful
              if (viteProxyResponse.ok) {
                response = viteProxyResponse;
                usingProxy = true;
                console.log("🎬 Vite proxy request successful");
              } else {
                console.log(`🎬 Vite proxy failed with status ${viteProxyResponse.status}: ${viteProxyResponse.statusText}`);
                throw new Error(`Vite proxy returned ${viteProxyResponse.status}`);
              }
            } catch (viteProxyError) {
              console.log("🎬 All connection methods failed");
              console.log("🎬 Vite proxy error:", viteProxyError.message);
              throw new Error("All connection methods failed - backend proxy, test proxy, ngrok, and Vite proxy all failed");
            }
          }
        }
      }
    }

      if (!response.ok) {
        // Try to get error details from response
        let errorMessage = `AnimateDiff API request failed: ${response.status} ${response.statusText}`;
        const methodUsedForError = usingProxy ? "proxy" : "direct request";

        try {
          const errorData = await response.json();
          if (errorData.error || errorData.message) {
            errorMessage = errorData.error || errorData.message;
          }
        } catch (e) {
          // If we can't parse error response, use the default message
        }

        console.log(`🎬 Final ${methodUsedForError} failed with status ${response.status}`);
        throw new Error(`${errorMessage} (via ${methodUsedForError})`);
      }

      // Handle response from AnimateDiff API
      const contentType = response.headers.get('content-type');
      let result;

      if (contentType && contentType.includes('video/')) {
        // Response is a video file (direct method)
        const videoBlob = await response.blob();
        console.log("🎥 Video blob created:", {
          size: videoBlob.size,
          type: videoBlob.type,
          isValid: videoBlob.size > 0
        });

        const videoUrl = URL.createObjectURL(videoBlob);
        console.log("🎥 Blob URL created:", videoUrl);

        result = {
          success: true,
          video_url: videoUrl,
          content_type: contentType,
          size: videoBlob.size,
          method: "direct"
        };
        console.log("🎬 Video generated successfully (direct):", result);
      } else {
        // Response is JSON (new transfer method)
        result = await response.json();
        console.log("🎬 AnimateDiff API Response:", result);

        // If video was transferred to main system, get it from there
        if (result.success && result.video_id && result.access_url) {
          console.log("🎬 Video transferred to main system, fetching from:", result.access_url);

          try {
            const videoResponse = await fetch(`${API_BASE_URL}${result.access_url}`, {
              method: 'GET',
              headers: {
                'Accept': 'video/mp4',
              },
              mode: 'cors',
              credentials: 'same-origin'
            });

            if (videoResponse.ok) {
              const videoBlob = await videoResponse.blob();
              const videoUrl = URL.createObjectURL(videoBlob);
              result = {
                ...result,
                video_url: videoUrl,
                content_type: videoResponse.headers.get('content-type') || 'video/mp4',
                size: videoBlob.size,
                method: "transferred"
              };
              console.log("🎬 Video fetched from main system successfully:", result);
            } else {
              console.log("⚠️ Failed to fetch video from main system, using fallback");
            }
          } catch (fetchError) {
            console.log("⚠️ Error fetching video from main system:", fetchError);
          }
        }
      }

      // Show success toast with method used and video info
      const methodUsed = usingProxy ? "via backend proxy" : "directly via public endpoint";
      const transferMethod = result.method === "transferred" ? " → transferred to main system" : "";
      const videoInfo = result.video_url ? `\n🎥 Video generated (${(result.size / 1024 / 1024).toFixed(2)} MB)` : '';

      toast.success(
        `🎬 AnimateDiff video generation completed ${methodUsed}${transferMethod}!${videoInfo}`,
        {
          duration: 6000,
          style: {
            background: 'linear-gradient(135deg, rgba(15, 15, 25, 0.95), rgba(25, 25, 35, 0.95))',
            color: '#fff',
            border: '1px solid rgba(255, 153, 51, 0.3)',
            borderRadius: '12px',
            fontSize: '14px',
            maxWidth: '500px',
            boxShadow: '0 0 20px rgba(255, 153, 51, 0.1)',
          },
        }
      );

      // If video was generated, store it for display
      if (result.video_url) {
        console.log("🎥 Generated video URL:", result.video_url);
        console.log("🎥 Video can be displayed using this URL in a <video> element");

        // Store the video data and show in sidebar
        showVideo({
          url: result.video_url,
          contentType: result.content_type,
          size: result.size,
          subject: subject,
          topic: topic,
          timestamp: new Date().toISOString()
        });
      }

      return result;
    } catch (error) {
      console.error("🎬 Error sending to video generation API:", error);

      // Determine error type for better user feedback
      let errorMessage = error.message;
      if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
        errorMessage = "Network connection failed. Please check that your backend (localhost:8001) is running and can reach the AnimateDiff service.";
      } else if (error.message.includes('CORS')) {
        errorMessage = "Cross-origin request blocked. Using backend proxy to resolve the issue.";
      } else if (error.message.includes('404')) {
        errorMessage = "Video generation API endpoint not found. Please verify the AnimateDiff service endpoint is correct.";
      } else if (error.message.includes('401') || error.message.includes('403')) {
        errorMessage = "Authentication failed. Please verify the API key is correct.";
      } else if (error.message.includes('500') || error.message.includes('503')) {
        errorMessage = "AnimateDiff service is temporarily unavailable or unreachable. Please try again later.";
      } else if (error.message.includes('504')) {
        errorMessage = "Video generation request timed out. The process may take longer than expected.";
      }

      // Show error toast (non-blocking)
      toast.error(
        `🎬 Failed to connect to AnimateDiff API: ${errorMessage}\n📍 Backend Proxy: localhost:8001 → 192.168.0.121:8501\n🌐 Ngrok Fallback: 8c9ce043b836.ngrok-free.app`,
        {
          duration: 8000,
          style: {
            background: 'linear-gradient(135deg, rgba(15, 15, 25, 0.95), rgba(25, 25, 35, 0.95))',
            color: '#fff',
            border: '1px solid rgba(255, 153, 51, 0.3)',
            borderRadius: '12px',
            fontSize: '14px',
            maxWidth: '450px',
            boxShadow: '0 0 20px rgba(255, 153, 51, 0.1)',
          },
        }
      );
    }
  };







  // Regular lesson generation function using backend API
  const handleGenerateLesson = async (e) => {
    e.preventDefault();

    // Prevent submission if already processing
    if (isButtonDisabled() || isGeneratingLesson) {
      return;
    }

    // Validate form fields
    if (!isFormValid()) {
      toast.error(
        t("Please fill in both Subject and Topic fields before generating a lesson."),
        {
          duration: 4000,
          style: {
            background: 'linear-gradient(135deg, rgba(15, 15, 25, 0.95), rgba(25, 25, 35, 0.95))',
            color: '#fff',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: '12px',
          },
        }
      );
      return;
    }

    const trimmedSubject = selectedSubject.trim();
    const trimmedTopic = topic.trim();

    setIsSubmitting(true);
    setShowResults(true);
    setLessonData(null); // Clear previous data

    // Show loading toast
    toast.loading(
      `🎓 Generating lesson content...\n📚 ${trimmedSubject}: ${trimmedTopic}\n⏱️ Please wait...`,
      {
        id: "lesson-generation",
        duration: Infinity,
        style: {
          background: 'linear-gradient(135deg, rgba(15, 15, 25, 0.95), rgba(25, 25, 35, 0.95))',
          color: '#fff',
          border: '1px solid rgba(255, 153, 51, 0.3)',
          borderRadius: '12px',
          fontSize: '14px',
          maxWidth: '450px',
          fontWeight: '500',
          boxShadow: '0 0 20px rgba(255, 153, 51, 0.1)',
        },
      }
    );

    try {
      // Get current language from localStorage
      const getCurrentLanguage = () => {
        try {
          const settings = localStorage.getItem("gurukul_settings");
          if (settings) {
            const parsed = JSON.parse(settings);
            return parsed.language || "english";
          }
        } catch (error) {
          console.error("Error reading language from storage:", error);
        }
        return "english";
      };

      const currentLanguage = getCurrentLanguage();

      console.log("📚 Calling generate_lesson API with params:", {
        subject: trimmedSubject,
        topic: trimmedTopic,
        include_wikipedia: includeWikipedia,
        use_knowledge_store: useKnowledgeStore,
        language: currentLanguage
      });

      // Call the backend API using RTK Query
      const result = await triggerGenerateLesson({
        subject: trimmedSubject,
        topic: trimmedTopic,
        include_wikipedia: includeWikipedia,
        use_knowledge_store: useKnowledgeStore,
        language: currentLanguage
      }).unwrap();

      console.log("✅ API Response received:", result);
      console.log("🎬 RAW API Response - YouTube video check:", {
        has_youtube_video: !!result.youtube_video,
        youtube_video: result.youtube_video,
        youtube_video_type: typeof result.youtube_video,
        all_result_keys: Object.keys(result)
      });

      // Check if result has error
      if (result.error) {
        throw new Error(result.error);
      }

      // Map the API response to lessonData format expected by the UI
      const mappedLessonData = {
        title: result.title || `Lesson: ${trimmedTopic}`,
        level: result.level || "intermediate",
        explanation: result.text || result.explanation || result.content || "",
        text: result.text || result.explanation || result.content || "",
        content: result.text || result.explanation || result.content || "",
        quiz: Array.isArray(result.quiz) ? result.quiz : [],
        activity: result.activity || null,
        question: result.question || null,
        shloka: result.shloka || null,
        translation: result.translation || null,
        subject: result.subject || trimmedSubject,
        topic: result.topic || trimmedTopic,
        sources: Array.isArray(result.sources) ? result.sources : [],
        knowledge_base_used: result.knowledge_base_used || false,
        wikipedia_used: result.wikipedia_used || false,
        generated_at: result.generated_at || new Date().toISOString(),
        status: result.status || "success",
        streaming: false,
        // YouTube video data - IMPORTANT: preserve exactly as received, even if null/undefined
        youtube_video: result.youtube_video !== undefined ? result.youtube_video : null,
        video_url: result.video_url !== undefined ? result.video_url : null,
        video_status: result.video_status !== undefined ? result.video_status : "not_found",
      };

      console.log("✅ Mapped lesson data:", mappedLessonData);
      console.log("🎬 MAPPED YouTube video data:", {
        youtube_video: mappedLessonData.youtube_video,
        has_youtube_video: !!mappedLessonData.youtube_video,
        is_null: mappedLessonData.youtube_video === null,
        is_undefined: mappedLessonData.youtube_video === undefined,
        video_url: mappedLessonData.video_url,
        video_status: mappedLessonData.video_status
      });

      // Set the lesson data
      setLessonData(mappedLessonData);

      // Dismiss loading toast and show success
      toast.dismiss("lesson-generation");
      toast.success(
        `🎉 ${t("Lesson generated successfully!")}\n📚 ${trimmedSubject}: ${trimmedTopic}`,
        {
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

      // Process karma for using subjects/lessons
      const effectiveUserId = userId || "guest-user";
      const karmaResult = processSubjectsUsage(effectiveUserId);
      if (karmaResult) {
        dispatchKarmaChange(karmaResult);
        toast.success(`+${karmaResult.change} Karma: ${karmaResult.reason}`, {
          position: "top-right",
          duration: 3000,
        });
      }

      // Trigger TTS for the content if available
      if (serviceHealthy && mappedLessonData.content) {
        console.log("🔊 Jupiter TTS: Triggering auto-play for lesson content");
        handleJupiterResponse(mappedLessonData.content);
      }

    } catch (error) {
      console.error("❌ Lesson generation failed:", error);
      console.error("❌ Error details:", {
        message: error.message,
        data: error.data,
        status: error.status
      });

      toast.dismiss("lesson-generation");
      toast.error(
        `⚠️ Failed to generate lesson\n🔍 Error: ${error.message || error.data?.error || "Unknown error"}\n💡 Please try again`,
        {
          duration: 8000,
          style: {
            background: 'linear-gradient(135deg, rgba(15, 15, 25, 0.95), rgba(25, 25, 35, 0.95))',
            color: '#fff',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: '12px',
            fontSize: '14px',
            maxWidth: '450px',
            boxShadow: '0 0 20px rgba(239, 68, 68, 0.1)',
          },
        }
      );

      setLessonData({
        error: error.message || error.data?.error || "Failed to generate lesson",
        subject: trimmedSubject,
        topic: trimmedTopic,
        status: "error"
      });
    } finally {
      setIsSubmitting(false);
    }
  };


  return (
    <GlassContainer>
      <div className="max-w-full mx-auto px-8 py-10">
        {/* Show input form only when no results are displayed */}
        {!showResults && (
          <>
            <div className="text-center mb-8">
              <h2
                className="text-5xl md:text-6xl font-extrabold mb-4 drop-shadow-xl transition-all duration-300 bg-gradient-to-r from-white to-amber-200 bg-clip-text text-transparent"
                style={{
                  fontFamily: "Nunito, sans-serif",
                }}
              >
                {t("Subject Explorer")}
              </h2>

              {/* Orchestration Status */}
              <div className="flex items-center justify-center space-x-4 mb-6">
                {integrationStatus?.integration_status?.overall_valid && (
                  <div className="flex items-center space-x-2 bg-green-500/20 px-3 py-1 rounded-full border border-green-500/40">
                    <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                    <span className="text-green-300 text-sm font-medium">{t("AI Enhanced")}</span>
                  </div>
                )}
              </div>
            </div>

            <p
              className="text-xl md:text-2xl font-medium mb-10 text-center text-white/90"
              style={{
                fontFamily: "Inter, Poppins, sans-serif",
              }}
            >
              {t("Select a subject and enter a topic to begin your learning journey")}
            </p>

            <div
              className="space-y-8 max-w-5xl mx-auto bg-white/10 p-10 rounded-xl backdrop-blur-md border border-white/20 shadow-lg"
            >
              <div className="relative group">
                <label className={`block mb-3 font-medium text-lg transition-opacity duration-300 ${
                  isButtonDisabled() ? 'text-white/50' : 'text-white/90'
                }`}>
                  {t("Subject")}:
                </label>
                <div className="relative">
                  <GlassInput
                    type="text"
                    placeholder={t("Type any subject (e.g. Mathematics, Physics, History)")}
                    value={selectedSubject}
                    onChange={(e) => setSelectedSubject(e.target.value)}
                    icon={Book}
                    autoComplete="off"
                    className={`text-lg py-3 ${isButtonDisabled() ? 'opacity-60 cursor-not-allowed' : ''}`}
                    disabled={isButtonDisabled()}
                  />
                </div>
              </div>

              <div>
                <label className={`block mb-3 font-medium text-lg transition-opacity duration-300 ${
                  isButtonDisabled() ? 'text-white/50' : 'text-white/90'
                }`}>
                  {t("Topic")}:
                </label>
                <GlassInput
                  type="text"
                  placeholder={t("Enter a topic to explore")}
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  icon={BookOpen}
                  className={`text-lg py-3 ${isButtonDisabled() ? 'opacity-60 cursor-not-allowed' : ''}`}
                  disabled={isButtonDisabled()}
                />
              </div>

              {/* Toggle Switches */}
             <div
  className={`space-y-6 transition-opacity duration-300 ${
    isButtonDisabled() ? "opacity-60" : ""
  }`}
>
    {/* Use Knowledge Store Toggle */}
    <div className="flex items-center justify-between p-4 bg-white/5 rounded-xl border border-white/20">
      <div>
        <label
          className={`font-medium text-lg block transition-opacity duration-300 ${
            isButtonDisabled() ? "text-white/50" : "text-white/90"
          }`}
        >
          {t("Use Knowledge Store")}
        </label>
        <p
          className={`text-sm mt-1 transition-opacity duration-300 ${
            isButtonDisabled() ? "text-white/40" : "text-white/60"
          }`}
        >
          {t("Access curated knowledge database")}
        </p>
      </div>
      <button
        type="button"
        onClick={() => setUseKnowledgeStore(!useKnowledgeStore)}
        disabled={isButtonDisabled()}
        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 focus:ring-offset-gray-900 ${
          useKnowledgeStore ? "bg-amber-500" : "bg-gray-600"
        } ${
          isButtonDisabled()
            ? "opacity-50 cursor-not-allowed"
            : "cursor-pointer"
        }`}
      >
        <span
          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform duration-200 ease-in-out ${
            useKnowledgeStore ? "translate-x-6" : "translate-x-1"
          }`}
        />
      </button>
    </div>

              <div className="flex justify-center mt-10 relative">
                {/* Regular Generation Button (using backend API) */}
                <div className="relative">
                  <GlassButton
                    type="button"
                    onClick={handleGenerateLesson}
                    icon={BookOpen}
                    variant="primary"
                    className={`px-8 py-4 text-lg font-medium transition-all duration-300 flex items-center justify-center ${
                      getButtonVisualState() === "invalid" ? "opacity-75" : ""
                    } ${
                      getButtonVisualState() === "disabled" || isGeneratingLesson
                        ? "cursor-not-allowed"
                        : ""
                    }`}
                    disabled={isButtonDisabled() || isGeneratingLesson}
                    aria-label={
                      isGeneratingLesson
                        ? t("Generating lesson content...")
                        : !isFormValid()
                        ? t("Please fill in both Subject and Topic fields")
                        : t("Generate lesson")
                    }
                  >
                    {isGeneratingLesson ? t("Generating...") : t("Generate Lesson")}
                  </GlassButton>
                </div>
              </div>
             </div>
            </div>
          </>
        )}

        {/* Results Section */}
        {/* Loading Overlay - Positioned outside of results container for proper centering */}
        {(isLoadingData || isSubmitting) && (
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[9999] flex items-center justify-center">
            <div className="bg-white/10 rounded-xl p-8 backdrop-blur-md border border-white/30 shadow-xl w-full max-w-lg mx-4">
              {/* Orange Loader - Perfectly Centered */}
              <div className="flex justify-center items-center mb-6">
                <div className="animate-spin rounded-full h-20 w-20 border-4 border-orange-500/30 border-t-orange-500 border-r-orange-500"></div>
              </div>

              <div className="text-center">
                <p className="text-white/90 text-xl font-medium mb-3">
                  📚 {t("Generating lesson content for")} "{selectedSubject.trim()}: {topic.trim()}"
                </p>
                <p className="text-amber-300 text-lg mb-4">
                  ⏱️ {t("This will take approximately 2 minutes. Please be patient.")}
                </p>
                <div className="bg-gradient-to-r from-orange-900/20 to-amber-900/20 rounded-lg p-4 border border-orange-500/30">
                  <p className="text-orange-200 text-sm">
                    🤖 {t("AI is analyzing your topic and creating personalized content")}
                    <br />
                    ✨ {t("Including explanations, activities, and questions")}
                    <br />
                    📖 {t("Integrating knowledge from multiple sources")}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {showResults && (
          <div className="bg-white/20 rounded-xl p-8 backdrop-blur-md border border-white/30 shadow-xl">

            {isLoadingData || isSubmitting ? (
              <div className="text-center py-8">
                <p className="text-white/70">{t("Loading...")}</p>
              </div>
            ) : isErrorData ? (
              <div className="text-red-400 text-center my-8 p-6 bg-white/5 rounded-xl border border-red-500/20">
                <p className="font-semibold mb-4 text-xl">
                  {t("Sorry, the service is currently unavailable. Please try again later.")}
                </p>
                <div className="mt-8">
                  <GlassButton
                    onClick={handleNewSearch}
                    variant="secondary"
                    className="px-6 py-3 text-lg"
                  >
                    {t("Try Again")}
                  </GlassButton>
                </div>
              </div>
            ) : subjectData ? (
              <div className="space-y-8">

                {/* Structured lesson content */}
                <div className="space-y-10">
                  {/* Title */}
                  {subjectData?.title && (
                    <div className="text-center">
                      <div className="mb-4">
                        <h2 className="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-amber-200">
                          {subjectData.title}
                        </h2>
                      </div>
                      <div className="mt-3 flex justify-center">
                        <div className="bg-gradient-to-r from-amber-500/30 to-amber-600/30 text-amber-200 px-4 py-1.5 rounded-full text-base font-medium border border-amber-500/30 shadow-lg">
                          {selectedSubject.trim()}: {topic.trim()}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Shloka and Translation */}
                  {subjectData?.shloka && (
                    <div className="bg-amber-900/20 p-8 rounded-xl border border-amber-500/40 shadow-lg mx-auto max-w-4xl">
                      <div className="mb-5">
                        <p className="italic text-amber-200 font-medium text-center text-xl leading-relaxed">
                          {subjectData.shloka}
                        </p>
                      </div>
                      {subjectData?.translation && (
                        <div className="bg-white/10 p-4 rounded-lg">
                          <p className="text-white/90 text-base text-center">
                            <span className="text-amber-300 font-medium">
                              {t("Translation")}:
                            </span>{" "}
                            {subjectData.translation}
                          </p>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Mode and Enhancement Indicators */}
                  {(() => {
                    const formattedLesson = formatEnhancedLessonData(subjectData);
                    const isEnhanced = formattedLesson?.isEnhanced;
                    const contentLength = subjectData?.content?.length || 0;
                    const isLongContent = contentLength > 500;
                    const contentType = subjectData?.content_type || 'standard';

                    return (
                      <div className="space-y-3">
                        {/* Mode Indicator */}
                        <div className={`p-3 rounded-xl border shadow-lg ${
                          isEnhanced
                            ? 'bg-gradient-to-r from-green-900/30 to-emerald-900/30 border-green-500/40'
                            : 'bg-gradient-to-r from-blue-900/30 to-indigo-900/30 border-blue-500/40'
                        }`}>
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-3">
                              <div className={`w-3 h-3 rounded-full animate-pulse ${
                                isEnhanced ? 'bg-green-500' : 'bg-blue-500'
                              }`}></div>
                              <span className={`font-medium ${
                                isEnhanced ? 'text-green-300' : 'text-blue-300'
                              }`}>
                                {isEnhanced ? `🚀 ${t("Enhanced Mode")}` : `📚 ${t("Basic Mode")}`}
                              </span>
                            </div>
                            <div className="flex items-center space-x-3 text-sm">
                              {/* Content Length Indicator */}
                              <span className={`px-2 py-1 rounded-full ${
                                isLongContent
                                  ? 'bg-purple-500/20 text-purple-200'
                                  : 'bg-gray-500/20 text-gray-200'
                              }`}>
                                📝 {isLongContent ? t("Comprehensive") : t("Concise")} ({contentLength} {t("chars")})
                              </span>

                              {/* Wikipedia Indicator */}
                              <span className={`px-2 py-1 rounded-full ${
                                includeWikipedia
                                  ? 'bg-orange-500/20 text-orange-200'
                                  : 'bg-gray-500/20 text-gray-200'
                              }`}>
                                {includeWikipedia ? `🌐 ${t("Wikipedia")}` : `🧠 ${t("Pure AI")}`}
                              </span>

                              {/* Content Type */}
                              {contentType !== 'standard' && (
                                <span className="bg-indigo-500/20 text-indigo-200 px-2 py-1 rounded-full">
                                  {contentType === 'concise' ? `⚡ ${t("Concise")}` : `📖 ${t("Basic")}`}
                                </span>
                              )}
                            </div>
                          </div>
                        </div>

                        {/* Enhanced Features (only for orchestration) */}
                        {isEnhanced && (
                          <div className="bg-gradient-to-r from-amber-900/20 to-yellow-900/20 p-3 rounded-xl border border-amber-500/30">
                            <div className="flex items-center space-x-4 text-sm text-amber-200">
                              {formattedLesson.ragEnhanced && (
                                <span className="bg-green-500/20 px-2 py-1 rounded-full">📚 {t("RAG Enhanced")}</span>
                              )}
                              {formattedLesson.triggersDetected > 0 && (
                                <span className="bg-amber-500/20 px-2 py-1 rounded-full">
                                  ⚡ {formattedLesson.triggersDetected} {t("Triggers")}
                                </span>
                              )}
                              {formattedLesson.sourceDocumentsCount > 0 && (
                                <span className="bg-blue-500/20 px-2 py-1 rounded-full">
                                  📖 {formattedLesson.sourceDocumentsCount} {t("Sources")}
                                </span>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })()}

                  {/* Explanation/Content - Enhanced User-Friendly Design */}
                  {(subjectData?.explanation || subjectData?.text || subjectData?.content) && (
                    <div className="relative">
                      {/* Content Header with Modern Design */}
                      <div className="mb-6">
                        <div className="flex items-center justify-between mb-4">
                          <div className="flex items-center space-x-4">
                            <div className="relative">
                              <div className="w-12 h-12 bg-gradient-to-br from-amber-400 via-amber-500 to-amber-600 rounded-2xl flex items-center justify-center shadow-xl transform rotate-3">
                                <span className="text-white font-bold text-lg transform -rotate-3">1</span>
                              </div>
                              <div className="absolute -top-1 -right-1 w-4 h-4 bg-gradient-to-br from-yellow-300 to-yellow-400 rounded-full animate-pulse"></div>
                            </div>
                            <div>
                              <h3 className="text-2xl font-bold text-white mb-1">
                                {subjectData?.streaming ? t("Live Lesson Content") : t("Lesson Content")}
                              </h3>
                              <p className="text-white/60 text-sm">
                                {subjectData?.streaming ? t("Content is being generated in real-time") : t("Comprehensive lesson explanation")}
                              </p>
                            </div>
                          </div>

                          {/* Status Indicators */}
                          <div className="flex items-center space-x-3">
                            {subjectData?.streaming && (
                              <div className="flex items-center space-x-2 bg-gradient-to-r from-green-500/20 to-emerald-500/20 px-4 py-2 rounded-full border border-green-500/30">
                                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                                <span className="text-green-300 text-sm font-medium">{t("LIVE")}</span>
                              </div>
                            )}
                            <div className="bg-white/10 px-3 py-1 rounded-full">
                              <span className="text-white/70 text-xs">📚 {t("Educational Content")}</span>
                            </div>
                          </div>
                        </div>

                        {/* Progress Bar for Streaming */}
                        {subjectData?.streaming && (
                          <div className="w-full bg-white/10 rounded-full h-1 mb-4">
                            <div className="bg-gradient-to-r from-amber-400 to-amber-500 h-1 rounded-full animate-pulse" style={{width: '70%'}}></div>
                          </div>
                        )}
                      </div>

                      {/* Content Display with Enhanced Styling */}
                      <div className="relative bg-gradient-to-br from-white/5 to-white/10 backdrop-blur-sm rounded-3xl p-10 border border-white/20 shadow-2xl w-full max-w-none overflow-hidden">
                        {/* Decorative Elements */}
                        <div className="absolute top-4 right-4 w-20 h-20 bg-gradient-to-br from-amber-500/10 to-amber-600/10 rounded-full blur-xl"></div>
                        <div className="absolute bottom-4 left-4 w-16 h-16 bg-gradient-to-br from-blue-500/10 to-purple-500/10 rounded-full blur-xl"></div>

                        {/* Content Area with Live Rendering */}
                        <div className="relative z-10">
                          {subjectData?.streaming ? (
                            <LessonStreamRenderer
                              streamingContent={subjectData?.content || ''}
                              isStreaming={subjectData?.streaming}
                              speed={25} // Optimal speed for readability
                              className="w-full"
                              onComplete={() => {
                                console.log('🎉 Lesson streaming completed');
                                // Auto-play TTS after streaming completes
                                if (serviceHealthy && subjectData?.content) {
                                  setTimeout(() => {
                                    console.log("🔊 Jupiter TTS: Triggering auto-play for streamed lesson content");
                                    handleJupiterResponse(subjectData.content);
                                  }, 1000);
                                }
                              }}
                            />
                          ) : subjectData?.content || subjectData?.explanation || subjectData?.text ? (
                            <LessonLiveRenderer
                              content={subjectData?.content || subjectData?.explanation || subjectData?.text || ''}
                              speed={20} // Optimal character rendering speed
                              lineDelay={150} // Smooth delay between lines
                              autoStart={true}
                              showCursor={true}
                              className="w-full"
                              onComplete={() => {
                                console.log('🎉 Lesson rendering completed');
                                // Auto-play TTS after rendering completes
                                const content = subjectData?.content || subjectData?.explanation || subjectData?.text;
                                if (serviceHealthy && content) {
                                  setTimeout(() => {
                                    console.log("🔊 Jupiter TTS: Triggering auto-play for rendered lesson content");
                                    handleJupiterResponse(content);
                                  }, 1000);
                                }
                              }}
                            />
                          ) : (
                            <div className="text-white/70 text-center py-8">
                              <p>{t("No content available to display.")}</p>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* YouTube Video Display - Appears below generated text */}
                  {(() => {
                    // More robust check for YouTube video
                    const youtubeVideo = subjectData?.youtube_video;
                    const hasYoutubeVideo = youtubeVideo && 
                                           typeof youtubeVideo === 'object' && 
                                           youtubeVideo !== null &&
                                           (youtubeVideo.embed_url || youtubeVideo.video_id);
                    
                    console.log("🎬 DEBUG - Checking YouTube video:", {
                      has_subjectData: !!subjectData,
                      youtube_video: youtubeVideo,
                      youtube_video_type: typeof youtubeVideo,
                      is_null: youtubeVideo === null,
                      is_undefined: youtubeVideo === undefined,
                      is_object: typeof youtubeVideo === 'object',
                      has_embed_url: !!youtubeVideo?.embed_url,
                      has_video_id: !!youtubeVideo?.video_id,
                      will_render: hasYoutubeVideo,
                      all_keys: subjectData ? Object.keys(subjectData) : [],
                      youtube_video_keys: youtubeVideo ? Object.keys(youtubeVideo) : []
                    });
                    
                    if (!hasYoutubeVideo) {
                      return null;
                    }
                    
                    // Build embed URL if not present but video_id is available
                    const embedUrl = youtubeVideo.embed_url || 
                                    (youtubeVideo.video_id ? `https://www.youtube.com/embed/${youtubeVideo.video_id}` : null);
                    
                    if (!embedUrl) {
                      console.warn("⚠️ YouTube video found but no embed URL available");
                      return null;
                    }
                    
                    return (
                      <div className="relative mb-8 mt-8">
                        <div className="mb-6">
                          <div className="flex items-center space-x-4">
                            <div className="relative">
                              <div className="w-12 h-12 bg-gradient-to-br from-red-400 via-red-500 to-red-600 rounded-2xl flex items-center justify-center shadow-xl transform rotate-3">
                                <span className="text-white font-bold text-lg transform -rotate-3">▶️</span>
                              </div>
                              <div className="absolute -top-1 -right-1 w-4 h-4 bg-gradient-to-br from-red-300 to-red-400 rounded-full animate-pulse"></div>
                            </div>
                            <div>
                              <h3 className="text-2xl font-bold text-white mb-1">
                                {t("Related Video")}
                              </h3>
                              <p className="text-white/60 text-sm">
                                {youtubeVideo.title || t("Watch this video to learn more")}
                              </p>
                            </div>
                          </div>
                        </div>

                        <div className="relative bg-gradient-to-br from-white/5 to-white/10 backdrop-blur-sm rounded-3xl p-6 border border-white/20 shadow-2xl overflow-hidden">
                          <div className="relative w-full" style={{ paddingBottom: "56.25%" }}> {/* 16:9 aspect ratio */}
                            <iframe
                              src={embedUrl}
                              title={youtubeVideo.title || "YouTube video player"}
                              frameBorder="0"
                              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                              allowFullScreen
                              className="absolute top-0 left-0 w-full h-full rounded-xl"
                              style={{ backgroundColor: "#000" }}
                            ></iframe>
                          </div>
                          {youtubeVideo.channel_title && (
                            <div className="mt-4 flex items-center justify-between">
                              <div className="flex items-center space-x-3">
                                <div className="w-8 h-8 bg-gradient-to-br from-red-500 to-red-600 rounded-full flex items-center justify-center">
                                  <span className="text-white text-xs">📺</span>
                                </div>
                                <div>
                                  <p className="text-white/90 font-medium">{youtubeVideo.channel_title}</p>
                                  <a
                                    href={youtubeVideo.video_url || `https://www.youtube.com/watch?v=${youtubeVideo.video_id}`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-red-400 hover:text-red-300 text-sm transition-colors"
                                  >
                                    {t("Watch on YouTube")} →
                                  </a>
                                </div>
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })()}

                  {/* Activity - Enhanced User-Friendly Design */}
                  {subjectData?.activity && (
                    <div className="relative mt-8">
                      {/* Activity Header */}
                      <div className="mb-6">
                        <div className="flex items-center space-x-4 mb-4">
                          <div className="relative">
                            <div className="w-12 h-12 bg-gradient-to-br from-indigo-400 via-indigo-500 to-purple-600 rounded-2xl flex items-center justify-center shadow-xl transform -rotate-3">
                              <span className="text-white font-bold text-lg transform rotate-3">2</span>
                            </div>
                            <div className="absolute -top-1 -right-1 w-4 h-4 bg-gradient-to-br from-purple-300 to-purple-400 rounded-full animate-pulse"></div>
                          </div>
                          <div>
                            <h3 className="text-2xl font-bold text-white mb-1">{t("Interactive Activity")}</h3>
                            <p className="text-white/60 text-sm">{t("Hands-on learning experience")}</p>
                          </div>
                        </div>
                      </div>

                      {/* Activity Content */}
                      <div className="relative bg-gradient-to-br from-indigo-500/10 to-purple-500/10 backdrop-blur-sm rounded-3xl p-8 border border-indigo-500/20 shadow-2xl">
                        {/* Decorative Elements */}
                        <div className="absolute top-4 right-4 w-20 h-20 bg-gradient-to-br from-indigo-500/10 to-purple-500/10 rounded-full blur-xl"></div>
                        <div className="absolute bottom-4 left-4 w-16 h-16 bg-gradient-to-br from-purple-500/10 to-pink-500/10 rounded-full blur-xl"></div>

                        {/* Activity Icon */}
                        <div className="absolute top-6 right-6 w-8 h-8 bg-gradient-to-br from-indigo-400 to-purple-500 rounded-full flex items-center justify-center">
                          <span className="text-white text-sm">🎯</span>
                        </div>

                        {/* Content */}
                        <div className="relative z-10">
                          <div className="bg-white/5 rounded-2xl p-6 border border-white/10">
                            {renderActivityContent(subjectData.activity)}
                          </div>

                          {/* Action Hint */}
                          <div className="mt-4 flex items-center justify-center">
                            <div className="bg-gradient-to-r from-indigo-500/20 to-purple-500/20 px-4 py-2 rounded-full border border-indigo-500/30">
                              <span className="text-indigo-300 text-sm font-medium">💡 {t("Try this activity to reinforce your learning")}</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Question - Enhanced User-Friendly Design */}
                  {subjectData?.question && (
                    <div className="relative mt-8">
                      {/* Question Header */}
                      <div className="mb-6">
                        <div className="flex items-center space-x-4 mb-4">
                          <div className="relative">
                            <div className="w-12 h-12 bg-gradient-to-br from-amber-400 via-orange-500 to-red-500 rounded-2xl flex items-center justify-center shadow-xl transform rotate-6">
                              <span className="text-white font-bold text-lg transform -rotate-6">3</span>
                            </div>
                            <div className="absolute -top-1 -right-1 w-4 h-4 bg-gradient-to-br from-yellow-300 to-orange-400 rounded-full animate-pulse"></div>
                          </div>
                          <div>
                            <h3 className="text-2xl font-bold text-white mb-1">{t("Reflection Question")}</h3>
                            <p className="text-white/60 text-sm">{t("Think deeply about this concept")}</p>
                          </div>
                        </div>
                      </div>

                      {/* Question Content */}
                      <div className="relative bg-gradient-to-br from-amber-500/10 to-orange-500/10 backdrop-blur-sm rounded-3xl p-8 border border-amber-500/20 shadow-2xl">
                        {/* Decorative Elements */}
                        <div className="absolute top-4 right-4 w-20 h-20 bg-gradient-to-br from-amber-500/10 to-orange-500/10 rounded-full blur-xl"></div>
                        <div className="absolute bottom-4 left-4 w-16 h-16 bg-gradient-to-br from-orange-500/10 to-red-500/10 rounded-full blur-xl"></div>

                        {/* Question Icon */}
                        <div className="absolute top-6 right-6 w-8 h-8 bg-gradient-to-br from-amber-400 to-orange-500 rounded-full flex items-center justify-center">
                          <span className="text-white text-sm">❓</span>
                        </div>

                        {/* Content */}
                        <div className="relative z-10">
                          <div className="bg-gradient-to-r from-white/5 to-white/10 rounded-2xl p-6 border border-white/10">
                            {renderQuestionContent(subjectData.question)}
                          </div>

                          {/* Thinking Prompt */}
                          <div className="mt-4 flex items-center justify-center">
                            <div className="bg-gradient-to-r from-amber-500/20 to-orange-500/20 px-4 py-2 rounded-full border border-amber-500/30">
                              <span className="text-amber-300 text-sm font-medium">🤔 {t("Take a moment to reflect on this")}</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Fallback for legacy content format - Enhanced */}
                  {(subjectData?.lesson || subjectData?.content) &&
                    !subjectData?.title && (
                      <div className="relative mt-8">
                        <div className="mb-6">
                          <div className="flex items-center space-x-4">
                            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
                              <span className="text-white text-sm">📚</span>
                            </div>
                            <div>
                              <h3 className="text-xl font-bold text-white">{t("Legacy Content")}</h3>
                              <p className="text-white/60 text-sm">{t("Formatted lesson content")}</p>
                            </div>
                          </div>
                        </div>
                        <div
                          className="content-container bg-gradient-to-br from-white/5 to-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20 shadow-xl break-words overflow-wrap-anywhere"
                          dangerouslySetInnerHTML={{
                            __html: subjectData?.lesson || subjectData?.content,
                          }}
                        />
                      </div>
                    )}

                  {/* Emergency fallback - Enhanced Debug Display */}
                  {!subjectData?.title && !subjectData?.lesson && !subjectData?.content && (
                    <div className="relative mt-8">
                      <div className="mb-6">
                        <div className="flex items-center space-x-4">
                          <div className="w-10 h-10 bg-gradient-to-br from-red-500 to-pink-600 rounded-xl flex items-center justify-center">
                            <span className="text-white text-sm">🔧</span>
                          </div>
                          <div>
                            <h3 className="text-xl font-bold text-white">{t("Debug Information")}</h3>
                            <p className="text-white/60 text-sm">{t("Raw lesson data for troubleshooting")}</p>
                          </div>
                        </div>
                      </div>
                      <div className="bg-gradient-to-br from-red-500/10 to-pink-500/10 backdrop-blur-sm rounded-2xl p-6 border border-red-500/20 shadow-xl">
                        <pre className="text-white/90 whitespace-pre-wrap text-sm overflow-auto max-h-96 bg-black/20 rounded-xl p-4">
                          {JSON.stringify(subjectData, null, 2)}
                        </pre>
                      </div>
                    </div>
                  )}
                </div>

                {/* YouTube Recommendations Container - Shows after lesson is generated */}
                <div className="mt-12">
                  <YouTubeRecommendations 
                    subject={subjectData?.subject || selectedSubject} 
                    topic={subjectData?.topic || topic} 
                  />
                </div>

                {/* Action buttons */}
                <div className="flex justify-center items-center gap-6 mt-12">
                  {/* New Search Button */}
                  <GlassButton
                    onClick={handleNewSearch}
                    variant="secondary"
                    className="px-6 py-3 text-lg font-medium shadow-lg hover:shadow-xl transition-all"
                  >
                    {t("New Search")}
                  </GlassButton>
                </div>
              </div>
            ) : (
              <div className="text-center p-12 bg-gradient-to-br from-white/5 to-white/10 backdrop-blur-sm rounded-3xl border border-white/20 shadow-2xl">
                {/* Empty State Icon */}
                <div className="mb-6">
                  <div className="w-20 h-20 bg-gradient-to-br from-amber-500/20 to-orange-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                    <span className="text-4xl">📚</span>
                  </div>
                  <div className="w-32 h-1 bg-gradient-to-r from-transparent via-amber-500/30 to-transparent mx-auto"></div>
                </div>

                {/* Message */}
                <div className="mb-8">
                  <h3 className="text-2xl font-bold text-white mb-3">{t("No Content Available")}</h3>
                  <p className="text-white/70 text-lg leading-relaxed max-w-md mx-auto">
                    {t("We couldn't find any content for this topic. Please try searching for a different subject or check your connection.")}
                  </p>
                </div>

                {/* Action Button */}
                <GlassButton
                  onClick={handleNewSearch}
                  variant="secondary"
                  className="px-8 py-4 text-lg font-medium shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:scale-105"
                >
                  <span className="flex items-center space-x-2">
                    <span>🔍</span>
                    <span>{t("Try Again")}</span>
                  </span>
                </GlassButton>
              </div>
            )}
          </div>
        )}

        {/* Original Video Player Section - Removed */}
        {false && (
          <div className="mt-8 bg-white/20 rounded-xl p-8 backdrop-blur-md border border-white/30 shadow-xl">
            <div className="text-center mb-6">
              <h3 className="text-3xl font-bold text-white mb-2">
                🎬 Generated Video
              </h3>
              <p className="text-amber-300 text-lg">
                📚 {generatedVideo.subject}: {generatedVideo.topic}
              </p>
              <p className="text-white/70 text-sm mt-2">
                🎥 Size: {(generatedVideo.size / 1024 / 1024).toFixed(2)} MB •
                📅 Generated: {new Date(generatedVideo.timestamp).toLocaleString()}
              </p>
            </div>

            <div className="flex justify-center">
              <div className="bg-black/50 rounded-xl p-4 backdrop-blur-sm border border-orange-500/30 shadow-2xl">
                <video
                  src={generatedVideo.url}
                  controls
                  autoPlay={false}
                  loop
                  muted
                  className="max-w-full max-h-96 rounded-lg shadow-lg"
                  style={{ maxWidth: '600px', width: '100%' }}
                  onLoadStart={() => console.log("🎥 Video load started")}
                  onLoadedData={() => console.log("🎥 Video data loaded")}
                  onCanPlay={() => console.log("🎥 Video can play")}
                  onError={(e) => {
                    console.error("🎥 Video error:", e);
                    console.error("🎥 Video error details:", e.target.error);
                    console.error("🎥 Video src:", generatedVideo.url);
                  }}
                >
                  <p className="text-white">
                    {t("Your browser doesn't support video playback.")}
                    <a
                      href={generatedVideo.url}
                      download="generated_video.mp4"
                      className="text-orange-400 hover:text-orange-300 underline ml-1"
                    >
                      {t("Download the video instead")}
                    </a>
                  </p>
                </video>

                {/* Debug info */}
                <div className="mt-4 p-3 bg-gray-800/50 rounded-lg text-xs text-white/70">
                  <p><strong>{t("Debug Info")}:</strong></p>
                  <p>URL: {generatedVideo.url}</p>
                  <p>{t("Content Type")}: {generatedVideo.contentType}</p>
                  <p>{t("Size")}: {generatedVideo.size} {t("bytes")}</p>
                  <p>{t("URL Valid")}: {generatedVideo.url ? t('Yes') : t('No')}</p>
                  <p>{t("URL Type")}: {generatedVideo.url?.startsWith('blob:') ? t('Blob URL') : t('Regular URL')}</p>
                </div>
              </div>
            </div>

            <div className="flex justify-center gap-4 mt-6">
              <a
                href={generatedVideo.url}
                download={`${generatedVideo.subject}_${generatedVideo.topic}_video.mp4`}
                className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-orange-600 to-amber-600 text-white font-medium rounded-lg hover:from-orange-700 hover:to-amber-700 transition-all duration-300 shadow-lg hover:shadow-xl"
              >
                📥 {t("Download Video")}
              </a>

              <button
                onClick={() => {
                  console.log("🎥 Testing video URL:", generatedVideo.url);
                  const video = document.querySelector('video');
                  if (video) {
                    console.log("🎥 Video element found:", video);
                    console.log("🎥 Video src:", video.src);
                    console.log("🎥 Video readyState:", video.readyState);
                    console.log("🎥 Video networkState:", video.networkState);
                    video.load(); // Force reload
                  }
                }}
                className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white font-medium rounded-lg hover:from-blue-700 hover:to-blue-800 transition-all duration-300 shadow-lg hover:shadow-xl"
              >
                🔄 {t("Test Video")}
              </button>

              <button
                onClick={hideVideo}
                className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-gray-600 to-gray-700 text-white font-medium rounded-lg hover:from-gray-700 hover:to-gray-800 transition-all duration-300 shadow-lg hover:shadow-xl"
              >
                ✕ {t("Close Video")}
              </button>
            </div>
          </div>
        )}
      </div>
    </GlassContainer>
  );
}
