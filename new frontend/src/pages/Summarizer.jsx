import React, { useState, useRef, useEffect } from "react";
import GlassContainer from "../components/GlassContainer";
import { FiUpload, FiFileText, FiX } from "react-icons/fi";
import { useNavigate } from "react-router-dom";
import { toast } from "react-hot-toast";
import { useTranslation } from "react-i18next";
import { useAuth } from "../context/AuthContext";
import chatLogsService from "../services/chatLogsService";
import { CHAT_API_BASE_URL } from "../config";
import { useTTS } from "../hooks/useTTS";
import {
  useUploadPdfForSummaryMutation,
  useUploadImageForSummaryMutation,
  useLazyGetPdfSummaryQuery,
  useLazyGetImageSummaryQuery,
  useUploadPdfForUniGuruMutation,
  useUploadImageForUniGuruMutation,
  useLazyGetUniGuruPdfSummaryQuery,
  useLazyGetUniGuruImageSummaryQuery,
} from "../api/summaryApiSlice";
import { processSummarizerUsage, dispatchKarmaChange } from "../utils/karmaManager";

export default function Summarizer() {
  const { t, i18n } = useTranslation();
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const [showStreamingView, setShowStreamingView] = useState(false);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [selectedModel, setSelectedModel] = useState("grok"); // Using Grok model (default)
  const [userId, setUserId] = useState(null);
  const { user } = useAuth();
  const isSignedIn = !!user;
  const fileInputRef = useRef(null);
  const streamingControllerRef = useRef(null);
  const navigate = useNavigate();

  // RTK Query hooks - Using local backend with UniGuru model
  const [uploadPdfForSummary] = useUploadPdfForSummaryMutation();
  const [uploadImageForSummary] = useUploadImageForSummaryMutation();
  const [getPdfSummary] = useLazyGetPdfSummaryQuery();
  const [getImageSummary] = useLazyGetImageSummaryQuery();

  // TTS functionality
  const { autoPlayAI, serviceHealthy: ttsServiceHealthy } = useTTS({
    autoPlay: true
  });

  // UniGuru is the fixed model - no need to load from localStorage

  // Get user ID on component mount
  useEffect(() => {
    if (isSignedIn && user) setUserId(user.id);
    else setUserId("guest-user");
  }, [isSignedIn, user]);

  // Cleanup preview URL when file changes or component unmounts
  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];
    if (selectedFile) {
      const validTypes = [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "image/jpeg",
        "image/png",
      ];

      if (!validTypes.includes(selectedFile.type)) {
        const errorMsg = "Please upload a PDF, DOC, DOCX, JPG, or PNG file";
        setError(errorMsg);
        toast.error(errorMsg, {
          icon: "❌",
          position: "bottom-right",
        });
        return;
      }

      if (selectedFile.size > 10 * 1024 * 1024) {
        const errorMsg = "File size should be less than 10MB";
        setError(errorMsg);
        toast.error(errorMsg, {
          icon: "⚠️",
          position: "bottom-right",
        });
        return;
      }

      // Revoke previous preview URL if any
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
      setFile(selectedFile);
      setPreviewUrl(URL.createObjectURL(selectedFile));
      setError("");

      // Show success toast for file selection
      toast.success(`File "${selectedFile.name}" selected`, {
        icon: "📄",
        position: "bottom-right",
      });
    }
  };

  const getSummary = async (isImage) => {
    try {
      console.log(`📥 Fetching ${isImage ? 'image' : 'PDF'} summary...`);

      // Determine language for fetching summaries
      const currentLanguage = i18n.language && i18n.language.toLowerCase().startsWith("ar") ? "arabic" : "english";
      
      let response;
      if (isImage) {
        response = await getImageSummary(currentLanguage).unwrap();
      } else {
        response = await getPdfSummary(currentLanguage).unwrap();
      }
      
      console.log("✅ Summary response received:", response);
      
      // Validate response
      if (!response || (!response.answer && !response.summary && !response.content)) {
        console.warn("⚠️ Response missing content fields:", response);
        throw new Error("Summary response is empty or invalid");
      }
      
      return response;
    } catch (error) {
      console.error("❌ Failed to fetch summary:", error);
      const errorMessage = error.data?.error || error.message || "Failed to fetch summary";
      throw new Error(errorMessage);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      const errorMsg = "Please select a file first";
      setError(errorMsg);
      toast.error(errorMsg, {
        icon: "📁",
        position: "bottom-right",
      });
      return;
    }

    try {
      setLoading(true);
      setError("");

      const isImage = file.type.startsWith("image/");

      // Save the selected model to localStorage for use in other components
      localStorage.setItem("selectedAIModel", selectedModel);

      // Show upload progress toast
      toast.loading(
        `Uploading file to ${
          selectedModel.charAt(0).toUpperCase() + selectedModel.slice(1)
        }...`,
        {
          id: "upload-progress",
          position: "bottom-right",
        }
      );

      // Get current language (map i18n language to backend format)
      // Handle Arabic language codes: "ar", "ar-SA", "ar-EG", etc.
      const currentLanguage = i18n.language && i18n.language.toLowerCase().startsWith("ar") ? "arabic" : "english";
      console.log("🌐 Language detection:", { i18nLanguage: i18n.language, currentLanguage });

      // Upload file using RTK Query with Grok model
      if (isImage) {
        await uploadImageForSummary({
          file,
          llm: "grok",
          language: currentLanguage,
        }).unwrap();
      } else {
        await uploadPdfForSummary({
          file,
          llm: "grok",
          language: currentLanguage,
        }).unwrap();
      }

      // Dismiss upload progress toast
      toast.dismiss("upload-progress");

      // Show analyzing toast
      toast.loading("Analyzing document...", {
        id: "analyzing-progress",
        position: "bottom-right",
      });

      // Get summary from the appropriate endpoint based on file type
      const summaryResponse = await getSummary(isImage);

      // Dismiss analyzing toast
      toast.dismiss("analyzing-progress");

      // Save data to localStorage
      localStorage.setItem("summaryData", JSON.stringify(summaryResponse));
      localStorage.setItem(
        "fileData",
        JSON.stringify({
          type: file.type,
          name: file.name,
        })
      );

      // Show success toast
      toast.success("Document analyzed successfully!", {
        icon: "🎉",
        position: "bottom-right",
        duration: 3000,
      });

      // Process karma for using summarizer
      const effectiveUserId = userId || "guest-user";
      const karmaResult = processSummarizerUsage(effectiveUserId);
      if (karmaResult) {
        dispatchKarmaChange(karmaResult);
        toast.success(`+${karmaResult.change} Karma: ${karmaResult.reason}`, {
          position: "top-right",
          duration: 3000,
        });
      }

      // Log document summary to Supabase
      try {
        const effectiveUserId = userId || "guest-user";
        await chatLogsService.logDocumentSummary({
          userId: effectiveUserId,
          fileName: file.name,
          fileType: file.type,
          fileSize: file.size,
          model: selectedModel,
          hasAudio: summaryResponse.audio_file ? true : false,
        });
        // Document summary logged successfully
      } catch (logError) {
        // Continue even if logging fails
      }

      // Navigate to summary page
      navigate("/learn/summary");
    } catch (err) {
      const errorMsg = err.message || "Failed to process file";
      setError(errorMsg);
      toast.error(errorMsg, {
        position: "bottom-right",
        duration: 5000,
      });
    } finally {
      setLoading(false);
    }
  };

  // Streaming analysis function
  const handleStreamingAnalysis = async () => {
    if (!file) return;

    try {
      setIsStreaming(true);
      setShowStreamingView(true);
      setStreamingContent("");
      setError("");

      const isImage = file.type.startsWith("image/");

      // Validate file before upload
      if (file.size > 10 * 1024 * 1024) {
        throw new Error("File size exceeds 10MB limit. Please upload a smaller file.");
      }

      // Check backend connectivity first
      console.log("🔍 Checking backend connectivity:", CHAT_API_BASE_URL);
      try {
        const healthCheck = await fetch(`${CHAT_API_BASE_URL}/health`, {
          method: 'GET',
          signal: AbortSignal.timeout(5000) // 5 second timeout
        }).catch(() => null);
        
        if (!healthCheck || !healthCheck.ok) {
          console.warn("⚠️ Backend health check failed, but continuing...");
        } else {
          console.log("✅ Backend is reachable");
        }
      } catch (healthError) {
        console.warn("⚠️ Could not verify backend health:", healthError);
        // Continue anyway - the upload will fail with a better error if backend is down
      }

      // Upload file first with Grok model
      toast.loading("Uploading file to Grok...", {
        id: "upload-progress",
        position: "bottom-right",
      });

      console.log("📤 Uploading file for analysis:", {
        fileName: file.name,
        fileType: file.type,
        fileSize: file.size,
        fileSizeMB: (file.size / (1024 * 1024)).toFixed(2),
        isImage: isImage,
        llm: "grok",
        backendUrl: CHAT_API_BASE_URL
      });

      try {
        // Get current language (map i18n language to backend format)
        // Handle Arabic language codes: "ar", "ar-SA", "ar-EG", etc.
        const currentLanguage = i18n.language && i18n.language.toLowerCase().startsWith("ar") ? "arabic" : "english";
        console.log("🌐 Language detection (streaming):", { i18nLanguage: i18n.language, currentLanguage });
        
        // Use direct fetch to ensure query parameter is sent correctly
        // FastAPI endpoint: process_pdf(file: UploadFile = File(...), llm: str = "grok", language: str = "english")
        // Since llm and language are not Form(), FastAPI reads them from query string
        
        const uploadEndpoint = isImage ? "/process-img" : "/process-pdf";
        const uploadUrl = `${CHAT_API_BASE_URL}${uploadEndpoint}?llm=grok&language=${encodeURIComponent(currentLanguage)}`;
        
        console.log("📤 Direct upload attempt:", {
          endpoint: uploadUrl,
          fileName: file.name,
          fileSize: file.size,
          fileType: file.type,
          language: currentLanguage
        });
        
        const formData = new FormData();
        formData.append("file", file);
        // Also append llm and language as FormData - FastAPI might read them from FormData even if not marked as Form()
        formData.append("llm", "grok");
        formData.append("language", currentLanguage);
        
        let uploadResponse;
        let usedLLM = "grok";
        
        try {
          // Try direct fetch with grok - using both query parameter AND FormData
          // FastAPI endpoint: process_pdf(file: UploadFile = File(...), llm: str = "grok")
          // Since llm is not marked with Query() or Form(), FastAPI tries query params first,
          // but with File uploads, it might read from FormData too
          uploadResponse = await fetch(uploadUrl, {
            method: "POST",
            body: formData,
            // Don't set Content-Type - browser will set it with boundary for FormData
            credentials: 'include', // Include cookies if needed
          });
          
          console.log("📥 Upload response:", {
            status: uploadResponse.status,
            statusText: uploadResponse.statusText,
            ok: uploadResponse.ok,
            headers: Object.fromEntries(uploadResponse.headers.entries())
          });
          
          if (!uploadResponse.ok) {
            let errorText;
            try {
              const errorJson = await uploadResponse.json();
              errorText = errorJson.detail || errorJson.error || JSON.stringify(errorJson);
            } catch {
              errorText = await uploadResponse.text().catch(() => `HTTP ${uploadResponse.status}: ${uploadResponse.statusText}`);
            }
            
            console.error("❌ Upload failed:", {
              status: uploadResponse.status,
              errorText: errorText.substring(0, 500)
            });
            
            // Backend now handles automatic fallback (grok -> llama -> chatgpt)
            // If we get here, the backend tried all models and failed
            if (errorText.includes("GROQ_API_KEY") || errorText.includes("API key") || errorText.includes("not set")) {
              throw new Error(`API Key Missing: Please set GROQ_API_KEY environment variable in your backend.`);
            } else if (errorText.includes("Rate limit") || errorText.includes("429")) {
              throw new Error(`Rate limit exceeded. Please wait a moment and try again.`);
            } else if (errorText.includes("Invalid GROQ_API_KEY") || errorText.includes("401")) {
              throw new Error(`Invalid API Key: Please check your GROQ_API_KEY is correct.`);
            } else if (errorText.includes("All LLM models failed")) {
              throw new Error(`All AI models failed. Please check:\n1. GROQ_API_KEY is set correctly\n2. API key has sufficient credits\n3. Network connection is stable`);
            } else {
              // Generic error - backend should have tried fallback automatically
              throw new Error(`Upload failed: ${errorText}`);
            }
          }
          
          // Parse response if it's JSON
          const contentType = uploadResponse.headers.get("content-type");
          if (contentType && contentType.includes("application/json")) {
            const uploadResult = await uploadResponse.json();
            console.log("✅ File uploaded successfully:", uploadResult);
          } else {
            console.log("✅ File uploaded successfully (status:", uploadResponse.status + ")");
          }
          
          // Upload successful, continue with streaming
          
        } catch (directFetchError) {
          console.error("❌ Direct fetch upload failed:", directFetchError);
          
          // Get current language (map i18n language to backend format)
          // Handle Arabic language codes: "ar", "ar-SA", "ar-EG", etc.
          const currentLanguage = i18n.language && i18n.language.toLowerCase().startsWith("ar") ? "arabic" : "english";
          console.log("🌐 Language detection (fallback):", { i18nLanguage: i18n.language, currentLanguage });
          
          // Fallback to RTK Query with llama
          usedLLM = "llama";
          console.log("🔄 Falling back to RTK Query with Llama model...");
          
          if (isImage) {
            uploadResult = await uploadImageForSummary({ file, llm: "llama", language: currentLanguage }).unwrap();
          } else {
            uploadResult = await uploadPdfForSummary({ file, llm: "llama", language: currentLanguage }).unwrap();
          }
          
          console.log("✅ RTK Query upload successful with Llama:", uploadResult);
          
          toast("⚠️ Using Llama model (fallback)", {
            icon: "ℹ️",
            position: "bottom-right",
            duration: 3000,
          });
        }
      } catch (uploadError) {
        console.error("❌ File upload failed:", uploadError);
        console.error("❌ Upload error details:", {
          status: uploadError?.status,
          data: uploadError?.data,
          error: uploadError?.error,
          message: uploadError?.message,
          originalStatus: uploadError?.originalStatus,
          originalStatusText: uploadError?.originalStatusText
        });
        
        // Extract error message from RTK Query error structure
        let errorMessage = "Unknown error";
        let errorDetails = {};
        
        if (uploadError?.data) {
          // Backend returned error response
          errorDetails.backendResponse = uploadError.data;
          
          if (typeof uploadError.data === 'string') {
            errorMessage = uploadError.data;
          } else if (uploadError.data?.detail) {
            errorMessage = uploadError.data.detail;
          } else if (uploadError.data?.error) {
            errorMessage = uploadError.data.error;
          } else if (uploadError.data?.message) {
            errorMessage = uploadError.data.message;
          } else {
            errorMessage = JSON.stringify(uploadError.data);
          }
        } else if (uploadError?.error) {
          errorMessage = uploadError.error;
        } else if (uploadError?.message) {
          errorMessage = uploadError.message;
        }
        
        // Check for specific RTK Query error types
        if (uploadError?.status) {
          errorDetails.status = uploadError.status;
          
          if (uploadError.status === 'FETCH_ERROR') {
            errorMessage = `Network error: Could not connect to backend server at ${CHAT_API_BASE_URL}. Please ensure:
1. The backend is running on port 8001
2. CORS is properly configured
3. The server is accessible`;
          } else if (uploadError.status === 'PARSING_ERROR') {
            errorMessage = `Server response parsing error: ${errorMessage}. The server may have returned invalid data.`;
          } else if (uploadError.status === 'TIMEOUT_ERROR') {
            errorMessage = `Upload timeout after 120 seconds. The file (${(file.size / (1024 * 1024)).toFixed(2)} MB) may be too large or the server is taking too long to respond.`;
          } else if (typeof uploadError.status === 'number') {
            const statusCode = uploadError.status;
            if (statusCode === 400) {
              errorMessage = `Bad Request (400): ${errorMessage || 'Invalid file format or parameters'}`;
            } else if (statusCode === 413) {
              errorMessage = `File too large (413): The file exceeds the server's size limit`;
            } else if (statusCode === 415) {
              errorMessage = `Unsupported Media Type (415): The file type is not supported`;
            } else if (statusCode === 500) {
              errorMessage = `Server Error (500): ${errorMessage || 'Internal server error occurred'}`;
            } else if (statusCode === 503) {
              errorMessage = `Service Unavailable (503): The backend service is temporarily unavailable`;
            } else {
              errorMessage = `HTTP error ${statusCode}: ${uploadError.originalStatusText || errorMessage || 'Server error'}`;
            }
          }
        }
        
        console.error("❌ Full error details:", {
          error: uploadError,
          errorMessage,
          errorDetails,
          fileInfo: {
            name: file.name,
            size: file.size,
            type: file.type
          }
        });
        
        throw new Error(`Failed to upload file: ${errorMessage}`);
      }

      toast.dismiss("upload-progress");

      // Show analyzing toast
      toast.loading("Analyzing document with UniGuru AI...", {
        id: "analyzing-progress",
        position: "bottom-right",
      });

      // Start streaming analysis using local backend
      const streamEndpoint = isImage ? "/process-img-stream" : "/process-pdf-stream";
      const currentLanguage =
        i18n.language && i18n.language.toLowerCase().startsWith("ar")
          ? "arabic"
          : "english";
      const streamUrl = `${CHAT_API_BASE_URL}${streamEndpoint}?llm=grok&language=${encodeURIComponent(
        currentLanguage
      )}`;

      console.log(`🌊 Starting streaming ${isImage ? 'image' : 'document'} analysis:`, streamUrl);

      // Create abort controller for canceling the stream
      const controller = new AbortController();
      streamingControllerRef.current = controller;

      const response = await fetch(streamUrl, { 
        signal: controller.signal,
        headers: {
          'Accept': 'text/event-stream',
        }
      });

      if (!response.ok) {
        const errorText = await response.text().catch(() => 'Unknown error');
        console.error("❌ Streaming response error:", {
          status: response.status,
          statusText: response.statusText,
          errorText: errorText.substring(0, 500)
        });
        throw new Error(`HTTP error! status: ${response.status} - ${errorText.substring(0, 200)}`);
      }

      console.log("✅ Streaming connection established");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let accumulatedContent = "";
      let hasReceivedContent = false;

      // Process the stream
      while (true) {
        const { done, value } = await reader.read();

        if (done) {
          console.log("🏁 Streaming complete");
          if (!hasReceivedContent && accumulatedContent.trim() === "") {
            throw new Error("No content received from streaming endpoint. The document may not have been processed correctly.");
          }
          break;
        }

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.trim()) {
            if (line.includes('[END]')) {
              console.log("✅ Stream ended successfully");
              break;
            } else if (line.includes('[ERROR]')) {
              const errorMsg = line.replace('[ERROR]', '').trim() || "Streaming error occurred";
              throw new Error(errorMsg);
            } else if (line.startsWith('data: ')) {
              const content = line.substring(6).trim();

              // Filter out only obvious status messages, but be more lenient with content
              const isObviousStatusMessage = 
                (content.includes('🔍 Starting') && content.length < 50) || 
                (content.includes('📄 Processing') && content.length < 50) ||
                (content.includes('🤖 Using') && content.length < 50) ||
                (content.includes('📝 Generating') && content.length < 50) ||
                (content === '✅' || content === '✅ Image analysis complete!' || content === '✅ Document analysis complete!') ||
                (content.includes('🎵 Audio') && content.length < 50) ||
                content === '[END]' || 
                content === '[ERROR]' ||
                (content.includes('Starting document') && content.length < 50) || 
                (content.includes('Processing:') && content.length < 50) ||
                (content.includes('Using GROK') && content.length < 50) ||
                (content.includes('Using UNIGURU') && content.length < 50) ||
                (content === 'Document analysis complete!') ||
                (content === 'Audio summary available for download') ||
                (content === 'Image analysis complete!');

              // Add content if it's not an obvious status message
              // Be more lenient - include content that might be part of the analysis
              if (!isObviousStatusMessage && content.trim()) {
                // Check for Arabic characters
                const hasArabic = /[\u0600-\u06FF]/.test(content);
                // Check if it looks like actual analysis content
                const looksLikeContent = 
                  content.length > 20 || // Longer content is likely analysis
                  content.includes('.') || // Contains sentences
                  content.includes('The') || // Starts with common words
                  content.includes('This') ||
                  content.includes('It') ||
                  content.match(/^[A-Z]/); // Starts with capital letter (likely a sentence)

                // If Arabic UI selected, suppress short non-Arabic lines (often status/intro)
                const suppressNonArabic =
                  currentLanguage === "arabic" &&
                  !hasArabic &&
                  content.length < 150;

                if (!suppressNonArabic && (looksLikeContent || content.length > 15 || hasArabic)) {
                  accumulatedContent += content + '\n';
                  hasReceivedContent = true;
                  setStreamingContent(accumulatedContent);
                }
              }
            } else if (line.trim() && !line.startsWith('data: ')) {
              // Handle lines that don't start with 'data: ' but might contain content
              const trimmedLine = line.trim();
              if (trimmedLine.length > 10 && 
                  !trimmedLine.includes('[END]') && 
                  !trimmedLine.includes('[ERROR]')) {
                accumulatedContent += trimmedLine + '\n';
                hasReceivedContent = true;
                setStreamingContent(accumulatedContent);
              }
            }
          }
        }
      }

      // Dismiss analyzing toast
      toast.dismiss("analyzing-progress");

      if (!hasReceivedContent || accumulatedContent.trim() === "") {
        throw new Error("No analysis content was generated. Please try uploading the file again.");
      }

      // Save the final content to localStorage for potential navigation
      const finalSummaryData = {
        answer: accumulatedContent,
        title: isImage ? "Image Analysis" : "Document Summary",
        llm: "grok",
        audio_file: null, // Will be handled separately
      };

      localStorage.setItem("summaryData", JSON.stringify(finalSummaryData));
      localStorage.setItem("fileData", JSON.stringify({
        type: file.type,
        name: file.name,
      }));

      toast.success("Document analysis complete!", {
        icon: "🎉",
        position: "bottom-right",
        duration: 3000,
      });

      // Process karma for using summarizer
      const effectiveUserId = userId || "guest-user";
      const karmaResult = processSummarizerUsage(effectiveUserId);
      if (karmaResult) {
        dispatchKarmaChange(karmaResult);
        toast.success(`+${karmaResult.change} Karma: ${karmaResult.reason}`, {
          position: "top-right",
          duration: 3000,
        });
      }

      // Trigger TTS auto-play for the generated content
      if (ttsServiceHealthy && accumulatedContent.trim()) {
        console.log("🔊 Document Summarizer: Triggering TTS auto-play");

        // Clean the content for better speech
        const cleanContent = accumulatedContent
          .replace(/\*\*(.*?)\*\*/g, '$1') // Remove bold markdown
          .replace(/\*(.*?)\*/g, '$1') // Remove italic markdown
          .replace(/`(.*?)`/g, '$1') // Remove code markdown
          .replace(/#{1,6}\s/g, '') // Remove headers
          .replace(/\n+/g, '. ') // Replace newlines with periods
          .replace(/\s+/g, ' ') // Normalize whitespace
          .trim();

        // Auto-play with a delay for better UX
        setTimeout(() => {
          autoPlayAI(cleanContent, {
            delay: 1000,
            volume: 0.8
          }).catch(error => {
            console.warn("🔊 Document Summarizer: TTS auto-play failed:", error.message);
          });
        }, 1500);
      }

    } catch (err) {
      // Dismiss any loading toasts
      toast.dismiss("upload-progress");
      toast.dismiss("analyzing-progress");
      
      if (err.name === "AbortError") {
        // Stream was canceled by user
        toast("Analysis canceled", {
          icon: "🛑",
          position: "bottom-right",
        });
      } else {
        const errorMsg = err.message || err.data?.error || "Failed to stream document analysis";
        console.error("❌ Streaming analysis error:", {
          error: err,
          message: errorMsg,
          stack: err.stack
        });
        setError(errorMsg);
        toast.error(`Analysis failed: ${errorMsg}`, {
          position: "bottom-right",
          duration: 8000,
        });
      }
    } finally {
      setIsStreaming(false);
      streamingControllerRef.current = null;
    }
  };

  return (
    <GlassContainer>
      <div className="w-[95%] mx-auto px-4">
        {/* Header Section */}
        <div className="text-center mb-12">
          <h2
            className="text-5xl md:text-6xl font-extrabold mb-6 drop-shadow-lg transition-all duration-300 hover:bg-gradient-to-r hover:from-white hover:to-[#FF9933] hover:bg-clip-text hover:text-transparent"
            style={{
              color: "#FFFFFF",
              fontFamily: "Nunito, sans-serif",
            }}
          >
            {t("Smart Document Analysis")}
          </h2>
          <p className="text-white/80 text-xl mb-3">
            {t("Upload your documents for instant AI-powered summaries")}
          </p>
          <p className="text-white/60 text-sm">
            {t("Supported formats: PDF, DOC, DOCX, JPG, PNG • Max size: 10MB")}
          </p>

          {/* AI Model Display - Using Grok */}
          <div className="mt-4 flex items-center justify-center">
            <div className="relative group">
              <div className="absolute -top-8 left-0 bg-black/80 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none">
                {t("Powered by Grok AI Model")}
              </div>
              <label className="text-white/80 mr-3">{t("AI Model")}:</label>
              <div
                className="bg-gradient-to-r from-[#FF9933]/30 to-[#FF9933]/10 text-white border-2 border-[#FF9933]/30 rounded-lg px-3 py-2 text-sm font-medium"
                style={{
                  backdropFilter: "blur(10px)",
                  boxShadow: "0 2px 10px rgba(255, 153, 51, 0.2)",
                  textShadow: "0 1px 2px rgba(0, 0, 0, 0.3)",
                  minWidth: "110px",
                  textAlign: "center",
                }}
              >
                Grok
              </div>
            </div>
          </div>
        </div>

        {/* Main Content Area */}
        {showStreamingView ? (
          <div className="mt-6">
            <style>{`
              .summary-content::-webkit-scrollbar {
                width: 10px;
              }
              .summary-content::-webkit-scrollbar-track {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                margin: 4px 0;
              }
              .summary-content::-webkit-scrollbar-thumb {
                background: rgba(255, 153, 51, 0.6);
                border-radius: 10px;
                border: 2px solid rgba(0, 0, 0, 0.2);
              }
              .summary-content::-webkit-scrollbar-thumb:hover {
                background: rgba(255, 153, 51, 0.8);
              }
              /* Firefox scrollbar */
              .summary-content {
                scrollbar-width: thin;
                scrollbar-color: rgba(255, 153, 51, 0.6) rgba(255, 255, 255, 0.1);
              }
            `}</style>
            <div className="relative rounded-2xl bg-white/5 backdrop-blur-xl border border-white/10 shadow-2xl ring-1 ring-white/5 p-4 md:p-6 overflow-hidden">
              {/* Close (X) button to go back */}
              <button
                onClick={() => {
                  if (streamingControllerRef.current) {
                    streamingControllerRef.current.abort();
                  }
                  setIsStreaming(false);
                  setShowStreamingView(false);
                  setStreamingContent("");
                }}
                className="absolute top-3 right-3 p-2 bg-white/10 hover:bg-white/20 rounded-full transition-all duration-200 border border-white/20 backdrop-blur-sm"
                title={t("Close analysis")}
              >
                <FiX className="w-4 h-4 text-white" />
              </button>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 h-[65vh] md:h-[70vh]">
                {/* Preview Panel */}
                <div className="bg-black/20 p-3 md:p-4 rounded-xl border border-white/10 flex flex-col h-full">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-white font-semibold flex items-center gap-2"><FiFileText className="w-4 h-4 text-white/80" /> {t("Preview")}</h3>
                    {file && (
                      <span className="text-white/60 text-xs truncate max-w-[200px]">{file.name}</span>
                    )}
                  </div>
                  <div className="mt-2 rounded-xl overflow-hidden border border-white/5 bg-black/30 flex-1">
                    {file?.type?.includes("pdf") && previewUrl ? (
                      <object data={previewUrl} type="application/pdf" className="w-full h-full">
                        <div className="p-4 text-white/70 text-sm">{t("PDF preview not supported. You can download and open the file locally.")}</div>
                      </object>
                    ) : file?.type?.startsWith("image/") && previewUrl ? (
                      <img src={previewUrl} alt={file?.name || 'preview'} className="w-full h-full object-contain bg-black/30" />
                    ) : file ? (
                      <div className="p-6 text-white/70 text-sm">
                        {t("No inline preview available for this file type.")}
                        <div className="mt-2 text-white/50">{file.name}</div>
                      </div>
                    ) : (
                      <div className="p-6 text-white/60">{t("No file selected")}</div>
                    )}
                  </div>
                </div>

                {/* Live Analysis Panel */}
                <div className="bg-black/20 p-3 md:p-4 rounded-xl border border-white/10 flex flex-col h-full overflow-hidden">
                  <div className="flex items-center justify-between mb-3 flex-shrink-0">
                    <h3 className="text-white font-semibold">{t("Live Document Analysis")}</h3>
                    <div className="flex items-center gap-2">
                      <span className="bg-[#FF9933]/20 px-2 py-0.5 rounded text-xs font-bold text-white/90">Grok</span>
                      {isStreaming && (
                        <div className="flex items-center gap-1">
                          <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                          <span className="text-green-400 text-xs">{t("Analyzing...")}</span>
                        </div>
                      )}
                      {!isStreaming && streamingContent && ttsServiceHealthy && (
                        <div className="flex items-center gap-1">
                          <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse"></div>
                          <span className="text-blue-400 text-xs">🔊 {t("Audio Ready")}</span>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="bg-black/20 p-4 rounded-xl border border-white/5 flex-1 overflow-y-scroll overflow-x-hidden summary-content" style={{ minHeight: 0, maxHeight: '100%' }}>
                    {streamingContent ? (
                      <div className="text-white/90 leading-relaxed">
                        {streamingContent.split('\n\n').filter(p => p.trim()).map((paragraph, index) => (
                          <div
                            key={index}
                            className="mb-6 last:mb-0 group"
                          >
                            <p className="summary-paragraph text-white/95 leading-relaxed text-base md:text-lg font-normal text-justify bg-gradient-to-r from-white/5 via-white/3 to-transparent rounded-lg p-4 md:p-5 hover:bg-white/10 hover:shadow-lg hover:shadow-[#FF9933]/10 transition-all duration-300 border-l-2 border-[#FF9933]/30 hover:border-[#FF9933]/60 backdrop-blur-sm">
                              {paragraph.trim().split('\n').join(' ')}
                            </p>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="flex items-center justify-center h-full">
                        <div className="text-center">
                          <div className="w-8 h-8 border-2 border-[#FF9933]/30 border-t-[#FF9933] rounded-full animate-spin mx-auto mb-4"></div>
                          <p className="text-white/60">Preparing document analysis...</p>
                        </div>
                      </div>
                    )}
                  </div>

                  {!isStreaming && streamingContent && (
                    <div className="mt-4 flex justify-end gap-3">
                      <button
                        onClick={() => navigate('/learn/summary')}
                        className="px-5 py-2 bg-[#FF9933]/20 hover:bg-[#FF9933]/30 text-white rounded-lg transition-all duration-200"
                      >
                        View Full Summary
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center space-y-6 mt-6">
            {/* Upload Box */}
            <div
              className="w-72 h-72 border-2 border-dashed border-white/30 rounded-2xl flex flex-col items-center justify-center p-8 bg-white/5 hover:bg-white/10 transition-all duration-300 cursor-pointer group relative overflow-hidden"
              onClick={() => fileInputRef.current.click()}
            >
              <input
                type="file"
                onChange={handleFileChange}
                ref={fileInputRef}
                className="hidden"
                accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
              />

              <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>

              {!file ? (
                <>
                  <FiFileText className="text-white/70 w-20 h-20 mb-6 group-hover:text-[#FF9933] transition-colors duration-300" />
                  <div className="text-center relative z-10">
                    <p className="text-white text-lg font-medium mb-2">
                      {t("Drop your file here")}
                    </p>
                    <p className="text-white/60">{t("or click to browse")}</p>
                  </div>
                </>
              ) : (
                <div className="text-center relative z-10">
                  <FiFileText className="text-[#FF9933] w-16 h-16 mx-auto mb-4" />
                  <p className="text-white/90 font-medium mb-2 break-all">
                    {file.name}
                  </p>
                  <p className="text-white/60">
                    {(file.size / (1024 * 1024)).toFixed(2)} MB
                  </p>
                </div>
              )}
            </div>

            {/* Analysis Button */}
            <button
              onClick={handleStreamingAnalysis}
              disabled={!file || isStreaming}
              className={`w-72 px-8 py-4 rounded-xl transition-all duration-300 flex items-center justify-center space-x-3 ${
                !file || isStreaming
                  ? "bg-gray-500/50 cursor-not-allowed"
                  : "bg-[#FF9933]/20 hover:bg-[#FF9933]/30 hover:scale-105 active:scale-95"
              }`}
            >
              {isStreaming ? (
                <div className="w-6 h-6 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
              ) : (
                <FiUpload className="text-white w-5 h-5" />
              )}
              <span className="text-white text-lg">
                {isStreaming ? t("Analyzing...") : t("Analysis")}
              </span>
            </button>

            {/* Error Display */}
            {error && (
              <div className="text-red-400 text-center bg-red-500/10 p-4 rounded-xl border border-red-500/20 backdrop-blur-sm">
                {error}
              </div>
            )}
          </div>
        )}
      </div>
    </GlassContainer>
  );
}
