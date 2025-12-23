import { createSlice } from '@reduxjs/toolkit';
import i18n from '../i18n';

// Helper function to get initial settings from localStorage
const getInitialSettings = () => {
  try {
    const savedSettings = localStorage.getItem('gurukul_settings');
    return savedSettings
      ? JSON.parse(savedSettings)
      : {
          theme: 'dark',
          fontSize: 'medium',
          language: 'english',
          notifications: true,
          audioEnabled: true,
          audioVolume: 1,
        };
  } catch (error) {
    console.error('Error loading settings:', error);
    return {
      theme: 'dark',
      fontSize: 'medium',
      language: 'english',
      notifications: true,
      audioEnabled: true,
      audioVolume: 1,
    };
  }
};

// Helper function to save settings to localStorage
const saveSettingsToStorage = (settings) => {
  try {
    localStorage.setItem('gurukul_settings', JSON.stringify(settings));
    // Backup to sessionStorage
    sessionStorage.setItem('gurukul_settings', JSON.stringify(settings));
  } catch (error) {
    console.error('Error saving settings:', error);
  }
};

const initialState = getInitialSettings();

export const settingsSlice = createSlice({
  name: 'settings',
  initialState,
  reducers: {
    setTheme: (state, action) => {
      state.theme = action.payload;
      saveSettingsToStorage({ ...state });
      
      // Also update the document class for immediate theme change
      if (action.payload === 'dark') {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }
    },
    setFontSize: (state, action) => {
      state.fontSize = action.payload;
      saveSettingsToStorage({ ...state });
    },
    setLanguage: (state, action) => {
      state.language = action.payload;
      saveSettingsToStorage({ ...state });
      // Sync with i18n
      i18n.changeLanguage(action.payload);
      // Update HTML attribute
      document.documentElement.setAttribute('data-language', action.payload);
    },
    setNotifications: (state, action) => {
      state.notifications = action.payload;
      saveSettingsToStorage({ ...state });
    },
    setAudioEnabled: (state, action) => {
      state.audioEnabled = action.payload;
      saveSettingsToStorage({ ...state });
    },
    setAudioVolume: (state, action) => {
      state.audioVolume = action.payload;
      saveSettingsToStorage({ ...state });
    },
    updateSettings: (state, action) => {
      const newSettings = { ...state, ...action.payload };
      Object.assign(state, newSettings);
      saveSettingsToStorage(newSettings);
      
      // Handle theme change
      if ('theme' in action.payload) {
        if (action.payload.theme === 'dark') {
          document.documentElement.classList.add('dark');
        } else {
          document.documentElement.classList.remove('dark');
        }
      }
      
      // Handle language change
      if ('language' in action.payload) {
        i18n.changeLanguage(action.payload.language);
        document.documentElement.setAttribute('data-language', action.payload.language);
      }
    },
  },
});

// Export actions
export const {
  setTheme,
  setFontSize,
  setLanguage,
  setNotifications,
  setAudioEnabled,
  setAudioVolume,
  updateSettings,
} = settingsSlice.actions;

// Export selectors
export const selectTheme = (state) => state.settings.theme;
export const selectFontSize = (state) => state.settings.fontSize;
export const selectLanguage = (state) => state.settings.language;
export const selectNotifications = (state) => state.settings.notifications;
export const selectAudioEnabled = (state) => state.settings.audioEnabled;
export const selectAudioVolume = (state) => state.settings.audioVolume;
export const selectAllSettings = (state) => state.settings;

export default settingsSlice.reducer;
