import React, { useEffect, useState, useRef } from "react";
import {
  FiDownload,
  FiX,
  FiPlay,
  FiPause,
  FiVolume2,
  FiVolumeX,
} from "react-icons/fi";
import { useNavigate } from "react-router-dom";
import GlassContainer from "../components/GlassContainer";
import { CHAT_API_BASE_URL } from "../config";
import toast from "react-hot-toast";

// Custom styled audio player component
const CustomAudioPlayer = ({ audioSrc, autoPlay = true, onAutoPlayAttempted }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [duration, setDuration] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);
  const [isMuted, setIsMuted] = useState(false);
  const [volume, setVolume] = useState(1);
  const [audioError, setAudioError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [hasAutoPlayed, setHasAutoPlayed] = useState(false);
  const audioRef = useRef(null);
  const progressBarRef = useRef(null);

  useEffect(() => {
    // Get audio duration when metadata is loaded
    const audio = audioRef.current;
    if (!audio || !audioSrc) return;

    const setAudioData = () => {
      console.log("🎵 Audio metadata loaded, duration:", audio.duration);
      setDuration(audio.duration);
      setIsLoading(false);
      setAudioError(null);

      // Auto-play when audio is ready and hasn't been played yet
      if (autoPlay && !hasAutoPlayed) {
        console.log("🎵 Triggering auto-play from metadata loaded");
        setTimeout(() => tryAutoPlay(), 100); // Small delay to ensure audio is fully ready
      }
    };

    const updateTime = () => {
      setCurrentTime(audio.currentTime);
    };

    const handleError = (e) => {
      console.error("Audio loading error:", e, "URL:", audioSrc);
      setAudioError(`Failed to load audio file: ${audioSrc}`);
      setIsLoading(false);
    };

    const handleLoadStart = () => {
      console.log("Audio loading started:", audioSrc);
      setIsLoading(true);
      setAudioError(null);
      setHasAutoPlayed(false); // Reset auto-play flag for new audio
    };

    const handleCanPlay = () => {
      console.log("🎵 Audio can play:", audioSrc);
      // Try auto-play when audio can play
      if (autoPlay && !hasAutoPlayed) {
        console.log("🎵 Triggering auto-play from canplay event");
        setTimeout(() => tryAutoPlay(), 50); // Small delay for browser compatibility
      }
    };

    const tryAutoPlay = async () => {
      if (hasAutoPlayed) return;

      try {
        console.log("🎵 Attempting auto-play for:", audioSrc);
        console.log("🎵 Audio ready state:", audio.readyState);
        console.log("🎵 Audio paused:", audio.paused);

        // Ensure audio is ready
        if (audio.readyState < 3) {
          console.log("🎵 Audio not ready yet, waiting...");
          return;
        }

        const playPromise = audio.play();

        if (playPromise !== undefined) {
          await playPromise;
          setIsPlaying(true);
          setHasAutoPlayed(true);
          console.log("✅ Auto-play successful!");

          // Notify parent component that auto-play was attempted
          if (onAutoPlayAttempted) {
            onAutoPlayAttempted(true);
          }
        }
      } catch (error) {
        console.warn("⚠️ Auto-play blocked by browser:", error.message);
        console.warn("⚠️ Error details:", error);

        // Try to enable auto-play on next user interaction
        const enableAutoPlayOnInteraction = () => {
          console.log("🎵 User interacted, trying auto-play again...");
          audio.play()
            .then(() => {
              setIsPlaying(true);
              setHasAutoPlayed(true);
              console.log("✅ Auto-play successful after user interaction!");
              if (onAutoPlayAttempted) {
                onAutoPlayAttempted(true);
              }
              // Remove event listeners after successful play
              document.removeEventListener('click', enableAutoPlayOnInteraction);
              document.removeEventListener('keydown', enableAutoPlayOnInteraction);
            })
            .catch(err => console.warn("⚠️ Auto-play still failed:", err));
        };

        // Add event listeners for user interaction
        document.addEventListener('click', enableAutoPlayOnInteraction, { once: true });
        document.addEventListener('keydown', enableAutoPlayOnInteraction, { once: true });

        // Notify parent component that auto-play was attempted (but failed)
        if (onAutoPlayAttempted) {
          onAutoPlayAttempted(false);
        }
      }
    };

    // Reset states when audio source changes
    setIsLoading(true);
    setAudioError(null);
    setCurrentTime(0);
    setDuration(0);

    // Add event listeners
    audio.addEventListener("loadedmetadata", setAudioData);
    audio.addEventListener("timeupdate", updateTime);
    audio.addEventListener("error", handleError);
    audio.addEventListener("loadstart", handleLoadStart);
    audio.addEventListener("canplay", handleCanPlay);

    // Fallback: Try auto-play after a short delay if enabled
    if (autoPlay && !hasAutoPlayed) {
      const fallbackTimer = setTimeout(() => {
        console.log("🎵 Fallback auto-play attempt");
        tryAutoPlay();
      }, 1000); // Try after 1 second

      // Cleanup timer
      return () => {
        clearTimeout(fallbackTimer);
        audio.removeEventListener("loadedmetadata", setAudioData);
        audio.removeEventListener("timeupdate", updateTime);
        audio.removeEventListener("error", handleError);
        audio.removeEventListener("loadstart", handleLoadStart);
        audio.removeEventListener("canplay", handleCanPlay);
      };
    }

    // Cleanup
    return () => {
      audio.removeEventListener("loadedmetadata", setAudioData);
      audio.removeEventListener("timeupdate", updateTime);
      audio.removeEventListener("error", handleError);
      audio.removeEventListener("loadstart", handleLoadStart);
      audio.removeEventListener("canplay", handleCanPlay);
    };
  }, [audioSrc, autoPlay, hasAutoPlayed]);

  // Format time in MM:SS
  const formatTime = (time) => {
    if (isNaN(time)) return "00:00";
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes.toString().padStart(2, "0")}:${seconds
      .toString()
      .padStart(2, "0")}`;
  };

  // Toggle play/pause
  const togglePlay = () => {
    const audio = audioRef.current;
    if (!audio || audioError) return;

    if (isPlaying) {
      audio.pause();
    } else {
      audio.play().catch((err) => {
        console.error("Error playing audio:", err);
        setAudioError("Failed to play audio");
      });
    }
    setIsPlaying(!isPlaying);
  };

  // Toggle mute
  const toggleMute = () => {
    const audio = audioRef.current;
    if (!audio) return;

    audio.muted = !isMuted;
    setIsMuted(!isMuted);
  };

  // Handle volume change
  const handleVolumeChange = (e) => {
    const newVolume = parseFloat(e.target.value);
    const audio = audioRef.current;
    if (!audio) return;

    audio.volume = newVolume;
    setVolume(newVolume);
    setIsMuted(newVolume === 0);
  };

  // Handle progress bar click
  const handleProgressBarClick = (e) => {
    const audio = audioRef.current;
    const progressBar = progressBarRef.current;
    if (!audio || !progressBar) return;

    const rect = progressBar.getBoundingClientRect();
    const clickPosition = (e.clientX - rect.left) / rect.width;
    const newTime = clickPosition * duration;

    audio.currentTime = newTime;
    setCurrentTime(newTime);
  };

  // Handle audio end
  const handleAudioEnd = () => {
    setIsPlaying(false);
    setCurrentTime(0);
    audioRef.current.currentTime = 0;
  };

  return (
    <div className="bg-black/20 rounded-lg p-3">
      {/* Hidden native audio element */}
      <audio
        ref={audioRef}
        src={audioSrc}
        onEnded={handleAudioEnd}
        preload="metadata"
      />

      {/* Error message */}
      {audioError && (
        <div className="mb-3 p-2 bg-red-500/20 border border-red-500/30 rounded text-red-300 text-sm">
          {audioError}
        </div>
      )}

      {/* Loading indicator */}
      {isLoading && !audioError && (
        <div className="mb-3 p-2 bg-blue-500/20 border border-blue-500/30 rounded text-blue-300 text-sm">
          Loading audio...
        </div>
      )}

      {/* Custom audio player UI */}
      <div className="flex items-center gap-3">
        {/* Play/Pause button */}
        <button
          onClick={togglePlay}
          disabled={audioError || isLoading}
          className={`w-10 h-10 flex items-center justify-center rounded-full transition-all duration-200 ${
            audioError || isLoading
              ? "bg-gray-500/30 cursor-not-allowed"
              : "bg-[#FF9933]/30 hover:bg-[#FF9933]/50"
          }`}
        >
          {isPlaying ? (
            <FiPause className="text-white w-5 h-5" />
          ) : (
            <FiPlay className="text-white w-5 h-5 ml-0.5" />
          )}
        </button>

        {/* Time display */}
        <div className="text-white/80 text-xs w-16">
          {formatTime(currentTime)}
        </div>

        {/* Progress bar */}
        <div
          ref={progressBarRef}
          className="flex-1 h-2 bg-white/10 rounded-full overflow-hidden cursor-pointer"
          onClick={handleProgressBarClick}
        >
          <div
            className="h-full bg-gradient-to-r from-[#FF9933] to-[#FFD700] transition-all duration-100"
            style={{ width: `${(currentTime / duration) * 100}%` }}
          ></div>
        </div>

        {/* Duration */}
        <div className="text-white/80 text-xs w-16 text-right">
          {formatTime(duration)}
        </div>

        {/* Volume control */}
        <div className="flex items-center gap-2">
          <button
            onClick={toggleMute}
            className="text-white/80 hover:text-white transition-colors duration-200"
          >
            {isMuted ? (
              <FiVolumeX className="w-5 h-5" />
            ) : (
              <FiVolume2 className="w-5 h-5" />
            )}
          </button>

          <input
            type="range"
            min="0"
            max="1"
            step="0.01"
            value={isMuted ? 0 : volume}
            onChange={handleVolumeChange}
            className="w-16 accent-[#FF9933] cursor-pointer"
          />
        </div>
      </div>
    </div>
  );
};

export default function SummaryView() {
  const navigate = useNavigate();
  const [summaryData, setSummaryData] = React.useState(null);
  const [file, setFile] = React.useState(null);
  const [error, setError] = React.useState(null);
  const [shouldAutoPlay, setShouldAutoPlay] = React.useState(false);
  const [autoPlayFailed, setAutoPlayFailed] = React.useState(false);

  // Load data from localStorage on mount
  useEffect(() => {
    try {
      const savedSummary = localStorage.getItem("summaryData");
      const savedFile = localStorage.getItem("fileData");
      const autoPlayFlag = localStorage.getItem("shouldAutoPlay");

      if (savedSummary && savedFile) {
        setSummaryData(JSON.parse(savedSummary));
        setFile(JSON.parse(savedFile));

        // Check if this is a fresh summary that should auto-play
        if (autoPlayFlag === "true") {
          setShouldAutoPlay(true);
          // Clear the flag so it doesn't auto-play on subsequent visits
          localStorage.removeItem("shouldAutoPlay");
          console.log("🎵 Auto-play enabled for fresh summary");

          // Try immediate auto-play with a more aggressive approach
          setTimeout(() => {
            console.log("🎵 Attempting immediate auto-play...");
            const audioUrl = JSON.parse(savedSummary).audio_file;
            if (audioUrl) {
              const finalUrl = audioUrl.startsWith('/api/stream/')
                ? `${CHAT_API_BASE_URL}${audioUrl}`
                : `${CHAT_API_BASE_URL}/api/stream/${audioUrl.split("/").pop()}`;

              console.log("🎵 Trying to play:", finalUrl);
              const audio = new Audio(finalUrl);
              audio.play()
                .then(() => {
                  console.log("✅ Immediate auto-play successful!");
                  toast.success("🎵 Audio started automatically!", { duration: 3000 });
                })
                .catch(err => {
                  console.warn("⚠️ Immediate auto-play failed:", err);
                  // Will fall back to the component-level auto-play
                });
            }
          }, 500);
        }
      } else {
        navigate("/learn");
      }
    } catch (err) {
      setError("Failed to load summary data");
      console.error("Error loading summary:", err);
    }
  }, [navigate]);

  const handleReset = () => {
    try {
      localStorage.removeItem("summaryData");
      localStorage.removeItem("fileData");
      navigate("/learn");
    } catch (err) {
      console.error("Error resetting data:", err);
    }
  };

  const handleRefreshAudio = () => {
    try {
      // Force refresh by clearing localStorage and fetching latest data
      localStorage.removeItem("summaryData");
      localStorage.removeItem("fileData");

      // Fetch latest summary from API
      fetch(`${CHAT_API_BASE_URL}/summarize-pdf`)
        .then(response => {
          if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
          }
          return response.json();
        })
        .then(data => {
          console.log("🔄 Refreshed summary data:", data);
          setSummaryData(data);
          // Save to localStorage
          localStorage.setItem("summaryData", JSON.stringify(data));
          setError(null);
        })
        .catch(error => {
          console.error("Error fetching latest summary:", error);
          setError(`Failed to refresh audio data: ${error.message}`);
        });
    } catch (err) {
      console.error("Error refreshing audio:", err);
      setError(`Error refreshing audio: ${err.message}`);
    }
  };

  const testAudioUrl = (audioUrl) => {
    console.log("🧪 Testing audio URL:", audioUrl);

    // Test if URL is accessible
    fetch(audioUrl, { method: 'HEAD' })
      .then(response => {
        if (response.ok) {
          console.log("✅ Audio URL is accessible");
          // Try to play the audio
          const audio = new Audio(audioUrl);
          audio.play()
            .then(() => console.log("✅ Audio playback started successfully"))
            .catch(err => console.error("❌ Audio playback failed:", err));
        } else {
          console.error("❌ Audio URL not accessible:", response.status, response.statusText);
        }
      })
      .catch(error => {
        console.error("❌ Error testing audio URL:", error);
      });
  };

  const formatSummary = (text) => {
    if (!text) return [];

    try {
      // Split by double newlines to get paragraphs
      const paragraphs = text.split("\n\n").filter((p) => p.trim());

      if (paragraphs.length === 0) {
        return [{ title: "Summary", paragraphs: [text] }];
      }

      // Group paragraphs into logical sections
      // First paragraph is usually the overview/introduction
      // Remaining paragraphs are grouped together
      if (paragraphs.length === 1) {
        return [{ 
          title: "Summary", 
          paragraphs: [paragraphs[0].trim().split('\n').join(' ')] 
        }];
      }

      // Multiple paragraphs: first is intro, rest are grouped
      return [{
        title: "Summary",
        paragraphs: paragraphs.map(p => p.trim().split('\n').join(' '))
      }];
    } catch (error) {
      console.error("Error formatting summary:", error);
      return [{ title: "Summary", paragraphs: [text] }];
    }
  };

  if (error) {
    return (
      <GlassContainer>
        <div className="text-center py-8">
          <p className="text-red-400 mb-4">{error}</p>
          <button
            onClick={() => navigate("/learn")}
            className="px-4 py-2 bg-[#FF9933]/20 hover:bg-[#FF9933]/30 rounded-lg transition-all duration-300 text-white"
          >
            Return to Summarizer
          </button>
        </div>
      </GlassContainer>
    );
  }

  if (!summaryData || !file) {
    return (
      <GlassContainer>
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-[#FF9933]"></div>
        </div>
      </GlassContainer>
    );
  }

  const phases = formatSummary(summaryData?.answer);

  return (
    <GlassContainer className="p-0">
      <div className="w-[95%] mx-auto mt-8 mb-8">
        <div className="bg-black/30 backdrop-blur-md p-8 rounded-xl shadow-xl space-y-6 relative">
          {/* Action Buttons */}
          <div className="absolute -right-3 -top-3 flex gap-2 z-20">
            <button
              onClick={handleRefreshAudio}
              className="p-2.5 bg-blue-600/80 hover:bg-blue-500/90 rounded-full transition-all duration-300 group border border-blue-400/30"
              title="Refresh audio data"
            >
              <FiVolume2 className="w-5 h-5 text-white group-hover:text-white/90 transition-colors duration-300" />
            </button>
            <button
              onClick={handleReset}
              className="p-2.5 bg-red-600/80 hover:bg-red-500/90 rounded-full transition-all duration-300 group border border-red-400/30"
              title="Close summary"
            >
              <FiX className="w-5 h-5 text-white group-hover:text-white/90 transition-colors duration-300" />
            </button>
          </div>

          {/* Title and Model Info */}
          <div className="border-b border-white/10 pb-4">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl text-white font-bold">
                {summaryData.title || "Document Summary"}
              </h2>

              {/* Prominent Audio Start Button for Fresh Content */}
              {(shouldAutoPlay || autoPlayFailed) && summaryData.audio_file && (
                <button
                  onClick={() => {
                    const audioUrl = summaryData.audio_file.startsWith('/api/stream/')
                      ? `${CHAT_API_BASE_URL}${summaryData.audio_file}`
                      : `${CHAT_API_BASE_URL}/api/stream/${summaryData.audio_file.split("/").pop()}`;

                    const audio = new Audio(audioUrl);
                    audio.play()
                      .then(() => {
                        setShouldAutoPlay(false);
                        setAutoPlayFailed(false);
                        toast.success("🎵 Audio started!", { duration: 2000 });
                      })
                      .catch(err => {
                        console.error("Manual play failed:", err);
                        toast.error("Failed to play audio");
                      });
                  }}
                  className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-green-600/30 to-blue-600/30 hover:from-green-600/50 hover:to-blue-600/50 rounded-lg transition-all duration-300 border border-green-500/30 text-white font-medium"
                >
                  <FiPlay className="w-5 h-5" />
                  🎵 Listen to Summary
                </button>
              )}

              {/* AI Model Badge */}
              {summaryData.llm && (
                <div
                  className="inline-block px-3 py-1 rounded text-sm font-medium"
                  style={{
                    background:
                      summaryData.llm === "grok"
                        ? "linear-gradient(135deg, rgba(255, 153, 51, 0.3), rgba(255, 153, 51, 0.1))"
                        : summaryData.llm === "llama"
                        ? "linear-gradient(135deg, rgba(0, 128, 255, 0.3), rgba(0, 128, 255, 0.1))"
                        : summaryData.llm === "chatgpt"
                        ? "linear-gradient(135deg, rgba(16, 163, 127, 0.3), rgba(16, 163, 127, 0.1))"
                        : "linear-gradient(135deg, rgba(128, 0, 255, 0.3), rgba(128, 0, 255, 0.1))",
                    border:
                      summaryData.llm === "grok"
                        ? "1px solid rgba(255, 153, 51, 0.3)"
                        : summaryData.llm === "llama"
                        ? "1px solid rgba(0, 128, 255, 0.3)"
                        : summaryData.llm === "chatgpt"
                        ? "1px solid rgba(16, 163, 127, 0.3)"
                        : "1px solid rgba(128, 0, 255, 0.3)",
                    boxShadow: "0 1px 3px rgba(0, 0, 0, 0.1)",
                  }}
                >
                  Analyzed by{" "}
                  {summaryData.llm.charAt(0).toUpperCase() +
                    summaryData.llm.slice(1)}
                </div>
              )}
            </div>
          </div>

          {/* Content Sections */}
          <div className="space-y-8">
            {phases.map((section, index) => (
              <div
                key={index}
                className="bg-black/20 p-6 rounded-xl border border-white/5 hover:border-white/10 transition-all duration-300"
              >
                {/* Section Header - Only show if there are multiple sections or custom title */}
                {phases.length > 1 && (
                  <div className="flex items-center mb-6">
                    <span className="bg-gradient-to-r from-[#FF9933]/20 to-[#FF9933]/10 px-4 py-1.5 rounded-lg text-sm font-bold text-white/90 border border-[#FF9933]/30">
                      Section {index + 1}
                    </span>
                    {section.title !== "Summary" && (
                      <h3 className="text-lg text-white/90 font-semibold ml-3">
                        {section.title}
                      </h3>
                    )}
                  </div>
                )}

                {/* Section Content */}
                <div className="space-y-6 summary-content">
                  {(section.paragraphs || section.points || []).map((paragraph, i) => (
                    <div
                      key={i}
                      className="group"
                    >
                      <p className="summary-paragraph text-white/95 leading-relaxed text-base md:text-lg font-normal text-justify bg-gradient-to-r from-white/5 via-white/3 to-transparent rounded-lg p-4 md:p-5 hover:bg-white/10 hover:shadow-lg hover:shadow-[#FF9933]/10 transition-all duration-300 border-l-2 border-[#FF9933]/30 hover:border-[#FF9933]/60 backdrop-blur-sm">
                        {paragraph}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            ))}

            {/* Audio Section */}
            {summaryData.audio_file && (
              <div className="mt-8 pt-6 border-t border-white/10">
                {shouldAutoPlay && (
                  <div className="mb-4 p-3 bg-green-600/20 border border-green-500/30 rounded-lg">
                    <div className="flex items-center gap-2">
                      <FiVolume2 className="w-4 h-4 text-green-400" />
                      <span className="text-green-300 text-sm">
                        🎵 Audio will start automatically when ready
                      </span>
                    </div>
                  </div>
                )}

                {autoPlayFailed && (
                  <div className="mb-4 p-4 bg-orange-600/20 border border-orange-500/30 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <FiPlay className="w-5 h-5 text-orange-400" />
                        <div>
                          <div className="text-orange-300 text-sm font-medium">
                            🔇 Auto-play was blocked by your browser
                          </div>
                          <div className="text-orange-400/80 text-xs">
                            Click the button to start listening to the summary
                          </div>
                        </div>
                      </div>
                      <button
                        onClick={() => {
                          const audioUrl = summaryData.audio_file.startsWith('/api/stream/')
                            ? `${CHAT_API_BASE_URL}${summaryData.audio_file}`
                            : `${CHAT_API_BASE_URL}/api/stream/${summaryData.audio_file.split("/").pop()}`;

                          const audio = new Audio(audioUrl);
                          audio.play()
                            .then(() => {
                              setAutoPlayFailed(false);
                              toast.success("🎵 Audio started!", { duration: 2000 });
                            })
                            .catch(err => {
                              console.error("Manual play failed:", err);
                              toast.error("Failed to play audio");
                            });
                        }}
                        className="px-4 py-2 bg-orange-500/30 hover:bg-orange-500/50 rounded-lg transition-all duration-300 text-orange-200 font-medium"
                      >
                        ▶️ Play Audio
                      </button>
                    </div>
                  </div>
                )}
                <div className="bg-black/20 rounded-lg backdrop-blur-sm border border-white/10">
                  <div className="flex items-center px-4 py-3">
                    <div className="flex items-center flex-1 min-w-0">
                      <span className="w-8 h-8 flex items-center justify-center bg-[#FF9933]/20 rounded-full mr-3">
                        <span className="text-lg">🎧</span>
                      </span>
                      <div className="flex-1 min-w-0">
                        <h4 className="text-white font-medium text-sm">
                          Audio Summary
                        </h4>
                        <p className="text-white/60 text-xs truncate">
                          {summaryData.audio_file.split("/").pop()}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => {
                          const audioUrl = summaryData.audio_file.startsWith('/api/stream/')
                            ? `${CHAT_API_BASE_URL}${summaryData.audio_file}`
                            : `${CHAT_API_BASE_URL}/api/stream/${summaryData.audio_file.split("/").pop()}`;
                          testAudioUrl(audioUrl);
                        }}
                        className="p-2 bg-green-600/20 hover:bg-green-600/30 rounded-lg transition-all duration-300 group"
                        title="Test audio URL"
                      >
                        <FiPlay className="w-4 h-4 text-green-400 group-hover:text-green-300 group-hover:scale-110 transition-all duration-300" />
                      </button>
                      <a
                        href={summaryData.audio_file.startsWith('/api/')
                          ? `${CHAT_API_BASE_URL}${summaryData.audio_file.replace('/stream/', '/audio/')}`
                          : `${CHAT_API_BASE_URL}/api/audio/${summaryData.audio_file.split("/").pop()}`}
                        download
                        className="p-2 bg-[#FF9933]/10 hover:bg-[#FF9933]/20 rounded-lg transition-all duration-300 group"
                        title="Download audio"
                      >
                        <FiDownload className="w-4 h-4 text-white/70 group-hover:text-white group-hover:scale-110 transition-all duration-300" />
                      </a>
                    </div>
                  </div>

                  <div className="px-4 pb-3">
                    {(() => {
                      const audioUrl = summaryData.audio_file.startsWith('/api/stream/')
                        ? `${CHAT_API_BASE_URL}${summaryData.audio_file}`
                        : `${CHAT_API_BASE_URL}/api/stream/${summaryData.audio_file.split("/").pop()}`;

                      return (
                        <CustomAudioPlayer
                          audioSrc={audioUrl}
                          autoPlay={shouldAutoPlay}
                          onAutoPlayAttempted={(success) => {
                            if (success) {
                              toast.success("🎵 Audio started automatically!", {
                                duration: 3000,
                                position: "bottom-right",
                              });
                              setAutoPlayFailed(false);
                            } else {
                              toast("🔇 Auto-play blocked. Click the orange button to listen!", {
                                icon: "🎵",
                                duration: 5000,
                                position: "bottom-right",
                              });
                              setAutoPlayFailed(true);
                            }
                            // Disable the auto-play notification after attempt
                            setShouldAutoPlay(false);
                          }}
                        />
                      );
                    })()}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </GlassContainer>
  );
}
