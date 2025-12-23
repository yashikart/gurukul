import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";
import { API_BASE_URL, AGENT_API_BASE_URL } from "../config";

// Create a separate API slice for lesson endpoints using the same base URL
export const lessonApiSlice = createApi({
  reducerPath: "lessonApi",
  baseQuery: fetchBaseQuery({
    baseUrl: API_BASE_URL,
    timeout: 600000, // 10 minute timeout for Knowledge Store (can take 6+ minutes)
  }),
  tagTypes: ["Lessons"],
  endpoints: (builder) => ({
    // Get existing lesson data
    getLessonData: builder.query({
      query: ({ subject, topic }) => ({
        url: `/lessons/${encodeURIComponent(subject)}/${encodeURIComponent(
          topic
        )}`,
        method: "GET",
      }),
      providesTags: (result, error, { subject, topic }) => [
        { type: "Lessons", id: `${subject}-${topic}` },
      ],
    }),

    // Generate lesson using GET endpoint with parameters
    generateLesson: builder.query({
      query: ({
        subject,
        topic,
        include_wikipedia = true,
        use_knowledge_store = true,
        language = "english",
      }) => {
        // Log the request for debugging
        console.log("📚 Generating lesson with parameters:", {
          subject,
          topic,
          include_wikipedia,
          use_knowledge_store,
          language,
        });

        const params = new URLSearchParams({
          subject: subject,
          topic: topic,
          include_wikipedia: include_wikipedia.toString(),
          use_knowledge_store: use_knowledge_store.toString(),
          language: language,
        });

        const requestConfig = {
          url: `/generate_lesson?${params.toString()}`,
          method: "GET",
          // Ensure proper headers for JSON response
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
          },
        };

        console.log("📡 API Request config:", requestConfig);
        console.log("🌐 Full URL:", `${API_BASE_URL}${requestConfig.url}`);

        return requestConfig;
      },
      transformResponse: (response, meta, arg) => {
        console.log("📥 API Raw Response:", response);
        console.log("📥 API Response Type:", typeof response);
        console.log("📥 API Response Status:", meta?.response?.status);
        console.log("📥 API Args:", arg);
        
        // Check for error responses
        if (meta?.response?.status && meta.response.status >= 400) {
          console.error("❌ API Error Response:", response);
          throw new Error(response?.error || `API returned status ${meta.response.status}`);
        }
        
        // Handle different response formats
        if (!response) {
          console.error("❌ Empty response received");
          throw new Error("Empty response from API");
        }

        // If response is already an object (parsed JSON), use it directly
        if (typeof response === 'object' && response !== null) {
          console.log("✅ Response is already an object");
          
          // Check if response has error field
          if (response.error) {
            console.error("❌ API returned error:", response.error);
            throw new Error(response.error);
          }
          
          // Normalize the response structure to match frontend expectations
          const normalizedResponse = {
            // Map backend fields to frontend expected fields
            title: response.title || `Lesson: ${arg.topic}`,
            level: response.level || "intermediate",
            explanation: response.text || response.explanation || "",
            text: response.text || response.explanation || "",
            content: response.text || response.explanation || "",
            quiz: Array.isArray(response.quiz) ? response.quiz : [],
            tts: response.tts !== undefined ? response.tts : true,
            subject: response.subject || arg.subject,
            topic: response.topic || arg.topic,
            sources: Array.isArray(response.sources) ? response.sources : [],
            knowledge_base_used: response.knowledge_base_used || false,
            wikipedia_used: response.wikipedia_used || false,
            generated_at: response.generated_at || new Date().toISOString(),
            status: response.status || "success",
            // YouTube video fields - CRITICAL: preserve exactly as backend sends
            youtube_video: response.youtube_video !== undefined ? response.youtube_video : null,
            video_url: response.video_url !== undefined ? response.video_url : null,
            video_status: response.video_status !== undefined ? response.video_status : "not_found",
            // Include all original fields for backward compatibility (spread after to ensure backend values take precedence)
            ...response
          };
          
          // Log YouTube video data for debugging
          console.log("🎬 API Slice - YouTube video in normalized response:", {
            has_youtube_video: !!normalizedResponse.youtube_video,
            youtube_video: normalizedResponse.youtube_video,
            video_status: normalizedResponse.video_status,
            video_url: normalizedResponse.video_url
          });
          
          console.log("✅ Normalized Response:", normalizedResponse);
          console.log("✅ Response keys:", Object.keys(normalizedResponse));
          return normalizedResponse;
        }

        // If response is a string, try to parse it as JSON
        if (typeof response === 'string') {
          try {
            console.log("📝 Attempting to parse string response as JSON");
            const parsed = JSON.parse(response);
            console.log("✅ Successfully parsed JSON:", parsed);
            
            // Check for error in parsed response
            if (parsed.error) {
              console.error("❌ Parsed response contains error:", parsed.error);
              throw new Error(parsed.error);
            }
            
            // Normalize the parsed response
            const normalized = {
              title: parsed.title || `Lesson: ${arg.topic}`,
              level: parsed.level || "intermediate",
              explanation: parsed.text || parsed.explanation || "",
              text: parsed.text || parsed.explanation || "",
              content: parsed.text || parsed.explanation || "",
              quiz: Array.isArray(parsed.quiz) ? parsed.quiz : [],
              tts: parsed.tts !== undefined ? parsed.tts : true,
              subject: parsed.subject || arg.subject,
              topic: parsed.topic || arg.topic,
              sources: Array.isArray(parsed.sources) ? parsed.sources : [],
              knowledge_base_used: parsed.knowledge_base_used || false,
              wikipedia_used: parsed.wikipedia_used || false,
              generated_at: parsed.generated_at || new Date().toISOString(),
              status: parsed.status || "success",
              ...parsed
            };
            
            console.log("✅ Normalized parsed response:", normalized);
            return normalized;
          } catch (parseError) {
            console.error("❌ Failed to parse response as JSON:", parseError);
            console.error("❌ Response string preview:", response.substring(0, 500));
            // Return a fallback structure
            return {
              title: `Lesson: ${arg.topic}`,
              level: "intermediate",
              explanation: response,
              text: response,
              content: response,
              quiz: [],
              tts: true,
              subject: arg.subject,
              topic: arg.topic,
              sources: [],
              knowledge_base_used: false,
              wikipedia_used: false,
              generated_at: new Date().toISOString(),
              status: "success"
            };
          }
        }

        // Fallback: return response as-is
        console.warn("⚠️ Unknown response format, returning as-is");
        return response;
      },
      transformErrorResponse: (response, meta, arg) => {
        console.error("❌ API Error Response:", response);
        console.error("❌ Error Meta:", meta);
        
        // Extract error message from different possible formats
        let errorMessage = "Failed to generate lesson";
        
        if (typeof response === 'string') {
          try {
            const parsed = JSON.parse(response);
            errorMessage = parsed.error || parsed.message || errorMessage;
          } catch {
            errorMessage = response;
          }
        } else if (response && typeof response === 'object') {
          errorMessage = response.error || response.message || errorMessage;
        }
        
        return {
          error: errorMessage,
          status: meta?.response?.status || 500,
          subject: arg?.subject,
          topic: arg?.topic
        };
      },
      providesTags: (result, error, { subject, topic }) => [
        { type: "Lessons", id: `${subject}-${topic}` },
      ],
    }),

    // Create new lesson
    createLesson: builder.mutation({
      query: ({
        subject,
        topic,
        user_id,
        include_wikipedia = true,
        force_regenerate = false,
      }) => {
        const userId = user_id || "guest-user";

        return {
          url: "/lessons",
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: {
            subject,
            topic,
            user_id: userId,
            include_wikipedia,
            force_regenerate,
          },
        };
      },
      invalidatesTags: (result, error, { subject, topic }) => [
        { type: "Lessons", id: `${subject}-${topic}` },
      ],
    }),

    // Get YouTube recommendations - uses AGENT_API_BASE_URL (port 8005) for subject generation service
    getYouTubeRecommendations: builder.query({
      queryFn: async ({ subject, topic, max_results = 5 }, _queryApi, _extraOptions, baseQuery) => {
        try {
          const params = new URLSearchParams({
            subject: subject,
            topic: topic,
            max_results: max_results.toString(),
          });

          // Use AGENT_API_BASE_URL for subject generation service endpoints
          const baseUrl = AGENT_API_BASE_URL || "http://localhost:8005";
          const url = `${baseUrl}/youtube_recommendations?${params.toString()}`;

          console.log("🎬 [Frontend] Fetching YouTube recommendations");
          console.log("🎬 [Frontend] Base URL:", baseUrl);
          console.log("🎬 [Frontend] Full URL:", url);
          console.log("🎬 [Frontend] Subject:", subject, "Topic:", topic);

          const response = await fetch(url, {
            method: "GET",
            headers: {
              "Accept": "application/json",
              "Content-Type": "application/json",
            },
            mode: "cors",
          });

          console.log("🎬 [Frontend] Response status:", response.status, response.statusText);

          if (!response.ok) {
            let errorText = "";
            try {
              errorText = await response.text();
            } catch (e) {
              errorText = "Could not read error response";
            }
            
            console.error("❌ [Frontend] YouTube Recommendations API Error:", {
              status: response.status,
              statusText: response.statusText,
              error: errorText,
              url: url,
            });
            
            return {
              error: {
                status: response.status,
                error: `API error: ${response.status} ${response.statusText}. ${errorText.substring(0, 100)}`,
              },
            };
          }

          const data = await response.json();
          console.log("✅ [Frontend] YouTube Recommendations API Response:", data);
          console.log("✅ [Frontend] Recommendations count:", data.count || 0);

          return {
            data: {
              recommendations: data.recommendations || [],
              subject: data.subject,
              topic: data.topic,
              count: data.count || 0,
            },
          };
        } catch (error) {
          console.error("❌ [Frontend] YouTube Recommendations Fetch Error:", error);
          console.error("❌ [Frontend] Error type:", error.name);
          console.error("❌ [Frontend] Error message:", error.message);
          console.error("❌ [Frontend] Error stack:", error.stack);
          
          // Check if it's a network error
          if (error.name === "TypeError" && error.message.includes("fetch")) {
            return {
              error: {
                status: "NETWORK_ERROR",
                error: `Network error: Could not connect to ${AGENT_API_BASE_URL || "http://localhost:8005"}. Please ensure the subject generation service is running.`,
              },
            };
          }
          
          return {
            error: {
              status: "FETCH_ERROR",
              error: error.message || "Failed to fetch YouTube recommendations",
            },
          };
        }
      },
    }),
  }),
});

// Keep the original subjects API slice for backward compatibility
import { apiSlice } from "./apiSlice";

export const subjectsApiSlice = apiSlice.injectEndpoints({
  endpoints: (builder) => ({
    getSubjects: builder.query({
      query: () => "/subjects",
      transformResponse: (response) => {
        // You can transform the response data here if needed
        return response;
      },
      providesTags: ["Subjects"],
    }),
    getSubjectById: builder.query({
      query: (id) => `/subjects/${id}`,
      providesTags: (result, error, id) => [{ type: "Subjects", id }],
    }),
    addSubject: builder.mutation({
      query: (subject) => ({
        url: "/subjects",
        method: "POST",
        body: subject,
      }),
      invalidatesTags: ["Subjects"],
    }),
    updateSubject: builder.mutation({
      query: ({ id, ...subject }) => ({
        url: `/subjects/${id}`,
        method: "PUT",
        body: subject,
      }),
      invalidatesTags: (result, error, { id }) => [{ type: "Subjects", id }],
    }),
    deleteSubject: builder.mutation({
      query: (id) => ({
        url: `/subjects/${id}`,
        method: "DELETE",
      }),
      invalidatesTags: ["Subjects"],
    }),
  }),
});

// Export hooks from lesson API slice
export const {
  useGetLessonDataQuery,
  useLazyGetLessonDataQuery,
  useGenerateLessonQuery,
  useLazyGenerateLessonQuery,
  useCreateLessonMutation,
  useGetYouTubeRecommendationsQuery,
  useLazyGetYouTubeRecommendationsQuery,
} = lessonApiSlice;

// Export hooks from subjects API slice (for backward compatibility)
export const {
  useGetSubjectsQuery,
  useGetSubjectByIdQuery,
  useAddSubjectMutation,
  useUpdateSubjectMutation,
  useDeleteSubjectMutation,
} = subjectsApiSlice;
