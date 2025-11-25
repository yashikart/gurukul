// API Security utilities to prevent CSRF and XSS attacks

// Generate CSRF token
export const generateCSRFToken = () => {
  return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
};

// Store CSRF token in session storage
export const setCSRFToken = (token) => {
  sessionStorage.setItem('csrf_token', token);
};

// Get CSRF token from session storage
export const getCSRFToken = () => {
  return sessionStorage.getItem('csrf_token');
};

// Sanitize HTML content to prevent XSS
export const sanitizeHTML = (str) => {
  if (typeof str !== 'string') return str;
  
  const temp = document.createElement('div');
  temp.textContent = str;
  return temp.innerHTML;
};

// Escape HTML entities
export const escapeHTML = (str) => {
  if (typeof str !== 'string') return str;
  
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;')
    .replace(/\//g, '&#x2F;');
};

// Validate URL to prevent SSRF
export const isValidURL = (url) => {
  try {
    const urlObj = new URL(url);
    // Only allow http and https protocols
    if (!['http:', 'https:'].includes(urlObj.protocol)) {
      return false;
    }
    // Prevent localhost and private IP ranges in production
    if (import.meta.env.PROD) {
      const hostname = urlObj.hostname;
      if (hostname === 'localhost' || 
          hostname === '127.0.0.1' || 
          hostname.startsWith('192.168.') ||
          hostname.startsWith('10.') ||
          hostname.startsWith('172.')) {
        return false;
      }
    }
    return true;
  } catch {
    return false;
  }
};

// Secure fetch wrapper with CSRF protection
export const secureFetch = async (url, options = {}) => {
  // Validate URL
  if (!isValidURL(url)) {
    throw new Error('Invalid URL provided');
  }

  // Add CSRF token to headers
  const csrfToken = getCSRFToken();
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (csrfToken) {
    headers['X-CSRF-Token'] = csrfToken;
  }

  // Add credentials for same-origin requests
  const fetchOptions = {
    credentials: 'same-origin',
    ...options,
    headers,
  };

  return fetch(url, fetchOptions);
};

// Initialize CSRF protection
export const initCSRFProtection = () => {
  if (!getCSRFToken()) {
    const token = generateCSRFToken();
    setCSRFToken(token);
  }
};