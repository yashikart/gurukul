// Configuration settings for the application

// Determine the current environment
const isDevelopment = import.meta.env.DEV || false;
const isProduction = import.meta.env.PROD || false;

// Get environment variables with fallbacks
const getEnvVar = (key, fallback) => {
  const envVar = import.meta.env[key];
  return envVar !== undefined ? envVar : fallback;
};

// API Base URLs
export const API_BASE_URL = getEnvVar(
  'VITE_API_BASE_URL',
  isDevelopment ? 'http://localhost:8000' : 'https://api.gurukul.com'
);

// Chat API Base URL
export const CHAT_API_BASE_URL = getEnvVar(
  'VITE_CHAT_API_BASE_URL',
  isDevelopment ? 'http://localhost:8001' : 'https://api.gurukul.com'
);

// Financial API Base URL
export const FINANCIAL_API_BASE_URL = getEnvVar(
  'VITE_FINANCIAL_API_BASE_URL',
  isDevelopment ? 'http://localhost:8002' : 'https://api.gurukul.com'
);

// Agent API Base URL
export const AGENT_API_BASE_URL = getEnvVar(
  'VITE_AGENT_API_BASE_URL',
  isDevelopment ? 'http://localhost:8005' : 'https://api.gurukul.com'
);

// UniGuru API Base URL
export const UNIGURU_API_BASE_URL = getEnvVar(
  'VITE_UNIGURU_API_BASE_URL',
  isDevelopment ? 'https://e7d45d4c3f30.ngrok-free.app' : 'https://api.gurukul.com'
);

// Feature flags
export const ENABLE_ANALYTICS = getEnvVar('VITE_ENABLE_ANALYTICS', 'false') === 'true';
export const ENABLE_ERROR_REPORTING = getEnvVar('VITE_ENABLE_ERROR_REPORTING', 'true') === 'true';

// API endpoints configuration
export const API_ENDPOINTS = {
  // Base backend endpoints
  lessons: `${API_BASE_URL}/api/lessons`,
  users: `${API_BASE_URL}/api/users`,
  auth: `${API_BASE_URL}/api/auth`,
  
  // Chat endpoints
  chat: `${CHAT_API_BASE_URL}/api/chat`,
  history: `${CHAT_API_BASE_URL}/api/history`,
  
  // Financial endpoints
  financial: `${FINANCIAL_API_BASE_URL}/api/financial`,
  forecast: `${FINANCIAL_API_BASE_URL}/api/forecast`,
  
  // Agent endpoints
  agent: `${AGENT_API_BASE_URL}/api/agent`,
  
  // UniGuru endpoints
  uniguru: `${UNIGURU_API_BASE_URL}/api/uniguru`,
};

// Export environment information
export const ENV_INFO = {
  isDevelopment,
  isProduction,
  apiUrl: API_BASE_URL,
};
