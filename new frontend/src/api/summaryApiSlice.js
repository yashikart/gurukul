import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";
import { CHAT_API_BASE_URL, UNIGURU_API_BASE_URL } from "../config";

// Create a separate API slice for summary endpoints using the correct port (8001)
export const summaryApiSlice = createApi({
  reducerPath: "summaryApi",
  baseQuery: fetchBaseQuery({
    baseUrl: CHAT_API_BASE_URL, // Use port 8001 for PDF/Image processing
    timeout: 60000, // 60 second timeout for file processing
  }),
  tagTypes: ["Summary"],
  endpoints: (builder) => ({
    // Upload PDF for processing
    uploadPdfForSummary: builder.mutation({
      query: ({ file, llm = "grok" }) => {
        const formData = new FormData();
        formData.append("file", file);
        formData.append("llm", llm);

        return {
          url: "/process-pdf",
          method: "POST",
          body: formData,
        };
      },
      invalidatesTags: ["Summary"],
    }),

    // Upload image for processing
    uploadImageForSummary: builder.mutation({
      query: ({ file, llm = "grok" }) => {
        const formData = new FormData();
        formData.append("file", file);
        formData.append("llm", llm);

        return {
          url: "/process-img",
          method: "POST",
          body: formData,
        };
      },
      invalidatesTags: ["Summary"],
    }),

    // Get PDF summary
    getPdfSummary: builder.query({
      query: () => "/summarize-pdf",
      providesTags: ["Summary"],
    }),

    // Get image summary
    getImageSummary: builder.query({
      query: () => "/summarize-img",
      providesTags: ["Summary"],
    }),

    // Legacy upload file for summary (keeping for backward compatibility)
    uploadFileForSummary: builder.mutation({
      query: (file) => {
        const formData = new FormData();
        formData.append("file", file);

        return {
          url: "/process-pdf",
          method: "POST",
          body: formData,
        };
      },
      invalidatesTags: ["Summary"],
    }),

    getFileSummary: builder.query({
      query: (fileId) => `/get-summary/${fileId}`,
      providesTags: (result, error, fileId) => [
        { type: "Summary", id: fileId },
      ],
    }),

    getLastPdfSummary: builder.query({
      query: () => "/get-last-pdf",
      providesTags: ["Summary"],
    }),

    // Additional endpoints for summary-related operations
    getSummaryById: builder.query({
      query: (summaryId) => `/summary/${summaryId}`,
      providesTags: (result, error, summaryId) => [
        { type: "Summary", id: summaryId },
      ],
    }),

    deleteSummary: builder.mutation({
      query: (summaryId) => ({
        url: `/summary/${summaryId}`,
        method: "DELETE",
      }),
      invalidatesTags: ["Summary"],
    }),

    // UniGuru streaming endpoints
    uploadPdfForUniGuru: builder.mutation({
      query: ({ file }) => {
        const formData = new FormData();
        formData.append("file", file);
        formData.append("llm", "uniguru");

        return {
          url: `${UNIGURU_API_BASE_URL}/process-pdf`,
          method: "POST",
          body: formData,
          headers: {
            "ngrok-skip-browser-warning": "true",
          },
        };
      },
      invalidatesTags: ["Summary"],
    }),

    uploadImageForUniGuru: builder.mutation({
      query: ({ file }) => {
        const formData = new FormData();
        formData.append("file", file);
        formData.append("llm", "uniguru");

        return {
          url: `${UNIGURU_API_BASE_URL}/process-img`,
          method: "POST",
          body: formData,
          headers: {
            "ngrok-skip-browser-warning": "true",
          },
        };
      },
      invalidatesTags: ["Summary"],
    }),

    getUniGuruPdfSummary: builder.query({
      query: () => ({
        url: `${UNIGURU_API_BASE_URL}/summarize-pdf`,
        headers: {
          "ngrok-skip-browser-warning": "true",
        },
      }),
      providesTags: ["Summary"],
    }),

    getUniGuruImageSummary: builder.query({
      query: () => ({
        url: `${UNIGURU_API_BASE_URL}/summarize-img`,
        headers: {
          "ngrok-skip-browser-warning": "true",
        },
      }),
      providesTags: ["Summary"],
    }),
  }),
});

export const {
  useUploadPdfForSummaryMutation,
  useUploadImageForSummaryMutation,
  useGetPdfSummaryQuery,
  useLazyGetPdfSummaryQuery,
  useGetImageSummaryQuery,
  useLazyGetImageSummaryQuery,
  useUploadFileForSummaryMutation,
  useGetFileSummaryQuery,
  useGetLastPdfSummaryQuery,
  useGetSummaryByIdQuery,
  useDeleteSummaryMutation,
  // UniGuru endpoints
  useUploadPdfForUniGuruMutation,
  useUploadImageForUniGuruMutation,
  useGetUniGuruPdfSummaryQuery,
  useLazyGetUniGuruPdfSummaryQuery,
  useGetUniGuruImageSummaryQuery,
  useLazyGetUniGuruImageSummaryQuery,
} = summaryApiSlice;
