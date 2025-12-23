/**
 * Frontend-only Karma Manager
 * Manages karma state using localStorage (no backend required)
 */

const KARMA_STORAGE_KEY = 'gurukul_karma';
const KARMA_HISTORY_KEY = 'gurukul_karma_history';

// Curse words and inappropriate content detection
const CURSE_WORDS = [
  'damn', 'hell', 'shit', 'fuck', 'ass', 'bitch', 'bastard', 'crap',
  'stupid', 'idiot', 'moron', 'retard', 'hate', 'kill', 'die'
];

// Check if message contains inappropriate content
export const detectInappropriateContent = (message) => {
  const lowerMessage = message.toLowerCase();
  return CURSE_WORDS.some(word => lowerMessage.includes(word));
};

// Initialize karma for user
export const initializeKarma = (userId) => {
  const stored = localStorage.getItem(`${KARMA_STORAGE_KEY}_${userId}`);
  if (stored) {
    return JSON.parse(stored);
  }
  
  const initialKarma = {
    userId,
    karma: 100, // Start with 100 karma points
    dharmaPoints: 0,
    totalPositive: 0,
    totalNegative: 0,
    lastUpdated: new Date().toISOString()
  };
  
  saveKarma(userId, initialKarma);
  return initialKarma;
};

// Get karma for user
export const getKarma = (userId) => {
  const stored = localStorage.getItem(`${KARMA_STORAGE_KEY}_${userId}`);
  if (stored) {
    return JSON.parse(stored);
  }
  return initializeKarma(userId);
};

// Save karma to localStorage
export const saveKarma = (userId, karmaData) => {
  karmaData.lastUpdated = new Date().toISOString();
  localStorage.setItem(`${KARMA_STORAGE_KEY}_${userId}`, JSON.stringify(karmaData));
  
  // Also save to history
  addToHistory(userId, karmaData.karma);
};

// Add karma (positive action)
export const addKarma = (userId, amount = 5, reason = 'Good interaction') => {
  const karma = getKarma(userId);
  karma.karma = Math.max(0, karma.karma + amount);
  karma.dharmaPoints += amount;
  karma.totalPositive += amount;
  
  saveKarma(userId, karma);
  
  // Return change info for UI feedback
  return {
    change: amount,
    newKarma: karma.karma,
    reason
  };
};

// Subtract karma (negative action)
export const subtractKarma = (userId, amount = 10, reason = 'Inappropriate behavior') => {
  const karma = getKarma(userId);
  karma.karma = Math.max(0, karma.karma - amount);
  karma.totalNegative += amount;
  
  saveKarma(userId, karma);
  
  // Return change info for UI feedback
  return {
    change: -amount,
    newKarma: karma.karma,
    reason
  };
};

// Get karma history
export const getKarmaHistory = (userId, limit = 20) => {
  const stored = localStorage.getItem(`${KARMA_HISTORY_KEY}_${userId}`);
  if (stored) {
    const history = JSON.parse(stored);
    return history.slice(-limit);
  }
  return [];
};

// Add entry to history
const addToHistory = (userId, karmaValue) => {
  const stored = localStorage.getItem(`${KARMA_HISTORY_KEY}_${userId}`);
  const history = stored ? JSON.parse(stored) : [];
  
  history.push({
    karma: karmaValue,
    timestamp: new Date().toISOString()
  });
  
  // Keep only last 100 entries
  if (history.length > 100) {
    history.shift();
  }
  
  localStorage.setItem(`${KARMA_HISTORY_KEY}_${userId}`, JSON.stringify(history));
};

// Process chatbot message and update karma
export const processChatbotMessage = (userId, message) => {
  if (!message || message.trim().length === 0) {
    return null;
  }
  
  // Check for inappropriate content
  if (detectInappropriateContent(message)) {
    return subtractKarma(userId, 10, 'Used inappropriate language');
  }
  
  // Good interaction - using chatbot properly
  return addKarma(userId, 5, 'Used chatbot');
};

// Process summarizer usage (good action)
export const processSummarizerUsage = (userId) => {
  return addKarma(userId, 8, 'Used Summarizer');
};

// Process test result (pass = +karma, fail = -karma)
export const processTestResult = (userId, percentageScore) => {
  const passingScore = 50; // 50% is passing
  
  if (percentageScore >= passingScore) {
    // Passed the test
    const bonus = percentageScore >= 80 ? 15 : percentageScore >= 70 ? 12 : 10;
    return addKarma(userId, bonus, `Passed test with ${percentageScore}%`);
  } else {
    // Failed the test
    return subtractKarma(userId, 5, `Failed test with ${percentageScore}%`);
  }
};

// Process subjects/lessons usage (good action)
export const processSubjectsUsage = (userId) => {
  return addKarma(userId, 6, 'Accessed Subjects/Lessons');
};

// Process lectures usage (good action)
export const processLecturesUsage = (userId) => {
  return addKarma(userId, 6, 'Watched Lecture');
};

// Helper function to dispatch karma change event
export const dispatchKarmaChange = (karmaResult) => {
  if (karmaResult) {
    window.dispatchEvent(new CustomEvent('karmaChanged', {
      detail: karmaResult
    }));
  }
};

