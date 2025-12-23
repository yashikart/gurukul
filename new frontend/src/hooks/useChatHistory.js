/**
 * Chat History Management Hooks
 * Provides React hooks for managing persistent chat history with automatic saving
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { toast } from 'react-hot-toast';
import chatHistoryStorage, { DEFAULT_WELCOME_MESSAGE } from '../utils/chatHistoryStorage';
import chatErrorRecovery from '../utils/chatErrorRecovery';
import chatPerformanceOptimizer from '../utils/chatPerformanceOptimizer';
import { useAuth } from '../context/AuthContext';

/**
 * Main hook for managing chat history
 */
export const useChatHistory = () => {
  const { t } = useTranslation();
  const [messages, setMessages] = useState([DEFAULT_WELCOME_MESSAGE]);
  const [isLoading, setIsLoading] = useState(false);
  const [userId, setUserId] = useState(null);
  const [isInitialized, setIsInitialized] = useState(false);
  const [chatStats, setChatStats] = useState({
    sessionCount: 0,
    totalMessages: 0,
    storageSize: 0,
  });
  const [optimizedMessages, setOptimizedMessages] = useState([DEFAULT_WELCOME_MESSAGE]);

  // Use ref to track if we're currently saving to prevent race conditions
  const isSavingRef = useRef(false);
  const lastSaveRef = useRef(Date.now());

  // Create debounced save function
  const debouncedSave = useRef(null);

  /**
   * Initialize chat history storage and load existing history
   */
  const initializeChatHistory = useCallback(async (currentUserId) => {
    try {
      setIsLoading(true);
      
      // Initialize storage with current user ID
      const success = await chatHistoryStorage.init(currentUserId || 'guest-user');
      
      if (success) {
        // Load existing chat history
        const history = chatHistoryStorage.loadChatHistory();
        setMessages(history);
        
        // Update stats
        const stats = chatHistoryStorage.getChatStats();
        setChatStats(stats);
        
        setIsInitialized(true);
        console.log('✅ Chat history initialized with', history.length, 'messages');
      } else {
        console.warn('⚠️ Failed to initialize chat history, using default');
        setMessages([DEFAULT_WELCOME_MESSAGE]);
      }
    } catch (error) {
      console.error('❌ Error initializing chat history:', error);
      setMessages([DEFAULT_WELCOME_MESSAGE]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Save current messages to storage (optimized and debounced)
   */
  const saveToStorage = useCallback(async (messagesToSave) => {
    // Prevent concurrent saves
    if (isSavingRef.current) {
      return;
    }

    try {
      isSavingRef.current = true;

      // Optimize messages for storage
      const optimizedMessages = messagesToSave.map(msg =>
        chatPerformanceOptimizer.optimizeMessageForStorage(msg)
      );

      const success = await chatHistoryStorage.saveChatHistory(optimizedMessages);

      if (success) {
        // Update stats after successful save
        const stats = chatHistoryStorage.getChatStats();
        setChatStats(stats);
      }
    } catch (error) {
      console.error('Failed to save chat history:', error);
      chatErrorRecovery.handleError(error, 'saveToStorage');
    } finally {
      isSavingRef.current = false;
    }
  }, []);

  // Initialize debounced save function
  useEffect(() => {
    if (!debouncedSave.current) {
      debouncedSave.current = chatPerformanceOptimizer.createDebouncedSave(saveToStorage);
    }
  }, [saveToStorage]);

  /**
   * Add a new message to the chat history with error recovery
   */
  const addMessage = useCallback(async (message) => {
    try {
      const newMessage = {
        id: message.id || `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        role: message.role,
        content: message.content,
        model: message.model || 'grok',
        timestamp: message.timestamp || new Date().toISOString(),
        ...message,
      };

      setMessages(prev => {
        const updated = [...prev, newMessage];
        // Auto-save to storage with error handling
        if (isInitialized) {
          saveToStorage(updated).catch(error => {
            console.error('Failed to save message to storage:', error);
            chatErrorRecovery.handleError(error, 'addMessage');
          });
        }
        return updated;
      });

      return newMessage;
    } catch (error) {
      console.error('Failed to add message:', error);
      chatErrorRecovery.handleError(error, 'addMessage');

      // Still try to add the message to the UI even if storage fails
      const fallbackMessage = {
        id: `fallback_${Date.now()}`,
        role: message.role,
        content: message.content,
        model: message.model || 'grok',
        timestamp: new Date().toISOString(),
        ...message,
      };

      setMessages(prev => [...prev, fallbackMessage]);
      return fallbackMessage;
    }
  }, [isInitialized, saveToStorage]);

  /**
   * Update messages array and save to storage
   */
  const updateMessages = useCallback(async (newMessages) => {
    setMessages(newMessages);
    
    if (isInitialized) {
      await saveToStorage(newMessages);
    }
  }, [isInitialized, saveToStorage]);

  /**
   * Clear current chat session
   */
  const clearCurrentSession = useCallback(async () => {
    try {
      const success = await chatHistoryStorage.clearCurrentSession();
      
      if (success) {
        setMessages([DEFAULT_WELCOME_MESSAGE]);
        
        // Update stats
        const stats = chatHistoryStorage.getChatStats();
        setChatStats(stats);
        
        toast.success(t('Chat history cleared'), {
          duration: 2000,
          icon: '🧹',
        });
        
        return true;
      } else {
        throw new Error('Failed to clear session');
      }
    } catch (error) {
      console.error('Failed to clear chat session:', error);
      toast.error(t('Failed to clear chat history'), {
        duration: 3000,
        icon: '❌',
      });
      return false;
    }
  }, [t]);

  /**
   * Clear all chat history
   */
  const clearAllHistory = useCallback(async () => {
    try {
      const success = await chatHistoryStorage.clearAllHistory();
      
      if (success) {
        setMessages([DEFAULT_WELCOME_MESSAGE]);
        setChatStats({
          sessionCount: 0,
          totalMessages: 0,
          storageSize: 0,
        });
        
        toast.success(t('All chat history cleared'), {
          duration: 2000,
          icon: '🧹',
        });
        
        return true;
      } else {
        throw new Error('Failed to clear all history');
      }
    } catch (error) {
      console.error('Failed to clear all chat history:', error);
      toast.error(t('Failed to clear all chat history'), {
        duration: 3000,
        icon: '❌',
      });
      return false;
    }
  }, [t]);



  // Initialize on mount and when userId changes
  const { user } = useAuth();
  const isSignedIn = !!user;

  useEffect(() => {
    const currentUserId = isSignedIn && user ? user.id : 'guest-user';
    setUserId(currentUserId);
    initializeChatHistory(currentUserId);
  }, [initializeChatHistory, isSignedIn, user]);

  // Optimize messages for rendering when they change
  useEffect(() => {
    if (messages.length > 0) {
      const optimized = chatPerformanceOptimizer.optimizeMessagesForRendering(messages);
      setOptimizedMessages(optimized);
    }
  }, [messages]);

  // Auto-save when messages change (debounced)
  useEffect(() => {
    if (isInitialized && messages.length > 0 && debouncedSave.current) {
      debouncedSave.current(messages);
    }
  }, [messages, isInitialized]);



  /**
   * Get all sessions for current user (simplified)
   */
  const getAllSessions = useCallback(() => {
    if (!isInitialized) return [];
    return chatHistoryStorage.getAllSessions();
  }, [isInitialized]);

  /**
   * Switch to a different session
   */
  const switchToSession = useCallback(async (sessionId) => {
    try {
      const success = await chatHistoryStorage.switchToSession(sessionId);

      if (success) {
        // Reload messages for the new session
        const newMessages = chatHistoryStorage.loadChatHistory();
        setMessages(newMessages);

        // Update stats
        const stats = chatHistoryStorage.getChatStats();
        setChatStats(stats);

        toast.success(t('Switched to conversation'), {
          duration: 2000,
          icon: '💬',
        });

        return true;
      }
    } catch (error) {
      console.error('Failed to switch session:', error);
      toast.error(t('Failed to switch conversation'), {
        duration: 3000,
        icon: '❌',
      });
    }
    return false;
  }, [isInitialized, t]);

  /**
   * Create a new session
   */
  const createNewSession = useCallback(async () => {
    try {
      const newSessionId = await chatHistoryStorage.createNewSession();

      if (newSessionId) {
        // Load the new session (should have welcome message)
        const newMessages = chatHistoryStorage.loadChatHistory();
        setMessages(newMessages);

        // Update stats
        const stats = chatHistoryStorage.getChatStats();
        setChatStats(stats);

        toast.success(t('New conversation started'), {
          duration: 2000,
          icon: '✨',
        });

        return newSessionId;
      }
    } catch (error) {
      console.error('Failed to create new session:', error);
      toast.error(t('Failed to start new conversation'), {
        duration: 3000,
        icon: '❌',
      });
    }
    return null;
  }, [isInitialized, t]);

  /**
   * Delete a session
   */
  const deleteSession = useCallback(async (sessionId) => {
    try {
      const success = await chatHistoryStorage.deleteSession(sessionId);

      if (success) {
        // Update stats
        const stats = chatHistoryStorage.getChatStats();
        setChatStats(stats);

        toast.success(t('Conversation deleted'), {
          duration: 2000,
          icon: '🗑️',
        });

        return true;
      }
    } catch (error) {
      console.error('Failed to delete session:', error);
      toast.error(t('Failed to delete conversation'), {
        duration: 3000,
        icon: '❌',
      });
    }
    return false;
  }, [isInitialized, t]);

  /**
   * Get current session info
   */
  const getCurrentSessionInfo = useCallback(() => {
    if (!isInitialized) return null;
    return chatHistoryStorage.getCurrentSessionInfo();
  }, [isInitialized]);

  return {
    // State
    messages: optimizedMessages, // Return optimized messages for rendering
    rawMessages: messages, // Provide access to raw messages if needed
    isLoading,
    userId,
    isInitialized,
    chatStats,

    // Actions
    addMessage,
    updateMessages,
    clearCurrentSession,
    clearAllHistory,

    // Session Management (ChatGPT-like)
    getAllSessions,
    switchToSession,
    createNewSession,
    deleteSession,
    getCurrentSessionInfo,

    // Utilities
    initializeChatHistory,
  };
};

/**
 * Hook for chat history controls (history/clear buttons)
 */
export const useChatHistoryControls = () => {
  const { t } = useTranslation();
  const [showHistoryModal, setShowHistoryModal] = useState(false);
  const [showClearConfirm, setShowClearConfirm] = useState(false);

  const toggleHistoryModal = useCallback(() => {
    setShowHistoryModal(prev => !prev);
  }, []);

  const toggleClearConfirm = useCallback(() => {
    setShowClearConfirm(prev => !prev);
  }, []);

  const closeModals = useCallback(() => {
    setShowHistoryModal(false);
    setShowClearConfirm(false);
  }, []);

  return {
    showHistoryModal,
    showClearConfirm,
    toggleHistoryModal,
    toggleClearConfirm,
    closeModals,
  };
};
