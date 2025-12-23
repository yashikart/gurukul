import React, { useState, useEffect, useRef } from "react";
import GlassContainer from "../components/GlassContainer";
import { supabase } from "../supabaseClient";
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
  Quote,
} from "lucide-react";
import GlassButton from "../components/GlassButton";
import { useTimeTracking } from "../hooks/useTimeTracking";
import toast from "react-hot-toast";
import { useQuery } from "@tanstack/react-query";
import KarmaWidget from "../components/KarmaWidget";
import { useTranslation } from "react-i18next";

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
  const { t } = useTranslation();
  const { totalTimeToday, currentSessionTime, isLoading, timeHistory } =
    useTimeTracking();
  const [error, setError] = useState(null);
  const [dailyGoal, setDailyGoal] = useState(0);
  const [isSettingGoal, setIsSettingGoal] = useState(false);
  const [goalInput, setGoalInput] = useState({ hours: 0, minutes: 0 });
  const [user, setUser] = useState(null);
  const subscriptionRef = useRef(null);
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
        // Get user from Supabase session
        const { data: { session } } = await supabase.auth.getSession();
        if (!session) throw new Error("Not signed in");

        // Set user data
        setUser({
          id: session.user.id,
          email: session.user.email,
          user_metadata: {
            avatar_url: session.user.user_metadata?.avatar_url || null,
            full_name: session.user.user_metadata?.full_name || session.user.email || null,
          },
        });

        const userId = session.user.id;

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
  }, []);

  const handleSaveGoal = async () => {
    try {
      // Get user from Supabase session
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) throw new Error("Not signed in");

      const totalSeconds = goalInput.hours * 3600 + goalInput.minutes * 60;
      const { error } = await supabase.from("user_goals").upsert({
        user_id: session.user.id,
        daily_goal_seconds: totalSeconds,
      });

      if (error) throw error;

      setDailyGoal(totalSeconds);
      setIsSettingGoal(false);
      toast.success(t("Daily goal updated successfully!"));
    } catch (err) {
      console.error("Error saving goal:", err);
      toast.error(t("Failed to save goal"));
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
      label: t("First Day Completed"),
      unlocked: stats.daysActive >= 1,
    },
    {
      icon: <TrendingUp className="text-[#FF9933] mr-2" />,
      label: t("Week Warrior"),
      unlocked: stats.week > 0,
    },
    {
      icon: <Target className="text-[#4ade80] mr-2" />,
      label: t("Goal Crusher"),
      unlocked: percentageComplete >= 100,
    },
    {
      icon: <Award className="text-[#60a5fa] mr-2" />,
      label: t("Streak Master"),
      unlocked: stats.bestStreak >= 7,
    },
  ];

  // Format date string
  useEffect(() => {
    const now = new Date();
    const language = localStorage.getItem("gurukul_settings") 
      ? JSON.parse(localStorage.getItem("gurukul_settings")).language || "english"
      : "english";
    
    // Map language codes to locale strings
    const localeMap = {
      english: "en-US",
      hindi: "hi-IN",
      marathi: "mr-IN",
      arabic: "ar-SA"
    };
    
    const options = { weekday: "long", year: "numeric", month: "long", day: "numeric" };
    setDateString(now.toLocaleDateString(localeMap[language] || "en-US", options));
  }, []);

  // Get random fact
  useEffect(() => {
    const facts = [
      t("The human brain processes images seen by the eye in just 13 milliseconds."),
      t("Learning a new skill increases neural pathways in your brain."),
      t("Regular study sessions improve long-term memory retention by up to 50%."),
      t("The average person spends 5 years of their life waiting in lines."),
      t("Reading for just 30 minutes a day can expand your vocabulary by 1000+ words per year."),
      t("The most productive time for learning is typically between 10 AM and 2 PM."),
      t("Taking short breaks during study sessions can improve focus by up to 40%."),
      t("Students who take handwritten notes retain information better than those who type."),
    ];
    setRandomFact(facts[Math.floor(Math.random() * facts.length)]);
  }, [t]);

  if (error) {
    return (
      <GlassContainer>
        <div className="text-center py-12">
          <div className="text-red-400 text-xl mb-4">{t("Error loading dashboard")}</div>
          <div className="text-gray-300 mb-6">{error}</div>
          <GlassButton onClick={() => window.location.reload()}>
            {t("Reload Page")}
          </GlassButton>
        </div>
      </GlassContainer>
    );
  }

  return (
    <GlassContainer>
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">{t("Dashboard")}</h1>
        <p className="text-gray-300">{dateString}</p>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-6 mb-8">
        <DashboardTile
          icon={<Clock className="text-blue-400" />}
          title={t("Today's Study Time")}
        >
          <div className="text-3xl font-bold text-[#FF9933] mb-2">
            {displayTime}
          </div>
          <div className="w-full bg-gray-700 rounded-full h-2.5">
            <div
              className="bg-[#FF9933] h-2.5 rounded-full"
              style={{ width: `${percentageComplete}%` }}
            ></div>
          </div>
          <div className="text-sm text-gray-400 mt-2">
            {Math.round(percentageComplete)}% {t("of daily goal")}
          </div>
        </DashboardTile>

        <DashboardTile
          icon={<Target className="text-green-400" />}
          title={t("This Week")}
        >
          <div className="text-3xl font-bold text-green-400 mb-2">
            {formatDuration(stats.week)}
          </div>
          <div className="text-sm text-gray-400">
            {stats.daysActive} {t("active days")}
          </div>
        </DashboardTile>

        <DashboardTile
          icon={<Calendar className="text-purple-400" />}
          title={t("This Month")}
        >
          <div className="text-3xl font-bold text-purple-400 mb-2">
            {formatDuration(stats.month)}
          </div>
          <div className="text-sm text-gray-400">
            {t("Best streak")}: {stats.bestStreak} {t("days")}
          </div>
        </DashboardTile>

        {/* Karma Widget */}
        <KarmaWidget />

        <DashboardTile
          icon={<Zap className="text-yellow-400" />}
          title={t("Achievements")}
        >
          <div className="space-y-3">
            {achievements.map((achievement, index) => (
              <div key={index} className="flex items-center">
                {achievement.icon}
                <span
                  className={`text-sm ${
                    achievement.unlocked ? "text-white" : "text-gray-500"
                  }`}
                >
                  {achievement.label}
                </span>
                {achievement.unlocked && (
                  <ChevronUp className="ml-auto text-green-400" size={16} />
                )}
              </div>
            ))}
          </div>
        </DashboardTile>
      </div>

      {/* Goal Setting */}
      <div className="mb-8">
          <DashboardTile
            icon={<Trophy className="text-[#FFD700]" />}
            title={t("Daily Goal")}
            className="h-full"
          >
            {isSettingGoal ? (
              <div className="space-y-4">
                <div className="flex items-center space-x-4">
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">
                      {t("Hours")}
                    </label>
                    <input
                      type="number"
                      min="0"
                      max="24"
                      value={goalInput.hours}
                      onChange={(e) =>
                        setGoalInput({
                          ...goalInput,
                          hours: parseInt(e.target.value) || 0,
                        })
                      }
                      className="w-20 bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">
                      {t("Minutes")}
                    </label>
                    <input
                      type="number"
                      min="0"
                      max="59"
                      value={goalInput.minutes}
                      onChange={(e) =>
                        setGoalInput({
                          ...goalInput,
                          minutes: parseInt(e.target.value) || 0,
                        })
                      }
                      className="w-20 bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white"
                    />
                  </div>
                </div>
                <div className="flex space-x-3">
                  <GlassButton onClick={handleSaveGoal} variant="primary">
                    {t("Save")}
                  </GlassButton>
                  <GlassButton
                    onClick={() => setIsSettingGoal(false)}
                    variant="secondary"
                  >
                    {t("Cancel")}
                  </GlassButton>
                </div>
              </div>
            ) : (
              <div className="text-center">
                <div className="text-2xl font-bold text-white mb-4">
                  {formatDuration(dailyGoal)}
                </div>
                <GlassButton
                  onClick={() => setIsSettingGoal(true)}
                  variant="primary"
                >
                  {t("Set New Goal")}
                </GlassButton>
              </div>
            )}
        </DashboardTile>
      </div>

      {/* Quote and Fact Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Motivational Quote */}
        <DashboardTile
          icon={<Quote className="text-[#FFD700]" />}
          title={t("Motivational Quote")}
        >
          {quoteLoading ? (
            <div className="flex justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-[#FF9933]"></div>
            </div>
          ) : (
            <div className="text-center">
              <div className="text-lg italic text-white mb-4">
                "{quoteData?.q ? t(quoteData.q) || quoteData.q : t("Keep learning, keep growing!")}"
              </div>
            </div>
          )}
        </DashboardTile>

        {/* Did You Know? */}
        <DashboardTile
          icon={<Award className="text-blue-400" />}
          title={t("Did You Know?")}
        >
          <div className="text-center">
            <div className="text-lg text-white">
              {randomFact || t("Learning is the best investment you can make!")}
            </div>
          </div>
        </DashboardTile>
      </div>
    </GlassContainer>
  );
}