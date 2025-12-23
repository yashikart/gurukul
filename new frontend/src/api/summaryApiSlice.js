import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";
import { CHAT_API_BASE_URL, UNIGURU_API_BASE_URL } from "../config";

// Create a separate API slice for summary endpoints using the correct port (8001)
export const summaryApiSlice = createApi({
  reducerPath: "summaryApi",
  baseQuery: fetchBaseQuery({
    baseUrl: CHAT_API_BASE_URL, // Use port 8001 for PDF/Image processing
    timeout: 120000, // 120 second timeout for file processing (increased for large files)
    prepareHeaders: (headers, { getState }) => {
      // Add any necessary headers here
      return headers;
    },
  }),
  tagTypes: ["Summary"],
  endpoints: (builder) => ({
    // Upload PDF for processing
    uploadPdfForSummary: builder.mutation({
      query: ({ file, llm = "grok", language = "english" }) => {
        const formData = new FormData();
        formData.append("file", file);
        // Backend endpoint signature: process_pdf(file: UploadFile = File(...), llm: str = "grok", language: str = "english")
        // FastAPI will read llm and language from query parameters for POST requests
        // Also add to FormData as backup (though backend doesn't use Form() for llm)
        formData.append("llm", llm);
        formData.append("language", language);

        const endpoint = `/process-pdf?llm=${encodeURIComponent(llm)}&language=${encodeURIComponent(language)}`;
        console.log("📤 Uploading PDF:", {
          fileName: file.name,
          fileSize: file.size,
          fileSizeMB: (file.size / (1024 * 1024)).toFixed(2),
          fileType: file.type,
          llm: llm,
          language: language,
          endpoint: endpoint,
          fullUrl: `${CHAT_API_BASE_URL}${endpoint}`
        });

        return {
          url: endpoint,
          method: "POST",
          body: formData,
          // Don't set Content-Type header - browser will set it with boundary for FormData
          // FastAPI will read llm and language from query parameters
        };
      },
      transformErrorResponse: (response, meta, arg) => {
        console.error("❌ PDF upload error:", {
          status: meta?.response?.status,
          statusText: meta?.response?.statusText,
          response: response
        });
        return response;
      },
      invalidatesTags: ["Summary"],
    }),

    // Upload image for processing
    uploadImageForSummary: builder.mutation({
      query: ({ file, llm = "grok", language = "english" }) => {
        const formData = new FormData();
        formData.append("file", file);
        // Backend endpoint signature: process_image(file: UploadFile = File(...), llm: str = "grok", language: str = "english")
        // FastAPI will read llm and language from query parameters for POST requests
        // Also add to FormData as backup
        formData.append("llm", llm);
        formData.append("language", language);

        const endpoint = `/process-img?llm=${encodeURIComponent(llm)}&language=${encodeURIComponent(language)}`;
        console.log("📤 Uploading Image:", {
          fileName: file.name,
          fileSize: file.size,
          fileSizeMB: (file.size / (1024 * 1024)).toFixed(2),
          fileType: file.type,
          llm: llm,
          language: language,
          endpoint: endpoint,
          fullUrl: `${CHAT_API_BASE_URL}${endpoint}`
        });

        return {
          url: endpoint,
          method: "POST",
          body: formData,
          // Don't set Content-Type header - browser will set it with boundary for FormData
          // FastAPI will read llm and language from query parameters
        };
      },
      transformErrorResponse: (response, meta, arg) => {
        console.error("❌ Image upload error:", {
          status: meta?.response?.status,
          statusText: meta?.response?.statusText,
          response: response
        });
        return response;
      },
      invalidatesTags: ["Summary"],
    }),

    // Get PDF summary
    getPdfSummary: builder.query({
      query: (language = "english") => {
        const lang = (language || "english").toLowerCase().startsWith("ar") ? "arabic" : "english";
        return `/summarize-pdf?language=${encodeURIComponent(lang)}`;
      },
      providesTags: ["Summary"],
    }),

    // Get image summary
    getImageSummary: builder.query({
      query: (language = "english") => {
        const lang = (language || "english").toLowerCase().startsWith("ar") ? "arabic" : "english";
        return `/summarize-img?language=${encodeURIComponent(lang)}`;
      },
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
