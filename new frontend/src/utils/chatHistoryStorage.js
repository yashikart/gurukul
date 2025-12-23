/**
 * Chat History Storage Utility
 * Manages persistent chat history using localStorage with compression and quota management
 * Supports multiple chat sessions and user authentication state changes
 */

import { safeSetItem } from './storageManager';
import chatErrorRecovery from './chatErrorRecovery';
import { translate } from '../store/languageSlice';

// Simple compression utilities (inline implementation)
const compressData = (data) => {
  try {
    if (typeof data !== 'object' || data === null) {
      return JSON.stringify(data);
    }

    // Simple compression by removing unnecessary fields and compacting data
    const compressed = JSON.stringify(data, (key, value) => {
      // Round numbers to reduce precision
      if (typeof value === 'number' && !Number.isInteger(value)) {
        return Math.round(value * 100) / 100;
      }
      return value;
    });
    return compressed;
  } catch (error) {
    console.warn('Failed to compress data:', error);
    try {
      return JSON.stringify(data);
    } catch (stringifyError) {
      console.error('Failed to stringify data as fallback:', stringifyError);
      return '{}';
    }
  }
};

const decompressData = (compressedData) => {
  try {
    return JSON.parse(compressedData);
  } catch (error) {
    console.warn('Failed to decompress data:', error);
    return null;
  }
};

// Storage keys
const CHAT_HISTORY_KEY = 'gurukul_chat_history';
const CHAT_SESSIONS_KEY = 'gurukul_chat_sessions';
const CHAT_SETTINGS_KEY = 'gurukul_chat_settings';

// Default settings
const DEFAULT_SETTINGS = {
  maxMessagesPerSession: 100,
  maxSessions: 10,
  autoSave: true,
  compressionEnabled: true,
};

// Welcome message variations for first-time users - always start with proper introduction
const WELCOME_MESSAGES = [
  '🙏🏽 Namaste! I\'m Gurukul, your AI learning companion. How can I assist you with your learning journey today?',
  '🙏🏽 Namaste! I am Gurukul, your personal AI guide to ancient wisdom and modern learning. What knowledge are you seeking today?',
  '🙏🏽 Namaste! Welcome to Gurukul. I\'m your AI learning assistant, here to help you explore the depths of knowledge. How can I guide you today?',
  '🙏🏽 Namaste! I\'m Gurukul, your dedicated AI companion for learning and wisdom. What would you like to discover today?',
  '🙏🏽 Namaste! Greetings from Gurukul, your AI learning guide. I\'m here to assist you on your educational journey. How can I help you today?',
];

// Function to get a contextual welcome message
const getWelcomeMessage = (isReturningUser = false, lastSessionTime = null, hasRealConversation = false) => {
  let message;

  // If there's no real conversation history, always treat as first-time user
  if (!hasRealConversation) {
    // No real conversation - use first-time Gurukul introduction
    const rawMessage = WELCOME_MESSAGES[Math.floor(Math.random() * WELCOME_MESSAGES.length)];
    message = translate(rawMessage);
  } else if (isReturningUser && lastSessionTime) {
    const timeDiff = Date.now() - new Date(lastSessionTime).getTime();
    const hoursDiff = timeDiff / (1000 * 60 * 60);

    // User has real conversation history - use continuation messages
    if (hoursDiff < 1) {
      message = translate('👋 Welcome back! Ready to continue our conversation?');
    } else if (hoursDiff < 24) {
      message = translate('🌅 Good to see you again! What would you like to explore today?');
    } else {
      message = translate('🌟 Welcome back! It\'s been a while. What new topics are you interested in learning about?');
    }
  } else {
    // First time or new session - use random welcome message with proper Gurukul introduction
    const rawMessage = WELCOME_MESSAGES[Math.floor(Math.random() * WELCOME_MESSAGES.length)];
    message = translate(rawMessage);
  }

  return {
    id: `welcome-${Date.now()}`,
    role: 'assistant',
    content: message,
    model: 'grok',
    timestamp: new Date().toISOString(),
    isWelcome: true,
  };
};

// Default welcome message (fallback)
const DEFAULT_WELCOME_MESSAGE = getWelcomeMessage();

class ChatHistoryStorage {
  constructor() {
    this.settings = this.loadSettings();
    this.currentSessionId = null;
    this.isInitialized = false;
  }

  /**
   * Initialize the chat history storage
   */
  async init(userId = 'guest-user') {
    try {
      this.currentSessionId = this.generateSessionId(userId);
      this.isInitialized = true;
      
      // Ensure we have a current session
      await this.ensureCurrentSession();
      
      console.log('✅ Chat history storage initialized for user:', userId);
      return true;
    } catch (error) {
      console.error('❌ Failed to initialize chat history storage:', error);
      return false;
    }
  }

  /**
   * Generate a session ID based on user and timestamp
   */
  generateSessionId(userId) {
    const timestamp = new Date().toISOString().split('T')[0]; // YYYY-MM-DD
    const timeId = Date.now().toString().slice(-6); // Last 6 digits for uniqueness
    return `${userId}_${timestamp}_${timeId}`;
  }

  /**
   * Load chat settings from localStorage
   */
  loadSettings() {
    try {
      const stored = localStorage.getItem(CHAT_SETTINGS_KEY);
      if (stored) {
        const settings = JSON.parse(stored);
        return { ...DEFAULT_SETTINGS, ...settings };
      }
    } catch (error) {
      console.warn('Failed to load chat settings:', error);
    }
    return DEFAULT_SETTINGS;
  }

  /**
   * Save chat settings to localStorage
   */
  async saveSettings(newSettings) {
    try {
      this.settings = { ...this.settings, ...newSettings };
      const result = await safeSetItem(CHAT_SETTINGS_KEY, JSON.stringify(this.settings));
      return result.success;
    } catch (error) {
      console.error('Failed to save chat settings:', error);
      return false;
    }
  }

  /**
   * Load all chat sessions from localStorage with error recovery
   */
  loadSessions() {
    try {
      const stored = localStorage.getItem(CHAT_SESSIONS_KEY);
      if (stored) {
        try {
          const compressed = JSON.parse(stored);
          const decompressed = this.settings.compressionEnabled ? decompressData(compressed) : compressed;

          // Validate the loaded data
          if (typeof decompressed === 'object' && decompressed !== null) {
            return decompressed;
          } else {
            throw new Error('Invalid session data structure');
          }
        } catch (parseError) {
          console.warn('Failed to parse stored sessions, attempting recovery:', parseError);

          // Attempt to recover corrupted data
          chatErrorRecovery.handleError(parseError, 'loadSessions');

          // Return empty sessions to start fresh
          return {};
        }
      }
    } catch (error) {
      console.warn('Failed to load chat sessions:', error);
      chatErrorRecovery.handleError(error, 'loadSessions');
    }
    return {};
  }

  /**
   * Save all chat sessions to localStorage with error recovery
   */
  async saveSessions(sessions) {
    try {
      const dataToStore = this.settings.compressionEnabled ? compressData(sessions) : sessions;
      const result = await safeSetItem(CHAT_SESSIONS_KEY, JSON.stringify(dataToStore));

      if (!result.success) {
        // Attempt error recovery
        const recovered = await chatErrorRecovery.handleError(
          new Error(result.error || 'Failed to save sessions'),
          'saveSessions'
        );

        if (recovered) {
          // Retry after recovery
          const retryResult = await safeSetItem(CHAT_SESSIONS_KEY, JSON.stringify(dataToStore));
          return retryResult.success;
        }

        return false;
      }

      return true;
    } catch (error) {
      console.error('Failed to save chat sessions:', error);

      // Attempt error recovery
      const recovered = await chatErrorRecovery.handleError(error, 'saveSessions');

      if (recovered) {
        // Retry after recovery
        try {
          const dataToStore = this.settings.compressionEnabled ? compressData(sessions) : sessions;
          const retryResult = await safeSetItem(CHAT_SESSIONS_KEY, JSON.stringify(dataToStore));
          return retryResult.success;
        } catch (retryError) {
          console.error('Retry failed after recovery:', retryError);
        }
      }

      return false;
    }
  }

  /**
   * Load chat history for current session
   */
  loadChatHistory() {
    if (!this.isInitialized) {
      console.warn('Chat history storage not initialized');
      return [this.getContextualWelcomeMessage()];
    }

    try {
      const sessions = this.loadSessions();
      const sessionHistory = sessions[this.currentSessionId];

      if (sessionHistory && Array.isArray(sessionHistory.messages)) {
        // Filter out any invalid messages and ensure proper structure
        const validMessages = sessionHistory.messages.filter(msg =>
          msg && typeof msg === 'object' && msg.role && msg.content
        );

        // Check if this is a returning user (has session history)
        const isReturningUser = true; // If we have sessionHistory, user has been here before
        const lastSessionTime = sessionHistory.lastUpdated;

        // If we have valid messages, check if we need to update the welcome message
        if (validMessages.length > 0) {
          const hasWelcomeMessage = validMessages.some(msg => msg.isWelcome);

          if (!hasWelcomeMessage) {
            // Add contextual welcome message at the beginning
            const welcomeMessage = this.getContextualWelcomeMessage(isReturningUser, lastSessionTime, validMessages);
            return [welcomeMessage, ...validMessages];
          }

          // If it's a returning user and the welcome message is old, update it
          if (isReturningUser && hasWelcomeMessage) {
            const welcomeIndex = validMessages.findIndex(msg => msg.isWelcome);
            if (welcomeIndex !== -1) {
              const welcomeMessage = validMessages[welcomeIndex];
              const welcomeAge = Date.now() - new Date(welcomeMessage.timestamp).getTime();

              // If welcome message is older than 1 hour, update it
              if (welcomeAge > 60 * 60 * 1000) {
                const newWelcomeMessage = this.getContextualWelcomeMessage(true, lastSessionTime, validMessages);
                validMessages[welcomeIndex] = newWelcomeMessage;
              }
            }
          }

          return validMessages;
        }
      }
    } catch (error) {
      console.warn('Failed to load chat history:', error);
    }

    return [this.getContextualWelcomeMessage()];
  }

  /**
   * Get contextual welcome message based on user history
   */
  getContextualWelcomeMessage(isReturningUser = false, lastSessionTime = null, existingMessages = []) {
    // Check if there's real conversation history (messages that aren't welcome messages)
    let hasRealConversation = false;

    if (existingMessages.length > 0) {
      // Check if there are any non-welcome messages in the provided messages
      hasRealConversation = existingMessages.some(msg => !msg.isWelcome);
    }

    return getWelcomeMessage(isReturningUser, lastSessionTime, hasRealConversation);
  }

  /**
   * Save chat history for current session
   */
  async saveChatHistory(messages) {
    if (!this.isInitialized || !this.settings.autoSave) {
      return false;
    }

    try {
      const sessions = this.loadSessions();
      
      // Ensure we don't exceed max messages per session
      const trimmedMessages = messages.slice(-this.settings.maxMessagesPerSession);
      
      // Update current session
      sessions[this.currentSessionId] = {
        messages: trimmedMessages,
        lastUpdated: new Date().toISOString(),
        messageCount: trimmedMessages.length,
      };

      // Clean up old sessions if we exceed max sessions
      await this.cleanupOldSessions(sessions);
      
      return await this.saveSessions(sessions);
    } catch (error) {
      console.error('Failed to save chat history:', error);
      return false;
    }
  }

  /**
   * Add a single message to chat history
   */
  async addMessage(message) {
    if (!this.isInitialized) {
      console.warn('Chat history storage not initialized');
      return false;
    }

    try {
      const currentHistory = this.loadChatHistory();
      const newMessage = {
        id: message.id || `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        role: message.role,
        content: message.content,
        model: message.model || 'grok',
        timestamp: message.timestamp || new Date().toISOString(),
        ...message,
      };
      
      const updatedHistory = [...currentHistory, newMessage];
      return await this.saveChatHistory(updatedHistory);
    } catch (error) {
      console.error('Failed to add message to chat history:', error);
      return false;
    }
  }

  /**
   * Clear chat history for current session
   */
  async clearCurrentSession() {
    if (!this.isInitialized) {
      return false;
    }

    try {
      const sessions = this.loadSessions();
      delete sessions[this.currentSessionId];
      await this.saveSessions(sessions);
      return true;
    } catch (error) {
      console.error('Failed to clear current session:', error);
      return false;
    }
  }

  /**
   * Clear all chat history
   */
  async clearAllHistory() {
    try {
      localStorage.removeItem(CHAT_SESSIONS_KEY);
      return true;
    } catch (error) {
      console.error('Failed to clear all chat history:', error);
      return false;
    }
  }

  /**
   * Get chat statistics
   */
  getChatStats() {
    try {
      const sessions = this.loadSessions();
      const sessionCount = Object.keys(sessions).length;
      const totalMessages = Object.values(sessions).reduce(
        (total, session) => total + (session.messageCount || 0), 
        0
      );
      
      return {
        sessionCount,
        totalMessages,
        currentSessionId: this.currentSessionId,
        storageSize: this.getStorageSize(),
      };
    } catch (error) {
      console.error('Failed to get chat stats:', error);
      return {
        sessionCount: 0,
        totalMessages: 0,
        currentSessionId: this.currentSessionId,
        storageSize: 0,
      };
    }
  }

  /**
   * Get storage size in bytes
   */
  getStorageSize() {
    try {
      const sessions = localStorage.getItem(CHAT_SESSIONS_KEY) || '';
      const settings = localStorage.getItem(CHAT_SETTINGS_KEY) || '';
      return sessions.length + settings.length;
    } catch (error) {
      return 0;
    }
  }

  /**
   * Ensure current session exists
   */
  async ensureCurrentSession() {
    const sessions = this.loadSessions();
    if (!sessions[this.currentSessionId]) {
      // Check if user has previous sessions to determine if they're returning
      const userId = this.currentSessionId ? this.currentSessionId.split('_')[0] : 'guest-user';
      const userSessions = Object.keys(sessions).filter(key => key.startsWith(userId + '_'));
      const isReturningUser = userSessions.length > 0;

      // Get the most recent session time for context
      let lastSessionTime = null;
      if (isReturningUser) {
        const recentSessions = userSessions
          .map(key => sessions[key])
          .filter(session => session.lastUpdated)
          .sort((a, b) => new Date(b.lastUpdated) - new Date(a.lastUpdated));

        if (recentSessions.length > 0) {
          lastSessionTime = recentSessions[0].lastUpdated;
        }
      }

      const welcomeMessage = this.getContextualWelcomeMessage(isReturningUser, lastSessionTime);

      sessions[this.currentSessionId] = {
        messages: [welcomeMessage],
        lastUpdated: new Date().toISOString(),
        messageCount: 1,
      };
      await this.saveSessions(sessions);
    }
  }

  /**
   * Clean up old sessions to maintain max session limit
   */
  async cleanupOldSessions(sessions) {
    const sessionKeys = Object.keys(sessions);
    if (sessionKeys.length <= this.settings.maxSessions) {
      return;
    }

    // Sort sessions by last updated date (oldest first)
    const sortedSessions = sessionKeys
      .map(key => ({ key, lastUpdated: sessions[key].lastUpdated }))
      .sort((a, b) => new Date(a.lastUpdated) - new Date(b.lastUpdated));

    // Remove oldest sessions
    const sessionsToRemove = sortedSessions.slice(0, sessionKeys.length - this.settings.maxSessions);
    sessionsToRemove.forEach(session => {
      delete sessions[session.key];
    });

    console.log(`🧹 Cleaned up ${sessionsToRemove.length} old chat sessions`);
  }



  /**
   * Get all available sessions for current user
   */
  getAllSessions() {
    try {
      const sessions = this.loadSessions();
      const currentUserPrefix = this.currentSessionId ? this.currentSessionId.split('_')[0] : 'guest-user';

      return Object.entries(sessions)
        .filter(([sessionId]) => sessionId.startsWith(currentUserPrefix))
        .map(([sessionId, sessionData]) => ({
          id: sessionId,
          date: sessionId.split('_')[1] || 'unknown',
          messageCount: sessionData.messageCount || 0,
          lastUpdated: sessionData.lastUpdated,
          preview: this.getSessionPreview(sessionData.messages),
        }))
        .sort((a, b) => new Date(b.lastUpdated) - new Date(a.lastUpdated));
    } catch (error) {
      console.error('Failed to get all sessions:', error);
      return [];
    }
  }

  /**
   * Get a preview of the session (first user message)
   */
  getSessionPreview(messages) {
    if (!Array.isArray(messages)) return 'Empty session';

    const firstUserMessage = messages.find(msg => msg.role === 'user' && !msg.isWelcome);
    if (firstUserMessage) {
      const content = typeof firstUserMessage.content === 'string'
        ? firstUserMessage.content
        : 'Message';
      return content.length > 50 ? content.substring(0, 50) + '...' : content;
    }

    return 'New conversation';
  }

  /**
   * Switch to a different session
   */
  async switchToSession(sessionId) {
    try {
      if (!sessionId) return false;

      this.currentSessionId = sessionId;

      // Ensure the session exists
      await this.ensureCurrentSession();

      console.log('✅ Switched to session:', sessionId);
      return true;
    } catch (error) {
      console.error('Failed to switch session:', error);
      return false;
    }
  }

  /**
   * Create a new session for current user
   */
  async createNewSession() {
    try {
      const userId = this.currentSessionId ? this.currentSessionId.split('_')[0] : 'guest-user';
      const timestamp = new Date().toISOString().split('T')[0];
      const timeId = Date.now().toString().slice(-6); // Last 6 digits for uniqueness

      const newSessionId = `${userId}_${timestamp}_${timeId}`;
      this.currentSessionId = newSessionId;

      // Create the new session
      await this.ensureCurrentSession();

      console.log('✅ Created new session:', newSessionId);
      return newSessionId;
    } catch (error) {
      console.error('Failed to create new session:', error);
      return null;
    }
  }

  /**
   * Delete a specific session
   */
  async deleteSession(sessionId) {
    try {
      if (!sessionId || sessionId === this.currentSessionId) {
        return false; // Can't delete current session
      }

      const sessions = this.loadSessions();
      delete sessions[sessionId];

      await this.saveSessions(sessions);

      console.log('✅ Deleted session:', sessionId);
      return true;
    } catch (error) {
      console.error('Failed to delete session:', error);
      return false;
    }
  }

  /**
   * Get current session info
   */
  getCurrentSessionInfo() {
    try {
      const sessions = this.loadSessions();
      const currentSession = sessions[this.currentSessionId];

      if (currentSession) {
        return {
          id: this.currentSessionId,
          messageCount: currentSession.messageCount || 0,
          lastUpdated: currentSession.lastUpdated,
          preview: this.getSessionPreview(currentSession.messages),
        };
      }

      return null;
    } catch (error) {
      console.error('Failed to get current session info:', error);
      return null;
    }
  }

  /**
   * Get chat statistics
   */
  getChatStats() {
    try {
      const sessions = this.loadSessions();
      const currentUserId = this.currentSessionId?.split('_')[0] || 'guest-user';

      // Filter sessions for current user
      const userSessions = Object.entries(sessions)
        .filter(([sessionId]) => sessionId.startsWith(currentUserId));

      const sessionCount = userSessions.length;

      let totalMessages = 0;
      userSessions.forEach(([, session]) => {
        totalMessages += session.messageCount || 0;
      });

      // Calculate storage size
      const historySize = this.getStorageSize(CHAT_HISTORY_KEY);
      const sessionsSize = this.getStorageSize(CHAT_SESSIONS_KEY);
      const settingsSize = this.getStorageSize(CHAT_SETTINGS_KEY);
      const storageSize = historySize + sessionsSize + settingsSize;

      return {
        sessionCount,
        totalMessages,
        storageSize,
      };
    } catch (error) {
      console.error('Failed to get chat stats:', error);
      return {
        sessionCount: 0,
        totalMessages: 0,
        storageSize: 0,
      };
    }
  }
}

// Create singleton instance
const chatHistoryStorage = new ChatHistoryStorage();

export default chatHistoryStorage;

// Export utility functions
export {
  DEFAULT_WELCOME_MESSAGE,
  CHAT_HISTORY_KEY,
  CHAT_SESSIONS_KEY,
  CHAT_SETTINGS_KEY,
};
