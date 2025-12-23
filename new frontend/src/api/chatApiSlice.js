import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";
import { CHAT_API_BASE_URL } from "../config";

// Create a separate API slice for chat with the correct base URL
export const chatApiSlice = createApi({
  reducerPath: "chatApi",
  baseQuery: fetchBaseQuery({
    baseUrl: CHAT_API_BASE_URL,
    prepareHeaders: (headers, { getState }) => {
      // You can add auth headers here if needed
      return headers;
    },
    timeout: 30000, // 30 second timeout for chat operations
  }),
  tagTypes: ["ChatHistory"],
  endpoints: (builder) => ({
    getChatHistory: builder.query({
      query: (userId) => ({
        url: "/chatbot",
        params: {
          user_id: userId || "guest-user",
          type: "chat_history",
          timestamp: new Date().toISOString(),
        },
      }),
      transformResponse: (response) => {
        // Handle the case where the API returns an error for first-time users
        if (
          response.error &&
          (response.error === "No queries yet" ||
            response.error === "No queries found for this user")
        ) {
          return {
            messages: [],
            isFirstQuery: true,
          };
        }
        return response;
      },
      providesTags: ["ChatHistory"],
    }),

    sendChatMessage: builder.mutation({
      query: ({ message, userId, llmModel = "grok" }) => ({
        url: "/chatpost",
        method: "POST",
        params: {
          user_id: userId || "guest-user",
        },
        body: {
          message,
          llm: llmModel,
          type: "chat_message",
        },
      }),
      // Optimistic update - add the user message to the chat history
      async onQueryStarted({ message, userId }, { dispatch, queryFulfilled }) {
        // Get the current timestamp
        const timestamp = new Date().toISOString();

        // Create a patch to update the cache optimistically
        const patchResult = dispatch(
          chatApiSlice.util.updateQueryData(
            "getChatHistory",
            userId || "guest-user",
            (draft) => {
              if (!draft.messages) {
                draft.messages = [];
              }

              // Add the user message to the chat history
              draft.messages.push({
                id: `temp-${Date.now()}`,
                sender: "user",
                content: message,
                timestamp,
              });
            }
          )
        );

        try {
          // Wait for the mutation to complete
          await queryFulfilled;

          // Invalidate the chat history to fetch the updated data
          dispatch(chatApiSlice.util.invalidateTags(["ChatHistory"]));
        } catch {
          // If the mutation fails, revert the optimistic update
          patchResult.undo();
        }
      },
      invalidatesTags: ["ChatHistory"],
    }),

    fetchChatbotResponse: builder.query({
      query: ({ message, userId }) => ({
        url: "/chatbot",
        params: {
          message,
          user_id: userId || "guest-user",
          timestamp: new Date().toISOString(),
          type: "chat_message",
        },
      }),
      transformResponse: (response) => {
        // Handle the case where the API returns an error for first-time users
        if (
          response.error &&
          (response.error === "No queries yet" ||
            response.error === "No queries found for this user")
        ) {
          return {
            message:
              "Hello! I'm your AI assistant. How can I help you today? (Note: This is the first query to the server)",
            isFirstQuery: true,
          };
        }
        return response;
      },
    }),
  }),
});

export const {
  useGetChatHistoryQuery,
  useSendChatMessageMutation,
  useLazyFetchChatbotResponseQuery,
} = chatApiSlice;