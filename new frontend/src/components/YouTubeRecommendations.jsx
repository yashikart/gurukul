import React from "react";
import { useLazyGetYouTubeRecommendationsQuery } from "../api/subjectsApiSlice";
import { ExternalLink, Play } from "lucide-react";

export default function YouTubeRecommendations({ subject, topic }) {
  const [triggerRecommendations, { data, isLoading, error }] = useLazyGetYouTubeRecommendationsQuery();
  const [lastFetchedKey, setLastFetchedKey] = React.useState("");

  React.useEffect(() => {
    // Create a unique key from subject and topic
    const currentKey = `${subject || ""}_${topic || ""}`;
    
    // Only fetch if subject/topic changed and both are provided
    // This ensures it fetches when lesson is generated, and refetches if user generates a new lesson
    if (subject && topic && subject.trim() && topic.trim() && currentKey !== lastFetchedKey) {
      setLastFetchedKey(currentKey);
      triggerRecommendations({
        subject: subject.trim(),
        topic: topic.trim(),
        max_results: 5,
      });
    }
  }, [subject, topic, triggerRecommendations, lastFetchedKey]);

  if (!subject || !topic || !subject.trim() || !topic.trim()) {
    return null;
  }

  if (isLoading) {
    return (
      <div className="bg-white/10 rounded-xl p-6 backdrop-blur-md border border-white/20 shadow-lg">
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-4 border-orange-500/30 border-t-orange-500"></div>
          <span className="ml-3 text-white/70">Loading YouTube recommendations...</span>
        </div>
      </div>
    );
  }

  if (error) {
    console.error("❌ YouTube Recommendations Error:", error);
    const errorMessage = error?.error || error?.data?.error || "Unknown error";
    const isNetworkError = error?.status === "NETWORK_ERROR" || errorMessage.includes("Network error");
    const is404Error = error?.status === 404 || errorMessage.includes("404");
    
    return (
      <div className="bg-white/10 rounded-xl p-6 backdrop-blur-md border border-red-500/20 shadow-lg">
        <div className="text-center py-4">
          <div className="mb-3">
            <div className="w-12 h-12 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-2">
              <span className="text-2xl">⚠️</span>
            </div>
          </div>
          <p className="text-white/90 font-medium mb-2">
            Unable to load YouTube recommendations
          </p>
          {is404Error ? (
            <div className="text-white/60 text-sm space-y-2">
              <p>
                The YouTube recommendations endpoint was not found (404).
              </p>
              <p className="text-amber-300 font-medium">
                ⚠️ Please restart the subject generation service (port 8005) to load the new endpoint.
              </p>
              <p className="text-xs text-white/50 mt-2">
                The endpoint `/youtube_recommendations` needs to be loaded by restarting the backend service.
              </p>
            </div>
          ) : isNetworkError ? (
            <p className="text-white/60 text-sm">
              Please ensure the subject generation service is running on port 8005
            </p>
          ) : (
            <p className="text-white/60 text-sm">
              {errorMessage}
            </p>
          )}
          {process.env.NODE_ENV === 'development' && (
            <details className="mt-4 text-left">
              <summary className="text-white/50 text-xs cursor-pointer">Debug Info</summary>
              <pre className="text-white/40 text-xs mt-2 p-2 bg-black/20 rounded overflow-auto">
                {JSON.stringify(error, null, 2)}
              </pre>
            </details>
          )}
        </div>
      </div>
    );
  }

  if (!data || !data.recommendations || data.recommendations.length === 0) {
    return null;
  }

  return (
    <div className="bg-white/10 rounded-xl p-6 backdrop-blur-md border border-white/20 shadow-lg">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center space-x-3 mb-2">
          <div className="w-10 h-10 bg-gradient-to-br from-red-500 to-red-600 rounded-xl flex items-center justify-center">
            <Play className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="text-2xl font-bold text-white">
              YouTube Recommendations
            </h3>
            <p className="text-white/60 text-sm">
              Videos related to {subject}: {topic}
            </p>
          </div>
        </div>
      </div>

      {/* Recommendations Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {data.recommendations.map((video, index) => (
          <a
            key={video.video_id || index}
            href={video.video_url}
            target="_blank"
            rel="noopener noreferrer"
            className="group bg-white/5 hover:bg-white/10 rounded-xl p-4 border border-white/10 hover:border-white/30 transition-all duration-300 cursor-pointer"
          >
            {/* Thumbnail */}
            <div className="relative w-full mb-3 rounded-lg overflow-hidden bg-black/20" style={{ aspectRatio: "16/9" }}>
              {video.thumbnail_url ? (
                <img
                  src={video.thumbnail_url}
                  alt={video.title}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-red-500/20 to-red-600/20">
                  <Play className="w-12 h-12 text-white/50" />
                </div>
              )}
              {/* Play overlay */}
              <div className="absolute inset-0 bg-black/40 group-hover:bg-black/20 transition-all duration-300 flex items-center justify-center opacity-0 group-hover:opacity-100">
                <div className="w-16 h-16 bg-red-600 rounded-full flex items-center justify-center transform scale-75 group-hover:scale-100 transition-transform duration-300">
                  <Play className="w-8 h-8 text-white ml-1" fill="white" />
                </div>
              </div>
            </div>

            {/* Video Info */}
            <div className="space-y-2">
              <h4 className="text-white font-semibold text-sm line-clamp-2 group-hover:text-amber-300 transition-colors">
                {video.title}
              </h4>
              
              {video.channel_title && (
                <p className="text-white/60 text-xs flex items-center">
                  <span className="truncate">{video.channel_title}</span>
                </p>
              )}

              {/* Description */}
              {video.description && (
                <p className="text-white/50 text-xs line-clamp-2">
                  {video.description}
                </p>
              )}

              {/* Link indicator */}
              <div className="flex items-center text-red-400 text-xs pt-2 opacity-0 group-hover:opacity-100 transition-opacity">
                <ExternalLink className="w-3 h-3 mr-1" />
                <span>Watch on YouTube</span>
              </div>
            </div>
          </a>
        ))}
      </div>

      {/* Footer */}
      <div className="mt-6 pt-4 border-t border-white/10">
        <p className="text-white/50 text-xs text-center">
          {data.count} recommendation{data.count !== 1 ? "s" : ""} found
        </p>
      </div>
    </div>
  );
}
