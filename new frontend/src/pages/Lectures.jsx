import React from "react";
import GlassContainer from "../components/GlassContainer";
import { useQuery } from "@tanstack/react-query";
import CenteredLoader from "../components/CenteredLoader";
import { getLectures } from "../api";
import { Play } from "lucide-react";
import { useSelector } from "react-redux";
import { selectUser } from "../store/authSlice";
import { processLecturesUsage, dispatchKarmaChange } from "../utils/karmaManager";
import { toast } from "react-hot-toast";
import { useTranslation } from "react-i18next";

export default function Lectures() {
  const user = useSelector(selectUser);
  const { t } = useTranslation();
  
  const {
    data: lectures,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ["lectures"],
    queryFn: getLectures,
  });

  const handleLectureClick = () => {
    // Process karma when user clicks on a lecture
    const effectiveUserId = user?.id || user?.user_id || 'guest-user';
    const karmaResult = processLecturesUsage(effectiveUserId);
    if (karmaResult) {
      dispatchKarmaChange(karmaResult);
      toast.success(`+${karmaResult.change} Karma: ${karmaResult.reason}`, {
        position: "top-right",
        duration: 3000,
      });
    }
  };

  // dynamic tilt handlers
  const handleMouseEnter = (e) => {
    const cardInner = e.currentTarget.querySelector(".flip-card-inner");
    cardInner.style.transition = "none";
  };
  const handleMouseMove = (e) => {
    const cardInner = e.currentTarget.querySelector(".flip-card-inner");
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const midX = rect.width / 2;
    const midY = rect.height / 2;
    const rotateY = ((x - midX) / midX) * 15;
    const rotateX = ((midY - y) / midY) * 15;
    cardInner.style.transform = `rotateY(${rotateY}deg) rotateX(${rotateX}deg)`;
  };
  const handleMouseLeave = (e) => {
    const cardInner = e.currentTarget.querySelector(".flip-card-inner");
    cardInner.style.transition = "transform 0.5s ease";
    cardInner.style.transform = "rotateY(0deg) rotateX(0deg)";
  };

  return (
    <GlassContainer>
      <h2
        className="text-4xl md:text-5xl font-extrabold mb-6 drop-shadow-lg transition-all duration-300 hover:bg-gradient-to-r hover:from-white hover:to-[#FF9933] hover:bg-clip-text hover:text-transparent"
        style={{ color: "#FFFFFF", fontFamily: "Nunito, sans-serif" }}
      >
        {t("Lectures")}
      </h2>
      <p
        className="text-lg md:text-xl font-medium mb-4"
        style={{ color: "#FFFFFF", fontFamily: "Nunito, sans-serif" }}
      >
        {t("Watch lectures and video content here.")}
      </p>
      {isLoading ? (
        <div className="relative" style={{ height: "calc(100vh - 350px)" }}>
          <CenteredLoader />
        </div>
      ) : isError ? (
        <p className="text-red-500">
          {error?.message || t("Failed to fetch lectures.")}
        </p>
      ) : lectures && Array.isArray(lectures) && lectures.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-4 gap-8">
          {lectures.map((lecture) => (
            <a
              key={lecture.lecture_id}
              href={lecture.link_to_lec}
              target="_blank"
              rel="noopener noreferrer"
              className="flip-card w-80 aspect-video mx-auto block group"
              onMouseEnter={handleMouseEnter}
              onMouseMove={handleMouseMove}
              onMouseLeave={handleMouseLeave}
              onClick={handleLectureClick}
            >
              <div className="flip-card-inner">
                <div className="flip-card-front relative overflow-hidden rounded-xl shadow-lg border border-white/20">
                  <img
                    src={lecture.image || lecture.thumbnail || "https://images.unsplash.com/photo-1456513080510-7bf3a84b82f8?w=400&h=300&fit=crop"}
                    alt={lecture.title}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      e.target.src = "https://images.unsplash.com/photo-1456513080510-7bf3a84b82f8?w=400&h=300&fit=crop";
                    }}
                  />
                  <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                    <div className="bg-orange-500 bg-opacity-75 rounded-full p-3">
                      <Play className="w-6 h-6 text-white" />
                    </div>
                  </div>
                </div>
                <div className="flip-card-back flex flex-col items-center justify-center bg-gradient-to-br from-orange-400 to-yellow-300 rounded-xl shadow-lg border border-white/20">
                  <h3 className="text-lg font-bold text-white drop-shadow-lg text-center px-2">
                    {lecture.title}
                  </h3>
                </div>
              </div>
            </a>
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <p className="text-white/70 text-lg">{t("No lectures available at the moment.")}</p>
          <p className="text-white/50 text-sm mt-2">{t("Please check back later for new content.")}</p>
        </div>
      )}
      {/* Tilt card styles */}
      <style>{`
        .flip-card { perspective: 1000px; }
        .flip-card-inner {
          position: relative;
          width: 100%;
          height: 100%;
          transform-style: preserve-3d;
          transition: transform 0.5s ease;
        }
        .flip-card-front, .flip-card-back {
          position: absolute;
          width: 100%;
          height: 100%;
          backface-visibility: hidden;
          border-radius: 0.75rem;
        }
        .flip-card-front { z-index: 2; }
        .flip-card-back {
          transform: rotateY(180deg);
          z-index: 1;
          display: flex;
          align-items: center;
          justify-content: center;
        }
      `}</style>
    </GlassContainer>
  );
}
