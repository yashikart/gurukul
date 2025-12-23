import React, { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Sparkles } from 'lucide-react';
import { getKarma } from '../utils/karmaManager';
import { useSelector } from 'react-redux';
import { selectUser } from '../store/authSlice';
import { useTranslation } from 'react-i18next';

const KarmaWidget = ({ onKarmaChange }) => {
  const { t } = useTranslation();
  const user = useSelector(selectUser);
  const userId = user?.id || user?.user_id || 'guest';
  
  const [karma, setKarma] = useState(() => getKarma(userId));
  const [recentChange, setRecentChange] = useState(null);
  const [showAnimation, setShowAnimation] = useState(false);

  // Listen for karma changes from other components
  useEffect(() => {
    const handleKarmaUpdate = () => {
      const updatedKarma = getKarma(userId);
      setKarma(updatedKarma);
    };

    // Check for karma updates every second
    const interval = setInterval(handleKarmaUpdate, 1000);
    
    return () => clearInterval(interval);
  }, [userId]);

  // Listen for custom karma change events
  useEffect(() => {
    const handleKarmaChangeEvent = (event) => {
      const { change, reason } = event.detail;
      setRecentChange({ change, reason });
      setShowAnimation(true);
      
      // Update karma
      const updatedKarma = getKarma(userId);
      setKarma(updatedKarma);
      
      // Hide animation after 3 seconds
      setTimeout(() => {
        setShowAnimation(false);
        setRecentChange(null);
      }, 3000);
    };

    window.addEventListener('karmaChanged', handleKarmaChangeEvent);
    return () => window.removeEventListener('karmaChanged', handleKarmaChangeEvent);
  }, [userId]);

  const getKarmaColor = () => {
    if (karma.karma >= 150) return 'text-green-400';
    if (karma.karma >= 100) return 'text-blue-400';
    if (karma.karma >= 50) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getKarmaLevel = () => {
    if (karma.karma >= 150) return t('Excellent');
    if (karma.karma >= 100) return t('Good');
    if (karma.karma >= 50) return t('Fair');
    return t('Needs Improvement');
  };

  return (
    <div className="relative">
      <div className="bg-gradient-to-br from-purple-900/30 to-indigo-900/30 backdrop-blur-lg rounded-xl p-4 border border-purple-500/20 shadow-lg">
        {/* Header */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-purple-400" />
            <h3 className="text-lg font-semibold text-white">{t("Karma")}</h3>
          </div>
          <span className={`text-xs px-2 py-1 rounded-full ${getKarmaColor()} bg-opacity-20`}>
            {getKarmaLevel()}
          </span>
        </div>

        {/* Karma Score */}
        <div className="relative">
          <div className={`text-4xl font-bold ${getKarmaColor()} mb-2 transition-all duration-300 ${showAnimation ? 'scale-110' : 'scale-100'}`}>
            {karma.karma}
          </div>
          
          {/* Change Animation */}
          {recentChange && showAnimation && (
            <div className={`absolute top-0 right-0 flex items-center gap-1 text-sm font-semibold animate-bounce ${
              recentChange.change > 0 ? 'text-green-400' : 'text-red-400'
            }`}>
              {recentChange.change > 0 ? (
                <TrendingUp className="w-4 h-4" />
              ) : (
                <TrendingDown className="w-4 h-4" />
              )}
              {recentChange.change > 0 ? '+' : ''}{recentChange.change}
            </div>
          )}
        </div>

        {/* Stats */}
        <div className="mt-4 pt-3 border-t border-purple-500/20">
          <div className="flex justify-between text-xs text-gray-400 mb-2">
            <span>{t("Dharma Points")}</span>
            <span className="text-green-400">{karma.dharmaPoints}</span>
          </div>
          <div className="flex justify-between text-xs text-gray-400">
            <span>{t("Positive Actions")}</span>
            <span className="text-green-400">+{karma.totalPositive}</span>
          </div>
          <div className="flex justify-between text-xs text-gray-400 mt-1">
            <span>{t("Negative Actions")}</span>
            <span className="text-red-400">-{karma.totalNegative}</span>
          </div>
        </div>

        {/* Recent Change Reason */}
        {recentChange && showAnimation && (
          <div className="mt-3 pt-3 border-t border-purple-500/20">
            <p className="text-xs text-gray-300 italic">
              {recentChange.reason}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default KarmaWidget;

