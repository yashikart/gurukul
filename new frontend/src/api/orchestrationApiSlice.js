import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";
import { WELLNESS_API_BASE_URL } from "../config";
import ttsService from "../services/ttsService";

// Create orchestration API slice for enhanced educational features
// Note: Orchestration system runs on port 8006 (Wellness API)
export const orchestrationApiSlice = createApi({
  reducerPath: "orchestrationApi",
  baseQuery: fetchBaseQuery({
    baseUrl: WELLNESS_API_BASE_URL,
    timeout: 90000, // 90 second timeout for orchestration calls
    prepareHeaders: (headers, { getState }) => {
      // Add any auth headers if needed
      headers.set("Content-Type", "application/json");
      return headers;
    },
  }),
  tagTypes: [
    "EnhancedLessons",
    "UserProgress",
    "UserAnalytics",
    "TriggerInterventions",
    "IntegrationStatus",
  ],
  endpoints: (builder) => ({
    // Enhanced lesson generation with orchestration
    generateEnhancedLesson: builder.mutation({
      query: ({
        subject,
        topic,
        user_id = "guest-user",
        quiz_score = null,
        use_orchestration = true,
        include_triggers = true,
        include_wikipedia = true,
      }) => {
        console.log("🎓 Generating enhanced lesson with orchestration:", {
          subject,
          topic,
          user_id,
          quiz_score,
          use_orchestration,
          include_triggers,
          include_wikipedia,
        });

        return {
          url: "/lessons/enhanced",
          method: "POST",
          body: {
            subject,
            topic,
            user_id,
            quiz_score,
            use_orchestration,
            include_triggers,
            include_wikipedia,
          },
        };
      },
      async onQueryStarted(arg, { queryFulfilled }) {
        try {
          const { data } = await queryFulfilled;

          // Trigger automatic TTS for enhanced lesson content
          if (data && (data.explanation || data.text || data.content)) {
            const contentToSpeak =
              data.explanation || data.text || data.content;

            if (contentToSpeak && contentToSpeak.trim()) {
              console.log(
                "🔊 Orchestration TTS: Triggering auto-play for enhanced lesson"
              );

              // Format content for better speech
              const formattedContent = contentToSpeak
                .replace(/\n\n/g, ". ")
                .replace(/\n/g, " ")
                .replace(/\*\*(.*?)\*\*/g, "$1") // Remove markdown bold
                .replace(/\*(.*?)\*/g, "$1"); // Remove markdown italic

              // Trigger TTS with a slight delay for better UX
              setTimeout(() => {
                ttsService
                  .autoPlayAI(formattedContent, {
                    delay: 1000,
                    volume: 0.8,
                  })
                  .catch((error) => {
                    console.warn(
                      "🔊 Orchestration TTS: Auto-play failed:",
                      error.message
                    );
                  });
              }, 500);
            }
          }
        } catch (error) {
          console.warn(
            "🔊 Orchestration TTS: Failed to process lesson for TTS:",
            error
          );
        }
      },
      invalidatesTags: (result, error, { subject, topic, user_id }) => [
        { type: "EnhancedLessons", id: `${subject}-${topic}` },
        { type: "UserProgress", id: user_id },
        { type: "UserAnalytics", id: user_id },
      ],
    }),

    // Get user progress and trigger analysis
    getUserProgress: builder.query({
      query: (user_id) => `/user-progress/${user_id}`,
      providesTags: (result, error, user_id) => [
        { type: "UserProgress", id: user_id },
      ],
    }),

    // Get comprehensive user analytics
    getUserAnalytics: builder.query({
      query: (user_id) => `/user-analytics/${user_id}`,
      providesTags: (result, error, user_id) => [
        { type: "UserAnalytics", id: user_id },
      ],
    }),

    // Manually trigger intervention for a user
    triggerIntervention: builder.mutation({
      query: ({ user_id, quiz_score = null }) => {
        console.log(
          "🚨 Triggering intervention for user:",
          user_id,
          "with quiz score:",
          quiz_score
        );

        const params = new URLSearchParams();
        if (quiz_score !== null) {
          params.append("quiz_score", quiz_score.toString());
        }

        return {
          url: `/trigger-intervention/${user_id}${
            params.toString() ? `?${params.toString()}` : ""
          }`,
          method: "POST",
        };
      },
      invalidatesTags: (result, error, { user_id }) => [
        { type: "TriggerInterventions", id: user_id },
        { type: "UserProgress", id: user_id },
        { type: "UserAnalytics", id: user_id },
      ],
    }),

    // Get integration status
    getIntegrationStatus: builder.query({
      query: () => {
        console.log("🔧 Checking orchestration integration status");
        return "/integration-status";
      },
      providesTags: ["IntegrationStatus"],
    }),

    // Health check for orchestration system
    checkOrchestrationHealth: builder.query({
      query: () => {
        console.log("❤️ Checking orchestration system health");
        return "/health";
      },
      providesTags: ["IntegrationStatus"],
    }),

    // Ask EduMentor for educational queries
    // Uses /edumentor endpoint from simple_api.py (port 8006)
    askEdumentor: builder.mutation({
      query: ({ query, user_id, quiz_score = null, language = "english" }) => {
        console.log("🎓 Asking EduMentor:", { query, user_id, quiz_score, language });
        return {
          url: "/edumentor",
          method: "POST",
          body: {
            query,
            user_id: user_id || "guest-user",
            language,
          },
        };
      },
      invalidatesTags: ["UserProgress", "UserAnalytics"],
    }),
  }),
});

// Export hooks for use in components
export const {
  useGenerateEnhancedLessonMutation,
  useGetUserProgressQuery,
  useLazyGetUserProgressQuery,
  useGetUserAnalyticsQuery,
  useLazyGetUserAnalyticsQuery,
  useTriggerInterventionMutation,
  useGetIntegrationStatusQuery,
  useLazyGetIntegrationStatusQuery,
  useCheckOrchestrationHealthQuery,
  useLazyCheckOrchestrationHealthQuery,
  useAskEdumentorMutation,
} = orchestrationApiSlice;

// Helper function to check if orchestration is available
export const checkOrchestrationAvailability = async (dispatch) => {
  try {
    const result = await dispatch(
      orchestrationApiSlice.endpoints.getIntegrationStatus.initiate()
    );

    if (result.data) {
      const isAvailable =
        result.data.integration_status?.overall_valid &&
        result.data.runtime_status?.orchestration_engine_initialized;

      console.log("🔧 Orchestration availability check:", isAvailable);
      return isAvailable;
    }

    return false;
  } catch (error) {
    console.warn("⚠️ Orchestration availability check failed:", error);
    return false;
  }
};

// Helper function to format enhanced lesson data for display
export const formatEnhancedLessonData = (lessonData) => {
  if (!lessonData) return null;

  // Check if this is an orchestration-enhanced lesson
  const isEnhanced =
    lessonData.source?.includes("orchestration") ||
    lessonData.enhanced_features ||
    lessonData.orchestration_data;

  if (isEnhanced) {
    // Extract orchestration-specific data
    const orchestrationData = lessonData.orchestration_data || {};
    const enhancedFeatures = lessonData.enhanced_features || {};

    return {
      // Basic lesson data
      subject: lessonData.subject,
      topic: lessonData.topic,
      content: lessonData.content,

      // Enhanced features
      isEnhanced: true,
      source: lessonData.source,

      // Orchestration-specific data
      activity: orchestrationData.activity_details || {},
      triggers: orchestrationData.triggers || [],
      interventions: orchestrationData.interventions || [],
      sourceDocuments: orchestrationData.source_documents || [],

      // Metrics
      triggersDetected: enhancedFeatures.triggers_detected || 0,
      interventionsApplied: enhancedFeatures.interventions_applied || 0,
      sourceDocumentsCount: enhancedFeatures.source_documents_count || 0,
      ragEnhanced: enhancedFeatures.rag_enhanced || false,

      // Timestamps
      generatedAt: lessonData.generated_at,
      timestamp: orchestrationData.timestamp,
    };
  }

  // Return basic lesson format for non-enhanced lessons
  return {
    subject: lessonData.subject,
    topic: lessonData.topic,
    content: lessonData.content,
    isEnhanced: false,
    source: lessonData.source || "basic",
    generatedAt: lessonData.generated_at,
  };
};

// Helper function to format user progress data
export const formatUserProgressData = (progressData) => {
  if (!progressData) return null;

  const educationalProgress = progressData.educational_progress || {};
  const recommendations = progressData.recommendations || [];
  const triggers = progressData.triggers_detected || [];

  return {
    userId: progressData.user_id,
    lastActive: progressData.last_active,
    interactionCount: progressData.interaction_count || 0,

    // Educational metrics
    quizScores: educationalProgress.quiz_scores || [],
    learningTopics: educationalProgress.learning_topics || [],
    averageScore:
      educationalProgress.quiz_scores?.length > 0
        ? educationalProgress.quiz_scores.reduce((a, b) => a + b, 0) /
          educationalProgress.quiz_scores.length
        : null,

    // Recommendations and triggers
    recommendations: recommendations.map((rec) => ({
      type: rec.type,
      priority: rec.priority,
      message: rec.message,
      action: rec.action,
    })),

    triggers: triggers.map((trigger) => ({
      type: trigger.type,
      severity: trigger.severity,
      message: trigger.message,
      recommendedAction: trigger.recommended_action,
    })),

    // Status indicators
    needsIntervention: triggers.some((t) => t.severity === "high"),
    performanceStatus:
      educationalProgress.quiz_scores?.length > 0
        ? educationalProgress.quiz_scores.slice(-3).every((score) => score < 60)
          ? "struggling"
          : "good"
        : "unknown",
  };
};

export default orchestrationApiSlice;
