/**
 * Dedicated Chatbot TTS Service Integration
 * Provides TTS functionality using the dedicated chatbot service with Google TTS
 */

import blobUrlManager from '../utils/blobUrlManager';

const CHATBOT_TTS_BASE_URL = "http://localhost:8007";

class DedicatedChatbotTTSService {
  constructor() {
    this.audioCache = new Map();
    this.currentAudio = null;
    this.isPlaying = false;
    this.autoPlayEnabled = true;
    this.volume = 0.8;
    this.playbackQueue = [];
    this.isProcessingQueue = false;
  }

  /**
   * Check if the dedicated chatbot TTS service is healthy
   * @returns {Promise<boolean>} Service health status
   */
  async checkServiceHealth() {
    try {
      const response = await fetch(`${CHATBOT_TTS_BASE_URL}/api/health`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (response.ok) {
        const data = await response.json();
        return data.status === "healthy";
      }
      return false;
    } catch (error) {
      // Silently handle blocked requests (ad blockers, etc.)
      if (error.message && error.message.includes('ERR_BLOCKED_BY_CLIENT')) {
        console.info('ℹ️ TTS health check blocked by browser extension');
      }
      return false;
    }
  }

  /**
   * Generate TTS audio using the dedicated chatbot service
   * @param {string} text - Text to convert to speech
   * @param {Object} options - Additional options
   * @returns {Promise<Object>} TTS generation result
   */
  async generateTTS(text, options = {}) {
    if (!text || !text.trim()) {
      throw new Error("Text is required for TTS generation");
    }

    // Check cache first
    const cacheKey = this.getCacheKey(text, options);
    if (this.audioCache.has(cacheKey)) {
      return this.audioCache.get(cacheKey);
    }

    try {
      // Use streaming endpoint with form data
      const formData = new FormData();
      formData.append("text", text.trim());

      const response = await fetch(
        `${CHATBOT_TTS_BASE_URL}/api/generate/stream`,
        {
          method: "POST",
          body: formData,
        }
      );

      if (!response.ok) {
        throw new Error(
          `TTS streaming failed: ${response.status} ${response.statusText}`
        );
      }

      // Get audio data as blob
      const audioBlob = await response.blob();

      // Create managed blob URL for the audio
      const audioUrl = blobUrlManager.createBlobUrl(audioBlob, 'DedicatedChatbotTTS', {
        textLength: text.length,
        timestamp: new Date().toISOString(),
        purpose: 'chatbot-tts-audio'
      });

      const result = {
        status: "success",
        audioUrl: audioUrl,
        fullAudioUrl: audioUrl,
        blob: audioBlob,
        textLength: text.length,
        timestamp: new Date().toISOString(),
        text: text,
        isStreaming: true,
      };

      // Cache the result
      this.audioCache.set(cacheKey, result);

      return result;
    } catch (error) {
      throw error;
    }
  }

  /**
   * Play TTS audio immediately
   * @param {string} text - Text to convert and play
   * @param {Object} options - Playback options
   * @returns {Promise<void>}
   */
  async playTTS(text, options = {}) {
    try {
      const audioData = await this.generateTTS(text, options);
      await this.playAudio(audioData.fullAudioUrl, {
        ...options,
        isStreaming: audioData.isStreaming,
      });
    } catch (error) {
      throw error;
    }
  }

  /**
   * Play audio from URL with simple error handling
   * @param {string} audioUrl - URL of the audio file
   * @param {Object} options - Playback options
   * @returns {Promise<void>}
   */
  async playAudio(audioUrl, options = {}) {
    return new Promise((resolve, reject) => {
      try {
        // Stop current audio if playing
        this.stopCurrentAudio();

        console.log('🔊 DedicatedChatbotTTS: Starting audio playback:', {
          url: audioUrl.substring(0, 50) + '...',
          isStreaming: options.isStreaming,
          volume: options.volume || this.volume
        });

        // Create audio element directly
        const audio = new Audio();
        audio.volume = options.volume || this.volume;
        audio.preload = 'auto';
        audio.crossOrigin = 'anonymous';

        // Set current audio reference
        this.currentAudio = audio;
        this.isPlaying = true;

        // Event listeners
        audio.addEventListener('loadstart', () => {
          console.log('🔊 DedicatedChatbotTTS: Audio loading started');
        });

        audio.addEventListener('canplay', () => {
          console.log('🔊 DedicatedChatbotTTS: Audio can play');
        });

        audio.addEventListener('play', () => {
          this.isPlaying = true;
          if (options.onPlayStart) {
            options.onPlayStart(audioUrl);
          }
        });

        audio.addEventListener('ended', () => {
          this.isPlaying = false;
          this.currentAudio = null;

          // Cleanup blob URL if it's a streaming audio
          if (options.isStreaming && audioUrl.startsWith("blob:")) {
            // Delay cleanup to ensure audio has finished
            setTimeout(() => {
              blobUrlManager.revokeBlobUrl(audioUrl);
              console.log('🔊 DedicatedChatbotTTS: Blob URL cleaned up after playback');
            }, 500); // Longer delay for safety
          }

          console.log('🔊 DedicatedChatbotTTS: Audio playback completed');
          if (options.onPlayEnd) {
            options.onPlayEnd(audioUrl);
          }
          resolve();
        });

        audio.addEventListener('error', (error) => {
          this.isPlaying = false;
          this.currentAudio = null;
          console.error('❌ DedicatedChatbotTTS: Audio playback error:', error);
          if (options.onError) {
            options.onError(error);
          }
          reject(new Error('Audio playback failed'));
        });

        // Set source and play
        audio.src = audioUrl;

        // Start playback
        const playPromise = audio.play();
        if (playPromise !== undefined) {
          playPromise
            .then(() => {
              console.log('🔊 DedicatedChatbotTTS: Audio playback started successfully');
            })
            .catch((error) => {
              this.isPlaying = false;
              this.currentAudio = null;

              if (error.name === 'NotAllowedError') {
                console.warn('🔊 DedicatedChatbotTTS: Autoplay blocked by browser');
                resolve(); // Don't treat autoplay block as error
              } else {
                console.error('❌ DedicatedChatbotTTS: Audio play error:', error);
                reject(error);
              }
            });
        }

      } catch (error) {
        this.isPlaying = false;
        this.currentAudio = null;
        console.error('❌ DedicatedChatbotTTS: Audio setup failed:', error);
        reject(error);
      }
    });
  }

  /**
   * Auto-play TTS for AI-generated content
   * @param {string} text - AI-generated text
   * @param {Object} options - Auto-play options
   */
  async autoPlayAI(text, options = {}) {
    if (!this.autoPlayEnabled || !text || !text.trim()) {
      return;
    }

    // Add a small delay for better UX
    const delay = options.delay || 500;
    setTimeout(async () => {
      try {
        await this.playTTS(text, { ...options, autoPlay: true });
      } catch (error) {
        // Handle autoplay policy errors gracefully
        if (error.message.includes("user interaction required")) {
          this.enableAutoplayAfterInteraction();
        }
      }
    }, delay);
  }

  /**
   * Enable autoplay after user interaction
   */
  enableAutoplayAfterInteraction() {
    const enableAutoplay = () => {
      document.removeEventListener("click", enableAutoplay);
      document.removeEventListener("keydown", enableAutoplay);
      document.removeEventListener("touchstart", enableAutoplay);
    };

    // Listen for any user interaction
    document.addEventListener("click", enableAutoplay, { once: true });
    document.addEventListener("keydown", enableAutoplay, { once: true });
    document.addEventListener("touchstart", enableAutoplay, { once: true });
  }

  /**
   * Stop current audio playback
   */
  stopCurrentAudio() {
    if (this.currentAudio) {
      this.currentAudio.pause();
      this.currentAudio.currentTime = 0;
      this.currentAudio = null;
      this.isPlaying = false;
    }
  }

  /**
   * Generate cache key for audio caching
   * @param {string} text - Text content
   * @param {Object} options - Options object
   * @returns {string} Cache key
   */
  getCacheKey(text, options = {}) {
    const optionsString = JSON.stringify(options);
    return `${text.trim()}_${optionsString}`;
  }

  /**
   * Clear audio cache and cleanup blob URLs
   */
  clearCache() {
    // Cleanup blob URLs to prevent memory leaks
    for (const [, result] of this.audioCache.entries()) {
      if (result.isStreaming && result.audioUrl) {
        blobUrlManager.revokeBlobUrl(result.audioUrl);
      }
    }
    this.audioCache.clear();
  }

  /**
   * Cleanup blob URL for a specific audio result
   * @param {Object} audioResult - Audio result object
   */
  cleanupAudioResult(audioResult) {
    if (audioResult && audioResult.isStreaming && audioResult.audioUrl) {
      blobUrlManager.revokeBlobUrl(audioResult.audioUrl);
    }
  }

  /**
   * Get current status
   * @returns {Object} Current service status
   */
  getStatus() {
    return {
      isPlaying: this.isPlaying,
      autoPlayEnabled: this.autoPlayEnabled,
      volume: this.volume,
      cacheSize: this.audioCache.size,
      currentAudio: this.currentAudio ? "playing" : "none",
      service: "Dedicated Chatbot TTS Service",
    };
  }
}

// Create and export singleton instance
const dedicatedChatbotTTSService = new DedicatedChatbotTTSService();
export default dedicatedChatbotTTSService;
