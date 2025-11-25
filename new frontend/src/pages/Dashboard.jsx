import React, { useState, useEffect, useRef } from "react";
import GlassContainer from "../components/GlassContainer";
import { supabase } from "../supabaseClient";
import { useUser } from "@clerk/clerk-react";
import {
  Clock,
  Target,
  Trophy,
  ChevronUp,
  Award,
  User,
  Calendar,
  TrendingUp,
  Zap,
  Sun,
  Cloud,
  CloudRain,
  Snowflake,
  CloudLightning,
  CloudFog,
  Moon,
  Quote,
} from "lucide-react";
import GlassButton from "../components/GlassButton";
import { useTimeTracking } from "../hooks/useTimeTracking";
import toast from "react-hot-toast";
import { useQuery } from "@tanstack/react-query";

// Format seconds into Hh Mm Ss
const formatDuration = (totalSeconds) => {
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  return `${hours}h ${minutes}m ${seconds}s`;
};

const LOCAL_QUOTES = [
  "Every day is a chance to learn something new!",
  "Small steps every day lead to big results.",
  "Consistency is the key to mastery.",
  "Your future is created by what you do today, not tomorrow.",
  "Learning never exhausts the mind.",
  "Success is the sum of small efforts, repeated day in and day out.",
  "The expert in anything was once a beginner.",
  "Stay positive, work hard, make it happen.",
];

// DashboardTile: glassy, equal-height tile for dashboard sections
function DashboardTile({ icon, title, children, footer, className = "" }) {
  return (
    <div
      className={`bg-white/5 rounded-xl shadow-inner flex flex-col justify-between h-full min-h-80 p-6 ${className}`}
    >
      <div className="flex items-center mb-3">
        <span className="wide-list-icon">{icon}</span>
        <span className="font-bold ml-2 text-lg md:text-xl">{title}</span>
      </div>
      <div className="flex-1 flex flex-col justify-center">{children}</div>
      {footer && <div className="mt-4">{footer}</div>}
    </div>
  );
}

export default function Dashboard() {
  const { totalTimeToday, currentSessionTime, isLoading, timeHistory } =
    useTimeTracking();
  const [error, setError] = useState(null);
  const [dailyGoal, setDailyGoal] = useState(0);
  const [isSettingGoal, setIsSettingGoal] = useState(false);
  const [goalInput, setGoalInput] = useState({ hours: 0, minutes: 0 });
  const [user, setUser] = useState(null);
  const { isSignedIn, user: clerkUser } = useUser();
  const subscriptionRef = useRef(null);
  const coords = useGeolocation();
  const { location, weather } = useLocationWeather(coords);
  const [dateString, setDateString] = useState("");
  // Fact for 'Did you know?'
  const [randomFact, setRandomFact] = useState("");

  // Fetch a daily motivational quote directly from external API
  const { data: quoteData, isLoading: quoteLoading } = useQuery({
    queryKey: ["daily-quote"],
    queryFn: async () => {
      try {
        // Directly use the external API
        const res = await fetch(
          "https://api.quotable.io/random?tags=motivational|inspirational",
          { signal: AbortSignal.timeout(5000) }
        );

        if (res.ok) {
          const data = await res.json();
          if (data.content) return { q: data.content };
        }

        throw new Error("Quote API failed or returned invalid data");
      } catch (error) {
        console.log("Using local quote due to:", error.message);

        // Fallback to local quotes
        const random =
          LOCAL_QUOTES[Math.floor(Math.random() * LOCAL_QUOTES.length)];
        return { q: random };
      }
    },
    staleTime: 1000 * 60 * 60 * 12, // 12 hours
    retry: 1, // Retry once if it fails
  });

  // Helper: Calculate stats from timeHistory
  const getStats = () => {
    if (!timeHistory || timeHistory.length === 0)
      return { week: 0, month: 0, daysActive: 0, bestStreak: 1 };
    const now = new Date();
    let week = 0,
      month = 0,
      daysActiveSet = new Set(),
      streak = 0,
      bestStreak = 0,
      prevDay = null;
    const sortedHistory = [...timeHistory].sort(
      (a, b) => new Date(a.date) - new Date(b.date)
    );
    sortedHistory.forEach(({ date, total }) => {
      const d = new Date(date);
      if (
        d.getMonth() === now.getMonth() &&
        d.getFullYear() === now.getFullYear()
      )
        month += total;
      if (now - d < 8 * 24 * 3600 * 1000) week += total;
      daysActiveSet.add(date);
      // Streak calculation
      if (prevDay) {
        const diff = (d - prevDay) / (1000 * 3600 * 24);
        if (diff === 1) {
          streak++;
        } else {
          bestStreak = Math.max(bestStreak, streak);
          streak = 1;
        }
      } else {
        streak = 1;
      }
      prevDay = d;
    });
    bestStreak = Math.max(bestStreak, streak);
    const stats = {
      week,
      month,
      daysActive: daysActiveSet.size,
      bestStreak,
    };
    // Remove debug output
    // console.debug("timeHistory", timeHistory);
    // console.debug("stats", stats);
    return stats;
  };

  useEffect(() => {
    const initializeDashboard = async () => {
      try {
        if (!isSignedIn || !clerkUser) throw new Error("Not signed in");

        // Map Clerk user to local shape for UI reuse
        setUser({
          id: clerkUser.id,
          email: clerkUser.primaryEmailAddress?.emailAddress || "",
          user_metadata: {
            avatar_url: clerkUser.imageUrl,
            full_name: clerkUser.fullName || clerkUser.username || "",
          },
        });
        const userId = clerkUser.id;

        // Fetch daily goal
        const { data: goalData, error: goalError } = await supabase
          .from("user_goals")
          .select("daily_goal_seconds")
          .eq("user_id", userId)
          .maybeSingle();

        if (goalError) {
          console.error("Error fetching goal:", goalError);
        } else if (goalData) {
          setDailyGoal(goalData.daily_goal_seconds);
          setGoalInput({
            hours: Math.floor(goalData.daily_goal_seconds / 3600),
            minutes: Math.floor((goalData.daily_goal_seconds % 3600) / 60),
          });
        }

        // Set up real-time subscription for user_goals
        subscriptionRef.current = supabase
          .channel("user_goals_changes")
          .on(
            "postgres_changes",
            {
              event: "*",
              schema: "public",
              table: "user_goals",
              filter: `user_id=eq.${userId}`,
            },
            (payload) => {
              if (payload.new?.daily_goal_seconds) {
                setDailyGoal(payload.new.daily_goal_seconds);
              }
            }
          )
          .subscribe();
      } catch (err) {
        console.error("Error initializing dashboard:", err);
        setError(err.message || "Error");
      }
    };

    initializeDashboard();

    return () => {
      if (subscriptionRef.current) {
        subscriptionRef.current.unsubscribe();
      }
    };
  }, [isSignedIn, clerkUser]);

  const handleSaveGoal = async () => {
    try {
      if (!isSignedIn || !clerkUser) throw new Error("Not signed in");

      const totalSeconds = goalInput.hours * 3600 + goalInput.minutes * 60;
      const { error } = await supabase.from("user_goals").upsert({
        user_id: clerkUser.id,
        daily_goal_seconds: totalSeconds,
      });

      if (error) throw error;

      setDailyGoal(totalSeconds);
      setIsSettingGoal(false);
      toast.success("Daily goal updated successfully!");
    } catch (err) {
      console.error("Error saving goal:", err);
      toast.error("Failed to save goal");
    }
  };

  const totalTimeWithSession = totalTimeToday + currentSessionTime;
  const displayTime = formatDuration(totalTimeWithSession);
  const percentageComplete = dailyGoal
    ? Math.min((totalTimeWithSession / dailyGoal) * 100, 100)
    : 0;

  // Stats
  const stats = getStats();

  // Achievements (frontend only)
  const achievements = [
    {
      icon: <Quote className="text-[#FFD700] mr-2" />,
      label: "First Day Completed",
      unlocked: stats.daysActive >= 1,
    },
    {
      icon: <TrendingUp className="text-[#FF9933] mr-2" />,
      label: "1 Hour in a Day",
      unlocked: totalTimeWithSession >= 3600,
    },
    {
      icon: <Zap className="text-[#00CFFF] mr-2" />,
      label: "5-Day Streak",
      unlocked: stats.bestStreak >= 5,
    },
    {
      icon: <Award className="text-[#FFD700] mr-2" />,
      label: "Daily Goal Completed",
      unlocked: percentageComplete >= 100,
    },
  ];
  // Remove debug output for achievements
  // achievements.forEach((a) => console.debug(`${a.label}: ${a.unlocked}`));

  // Next Goal
  let nextGoal = "Keep going!";
  let nextGoalType = "none";
  if (percentageComplete < 100 && dailyGoal > 0) {
    nextGoal = `Complete your daily goal: ${formatDuration(
      dailyGoal - totalTimeWithSession
    )}`;
    nextGoalType = "daily";
  } else if (stats.bestStreak < 5) {
    nextGoal = "Reach a 5-day streak!";
    nextGoalType = "streak";
  } else {
    nextGoal = "You're a star!";
    nextGoalType = "star";
  }

  // Next Goal progress bar logic
  let nextGoalProgress = 0;
  let nextGoalProgressText = "";
  if (nextGoalType === "daily") {
    nextGoalProgress = percentageComplete;
    nextGoalProgressText = `${Math.round(percentageComplete)}% complete`;
  } else if (nextGoalType === "streak") {
    nextGoalProgress = Math.min((stats.bestStreak / 5) * 100, 100);
    nextGoalProgressText = `${stats.bestStreak} / 5 days`;
  } else if (nextGoalType === "star") {
    nextGoalProgress = 100;
    nextGoalProgressText = `100% complete`;
  }

  // Circular Progress Bar for daily goal
  const CircleProgress = ({ percent = 0, size = 80, stroke = 8, goal = 0 }) => {
    const r = (size - stroke) / 2;
    const c = 2 * Math.PI * r;
    // Format goal as Hh Mm
    let goalText = "";
    if (goal > 0) {
      const h = Math.floor(goal / 3600);
      const m = Math.floor((goal % 3600) / 60);
      goalText = `${h > 0 ? h + "h " : ""}${m > 0 ? m + "m" : ""}`.trim();
    }
    return (
      <div style={{ position: "relative", width: size, height: size }}>
        <svg width={size} height={size}>
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            stroke="#fff"
            strokeWidth={stroke}
            fill="none"
            opacity="0.15"
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            stroke="#FFD700"
            strokeWidth={stroke}
            fill="none"
            strokeDasharray={c}
            strokeDashoffset={c - (percent / 100) * c}
            strokeLinecap="round"
            style={{ transition: "stroke-dashoffset 0.5s" }}
          />
        </svg>
        {goalText && (
          <div
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              width: "100%",
              height: "100%",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontWeight: 600,
              color: "#FFD700",
              fontSize: "1.1rem",
              pointerEvents: "none",
            }}
          >
            {goalText}
          </div>
        )}
      </div>
    );
  };

  // Weather icon mapping using Lucide
  const getWeatherIcon = (main, isDay) => {
    switch (main) {
      case "Clear":
        return isDay ? (
          <Sun size={36} color="#FFD700" />
        ) : (
          <Moon size={36} color="#FFD700" />
        );
      case "Clouds":
        return <Cloud size={36} color="#b0b0b0" />;
      case "Rain":
      case "Drizzle":
        return <CloudRain size={36} color="#4fc3f7" />;
      case "Snow":
        return <Snowflake size={36} color="#90caf9" />;
      case "Thunderstorm":
        return <CloudLightning size={36} color="#FFD700" />;
      case "Fog":
      case "Mist":
      case "Haze":
        return <CloudFog size={36} color="#b0b0b0" />;
      default:
        return <Cloud size={36} color="#b0b0b0" />;
    }
  };

  useEffect(() => {
    // Set current date string
    const now = new Date();
    setDateString(
      now.toLocaleDateString(undefined, {
        weekday: "long",
        year: "numeric",
        month: "long",
        day: "numeric",
      })
    );
  }, []);

  useEffect(() => {
    const fetchFact = async () => {
      try {
        // Directly use the external API
        const res = await fetch("http://numbersapi.com/random/trivia?json", {
          signal: AbortSignal.timeout(5000),
        });

        if (res.ok) {
          const data = await res.json();
          setRandomFact(data.text);
          return;
        }

        throw new Error("Numbers API failed");
      } catch (error) {
        console.log("Using static fact due to:", error.message);

        // Fallback to static facts
        const staticFacts = [
          "The human brain can store approximately 2.5 petabytes of information.",
          "A day on Venus is longer than a year on Venus.",
          "Honey never spoils. Archaeologists have found pots of honey in ancient Egyptian tombs that are over 3,000 years old and still perfectly good to eat.",
          "The first computer programmer was a woman named Ada Lovelace.",
          "The Great Barrier Reef is the largest living structure on Earth.",
          "A group of flamingos is called a 'flamboyance'.",
          "The shortest war in history was between Britain and Zanzibar on August 27, 1896. Zanzibar surrendered after 38 minutes.",
          "The average person will spend six months of their life waiting for red lights to turn green.",
          "A bolt of lightning is five times hotter than the surface of the sun.",
          "The world's oldest known living tree is over 5,000 years old.",
        ];

        setRandomFact(
          staticFacts[Math.floor(Math.random() * staticFacts.length)]
        );
      }
    };

    fetchFact();
  }, []);

  // Debug logs removed for cleaner console

  return (
    <GlassContainer>
      <div className="w-full max-w-[1500px] mx-auto">
        {/* Weather/Date/Location Tile */}
        <ul className="wide-list mb-6">
          <li className="wide-list-item">
            <span className="wide-list-icon">
              {weather ? (
                getWeatherIcon(weather.main, weather.isDay)
              ) : (
                <Cloud size={40} color="#b0b0b0" />
              )}
            </span>
            <div className="flex flex-col">
              <span className="font-bold text-lg">{dateString}</span>
              <span className="text-sm text-white/70">
                {location
                  ? `${location.city ? location.city + ", " : ""}${
                      location.country
                    }`
                  : "Location unavailable"}
              </span>
            </div>
            <div className="ml-auto flex items-center gap-2">
              {weather ? (
                <>
                  <span className="text-2xl font-bold">
                    {weather.temp}&deg;C
                  </span>
                  <span className="capitalize text-white/80">
                    {weather.desc}
                  </span>
                </>
              ) : (
                <span className="text-white/40">Weather unavailable</span>
              )}
            </div>
          </li>
        </ul>

        {/* Welcome/Profile List */}
        <ul className="wide-list mb-6">
          <li className="wide-list-item">
            {user?.user_metadata?.avatar_url ? (
              <img
                src={
                  user.user_metadata.avatar_url ||
                  "https://ui-avatars.com/api/?name=User"
                }
                alt="avatar"
                className="wide-list-avatar mr-3"
                onError={(e) => {
                  e.target.onerror = null;
                  e.target.src = "https://ui-avatars.com/api/?name=User";
                }}
              />
            ) : (
              <span className="wide-list-icon mr-3">
                <User size={48} className="text-[#FFD700]" />
              </span>
            )}
            <div>
              <div className="font-semibold text-lg">
                Welcome back
                {user?.user_metadata?.full_name
                  ? `, ${user.user_metadata.full_name}`
                  : ""}
                !
              </div>
              <div className="text-sm text-white/70">{user?.email}</div>
            </div>
            <div className="italic text-[#FFD700] text-sm flex items-center ml-auto min-w-0 sm:min-w-[200px]">
              <Quote size={20} className="mr-2" />
              {quoteLoading && <span>Loading quote...</span>}
              {quoteData?.q && <span>"{quoteData.q}"</span>}
            </div>
          </li>
        </ul>

        {/* Progress & Stats List */}
        <ul className="wide-list mb-6">
          <li className="wide-list-item">
            <span className="wide-list-icon mr-4">
              <CircleProgress percent={percentageComplete} goal={dailyGoal} />
            </span>
            <div>
              <div className="font-bold text-lg mb-1">Today's Progress</div>
              <div className="text-xl font-extrabold mb-1">
                {isLoading ? "--:--:--" : displayTime}
              </div>
              {dailyGoal > 0 && (
                <div className="text-sm text-white/70 mb-1">
                  Goal: {formatDuration(dailyGoal)}
                </div>
              )}
              <GlassButton
                icon={Target}
                onClick={() => setIsSettingGoal(true)}
                variant="primary"
                className="mt-1"
              >
                Set Daily Goal
              </GlassButton>
            </div>
          </li>
          <li className="wide-list-item">
            <span className="wide-list-icon">
              <Trophy size={24} className="text-[#FFD700]" />
            </span>
            <span className="font-bold mr-2">Learning Streak:</span>
            <span className="text-lg font-extrabold">
              {stats.bestStreak || 1} day
              {(stats.bestStreak || 1) > 1 ? "s" : ""}
            </span>
          </li>
          <li className="wide-list-item">
            <span className="wide-list-icon">
              <Calendar size={20} className="text-[#FFD700]" />
            </span>
            <span>
              This week:{" "}
              <span className="font-semibold">
                {formatDuration(stats.week)}
              </span>
            </span>
            <span className="ml-4">
              This month:{" "}
              <span className="font-semibold">
                {formatDuration(stats.month)}
              </span>
            </span>
            <span className="ml-4">
              Days active:{" "}
              <span className="font-semibold">{stats.daysActive}</span>
            </span>
          </li>
        </ul>

        {/* Achievements & Next Goal */}
        <div className="flex flex-col md:flex-row gap-10 h-full items-stretch">
          {/* Achievements */}
          <div className="flex-1 h-full">
            <DashboardTile
              icon={<Award className="text-[#FFD700]" />}
              title="Achievements:"
              footer={null}
            >
              {/* Progress bar for achievements */}
              <div className="w-full mb-3">
                <div className="w-full h-3 bg-white/10 rounded-full overflow-hidden shadow-inner">
                  <div
                    className="h-full bg-gradient-to-r from-[#FFD700] to-[#FF9933] transition-all duration-500"
                    style={{
                      width: `${Math.round(
                        (achievements.filter((a) => a.unlocked).length /
                          achievements.length) *
                          100
                      )}%`,
                    }}
                  ></div>
                </div>
                <div className="text-xs text-white/60 mt-1 text-right">
                  {achievements.filter((a) => a.unlocked).length} /{" "}
                  {achievements.length} unlocked
                </div>
              </div>
              <div className="flex flex-row flex-wrap gap-3 gap-y-2 items-center w-full bg-white/10 rounded-xl p-3 shadow-inner">
                {achievements.map((a, i) => (
                  <span
                    key={i}
                    className={`flex items-center gap-1 px-2 py-1 rounded-xl transition whitespace-nowrap ${
                      a.unlocked
                        ? "text-[#FFD700] bg-[rgba(255,215,0,0.12)] border border-[#FFD700]/30 shadow-sm"
                        : "text-white/40"
                    }`}
                    style={
                      a.unlocked
                        ? { boxShadow: "0 2px 8px 0 rgba(255,215,0,0.10)" }
                        : {}
                    }
                  >
                    {a.icon}
                    <span>{a.label}</span>
                    {a.unlocked && <span className="ml-1">✔️</span>}
                  </span>
                ))}
              </div>
            </DashboardTile>
          </div>
          {/* Next Goal */}
          <div className="flex-1 h-full">
            <DashboardTile
              icon={<TrendingUp size={24} className="text-[#FF9933]" />}
              title="Next Goal:"
              footer={
                <div className="p-3 bg-white/10 rounded-lg text-white/80 text-sm">
                  <span className="font-semibold text-[#FFD700]">
                    Did you know?
                  </span>{" "}
                  {randomFact}
                </div>
              }
            >
              {/* Progress bar for next goal */}
              <div className="w-full mb-3">
                <div className="w-full h-3 rounded-full overflow-hidden shadow-inner bg-white/10">
                  <div
                    className="h-full bg-gradient-to-r from-[#FFD700] to-[#FF9933] transition-all duration-500"
                    style={{ width: `${Math.round(nextGoalProgress)}%` }}
                  ></div>
                </div>
                <div className="text-xs text-white/60 mt-1 text-right">
                  {nextGoalProgressText}
                </div>
              </div>
              <span className="text-lg md:text-2xl font-semibold text-[#FFD700] mb-2">
                {nextGoal}
              </span>
            </DashboardTile>
          </div>
        </div>

        {/* Goal Setting Modal */}
        {isSettingGoal && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
            <div className="bg-[#1E1E28] p-6 rounded-xl border border-white/20 w-full max-w-md">
              <h3 className="text-xl font-semibold mb-4">
                Set Daily Learning Goal
              </h3>
              <div className="flex gap-4 mb-6">
                <div>
                  <label className="block text-sm mb-1">Hours</label>
                  <input
                    type="number"
                    min="0"
                    value={goalInput.hours}
                    onChange={(e) =>
                      setGoalInput((prev) => ({
                        ...prev,
                        hours: parseInt(e.target.value) || 0,
                      }))
                    }
                    className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm mb-1">Minutes</label>
                  <input
                    type="number"
                    min="0"
                    max="59"
                    value={goalInput.minutes}
                    onChange={(e) =>
                      setGoalInput((prev) => ({
                        ...prev,
                        minutes: parseInt(e.target.value) || 0,
                      }))
                    }
                    className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white"
                  />
                </div>
              </div>
              <div className="flex justify-end gap-3">
                <GlassButton onClick={() => setIsSettingGoal(false)}>
                  Cancel
                </GlassButton>
                <GlassButton variant="primary" onClick={handleSaveGoal}>
                  Save Goal
                </GlassButton>
              </div>
            </div>
          </div>
        )}

        {error && <p className="text-red-500">{error}</p>}
      </div>
    </GlassContainer>
  );
}

function useGeolocation() {
  const [coords, setCoords] = useState(null);
  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) =>
          setCoords({ lat: pos.coords.latitude, lon: pos.coords.longitude }),
        () => setCoords(null)
      );
    }
  }, []);
  return coords;
}

function useLocationWeather(coords) {
  // Directly use external APIs for location and weather
  const locationWeatherQuery = useQuery({
    queryKey: ["location-weather", coords],
    enabled: !!coords,
    queryFn: async () => {
      try {
        // Fetch location from OpenCage
        const locationRes = await fetch(
          `https://api.opencagedata.com/geocode/v1/json?q=${coords.lat}+${coords.lon}&key=16fa592c443b4ee4a8495415749e4c76`,
          { signal: AbortSignal.timeout(5000) }
        );

        // Fetch weather from OpenWeatherMap
        const weatherRes = await fetch(
          `https://api.openweathermap.org/data/2.5/weather?lat=${coords.lat}&lon=${coords.lon}&appid=40c58e845fb8e4636bca94fa940db50e&units=metric`,
          { signal: AbortSignal.timeout(5000) }
        );

        // Process location data
        let location = { city: "", country: "" };
        if (locationRes.ok) {
          const locationData = await locationRes.json();
          const components = locationData.results[0]?.components || {};
          location = {
            city:
              components.city || components.town || components.village || "",
            country: components.country || "",
          };
        } else {
          console.log("Location API error:", await locationRes.text());
        }

        // Process weather data
        let weather = null;
        if (weatherRes.ok) {
          const weatherData = await weatherRes.json();
          weather = {
            main: weatherData.weather[0].main,
            desc: weatherData.weather[0].description,
            temp: Math.round(weatherData.main.temp),
            isDay: weatherData.weather[0].icon.includes("d"),
          };
        } else {
          console.log("Weather API error:", await weatherRes.text());
        }

        return { location, weather };
      } catch (error) {
        console.log("Weather/location APIs failed:", error.message);

        // Return empty data if APIs fail
        return {
          location: { city: "Location unavailable", country: "" },
          weather: null,
        };
      }
    },
    retry: 1, // Retry once if it fails
    staleTime: 1000 * 60 * 30, // 30 minutes
  });

  return {
    location: locationWeatherQuery.data?.location,
    weather: locationWeatherQuery.data?.weather,
    isLoading: locationWeatherQuery.isLoading,
  };
}
