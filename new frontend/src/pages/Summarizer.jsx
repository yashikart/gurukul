import React, { useState, useRef, useEffect } from "react";
import GlassContainer from "../components/GlassContainer";
import { FiUpload, FiFileText, FiX } from "react-icons/fi";
import { useNavigate } from "react-router-dom";
import { toast } from "react-hot-toast";
import { useTranslation } from "react-i18next";
import { useUser } from "@clerk/clerk-react";
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

export default function Summarizer() {
  const { t } = useTranslation();
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const [showStreamingView, setShowStreamingView] = useState(false);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [selectedModel, setSelectedModel] = useState("uniguru"); // Fixed to UniGuru model
  const [userId, setUserId] = useState(null);
  const { isSignedIn, user } = useUser();
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
      if (isImage) {
        const response = await getImageSummary().unwrap();
        return response;
      } else {
        const response = await getPdfSummary().unwrap();
        return response;
      }
    } catch (error) {
      throw new Error("Failed to fetch summary");
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

      // Upload file using RTK Query with UniGuru model
      if (isImage) {
        await uploadImageForSummary({
          file,
          llm: "uniguru",
        }).unwrap();
      } else {
        await uploadPdfForSummary({
          file,
          llm: "uniguru",
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

      // Upload file first
      toast.loading("Uploading file to UniGuru...", {
        id: "upload-progress",
        position: "bottom-right",
      });

      if (isImage) {
        await uploadImageForSummary({ file }).unwrap();
      } else {
        await uploadPdfForSummary({ file }).unwrap();
      }

      toast.dismiss("upload-progress");

      // Start streaming analysis using local backend
      const streamEndpoint = isImage ? "/process-img-stream" : "/process-pdf-stream";
      const streamUrl = `${CHAT_API_BASE_URL}${streamEndpoint}?llm=uniguru`;

      console.log(`🌊 Starting streaming ${isImage ? 'image' : 'document'} analysis:`, streamUrl);

      // Create abort controller for canceling the stream
      const controller = new AbortController();
      streamingControllerRef.current = controller;

      const response = await fetch(streamUrl, { signal: controller.signal });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let accumulatedContent = "";

      // Process the stream
      while (true) {
        const { done, value } = await reader.read();

        if (done) {
          console.log("🏁 Streaming complete");
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
              throw new Error("Streaming error occurred");
            } else if (line.startsWith('data: ')) {
              const content = line.substring(6);

              // Filter out status messages and only accumulate actual content
              const isStatusMessage = content.includes('🔍') || content.includes('📄') ||
                                    content.includes('🤖') || content.includes('📝') ||
                                    content.includes('✅') || content.includes('🎵') ||
                                    content.includes('[END]') || content.includes('[ERROR]') ||
                                    content.includes('Starting document') || content.includes('Processing:') ||
                                    content.includes('Using UNIGURU') || content.includes('Generating comprehensive') ||
                                    content.includes('Document analysis complete') || content.includes('Audio summary available');

              // Add actual content, not status messages
              if (!isStatusMessage && content.trim()) {
                accumulatedContent += content + '\n';
                setStreamingContent(accumulatedContent);
              }
            }
          }
        }
      }

      // Save the final content to localStorage for potential navigation
      const finalSummaryData = {
        answer: accumulatedContent,
        title: isImage ? "Image Analysis" : "Document Summary",
        llm: "uniguru",
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
      if (err.name === "AbortError") {
        // Stream was canceled by user
        toast("Analysis canceled", {
          icon: "🛑",
          position: "bottom-right",
        });
      } else {
        const errorMsg = err.message || "Failed to stream document analysis";
        setError(errorMsg);
        toast.error(errorMsg, {
          position: "bottom-right",
          duration: 5000,
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
            Smart Document Analysis
          </h2>
          <p className="text-white/80 text-xl mb-3">
            Upload your documents for instant AI-powered summaries
          </p>
          <p className="text-white/60 text-sm">
            Supported formats: PDF, DOC, DOCX, JPG, PNG • Max size: 10MB
          </p>

          {/* AI Model Display - Fixed to UniGuru */}
          <div className="mt-4 flex items-center justify-center">
            <div className="relative group">
              <div className="absolute -top-8 left-0 bg-black/80 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none">
                {t("Powered by UniGuru AI Model")}
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
                UniGuru
              </div>
            </div>
          </div>
        </div>

        {/* Main Content Area */}
        {showStreamingView ? (
          <div className="mt-6">
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
                title="Close analysis"
              >
                <FiX className="w-4 h-4 text-white" />
              </button>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 h-[65vh] md:h-[70vh]">
                {/* Preview Panel */}
                <div className="bg-black/20 p-3 md:p-4 rounded-xl border border-white/10 flex flex-col h-full">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-white font-semibold flex items-center gap-2"><FiFileText className="w-4 h-4 text-white/80" /> Preview</h3>
                    {file && (
                      <span className="text-white/60 text-xs truncate max-w-[200px]">{file.name}</span>
                    )}
                  </div>
                  <div className="mt-2 rounded-xl overflow-hidden border border-white/5 bg-black/30 flex-1">
                    {file?.type?.includes("pdf") && previewUrl ? (
                      <object data={previewUrl} type="application/pdf" className="w-full h-full">
                        <div className="p-4 text-white/70 text-sm">PDF preview not supported. You can download and open the file locally.</div>
                      </object>
                    ) : file?.type?.startsWith("image/") && previewUrl ? (
                      <img src={previewUrl} alt={file?.name || 'preview'} className="w-full h-full object-contain bg-black/30" />
                    ) : file ? (
                      <div className="p-6 text-white/70 text-sm">
                        No inline preview available for this file type.
                        <div className="mt-2 text-white/50">{file.name}</div>
                      </div>
                    ) : (
                      <div className="p-6 text-white/60">No file selected</div>
                    )}
                  </div>
                </div>

                {/* Live Analysis Panel */}
                <div className="bg-black/20 p-3 md:p-4 rounded-xl border border-white/10 flex flex-col h-full">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-white font-semibold">Live Document Analysis</h3>
                    <div className="flex items-center gap-2">
                      <span className="bg-[#FF9933]/20 px-2 py-0.5 rounded text-xs font-bold text-white/90">UniGuru</span>
                      {isStreaming && (
                        <div className="flex items-center gap-1">
                          <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                          <span className="text-green-400 text-xs">Analyzing...</span>
                        </div>
                      )}
                      {!isStreaming && streamingContent && ttsServiceHealthy && (
                        <div className="flex items-center gap-1">
                          <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse"></div>
                          <span className="text-blue-400 text-xs">🔊 Audio Ready</span>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="bg-black/20 p-4 rounded-xl border border-white/5 flex-1 overflow-auto">
                    {streamingContent ? (
                      <div className="text-white/90 whitespace-pre-wrap leading-relaxed">
                        {streamingContent.split('\n').map((line, index) => (
                          <div key={index} className="mb-2">
                            {line.trim() && (
                              <div className="flex items-start">
                                <span className="text-[#FF9933] mr-2 mt-1.5">•</span>
                                <span>{line}</span>
                              </div>
                            )}
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
                      Drop your file here
                    </p>
                    <p className="text-white/60">or click to browse</p>
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
                {isStreaming ? "Analyzing..." : "Analysis"}
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
