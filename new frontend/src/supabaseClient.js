import { createClient } from "@supabase/supabase-js";
import { storage } from "./utils/storageUtils";

// Use the new Supabase credentials
const supabaseUrl = "https://aczmbrhfzankcvpbjavt.supabase.co";
const supabaseAnonKey = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFjem1icmhmemFua2N2cGJqYXZ0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQ1Njg1MDIsImV4cCI6MjA4MDE0NDUwMn0.PsCxt3xyBGlh6BskcqDH5ojPLDjWRLMwgNYW-8eKBys";

// Validate environment variables
if (!supabaseUrl || !supabaseAnonKey) {
  console.error(
    "Missing Supabase environment variables. Check your .env file."
  );
}

// Diagnostic function to test Supabase connectivity
export const testSupabaseConnection = async () => {
  try {
    const response = await fetch(`${supabaseUrl}/rest/v1/`, {
      method: 'HEAD',
      headers: {
        'apikey': supabaseAnonKey,
      },
    });
    return {
      success: true,
      status: response.status,
      message: 'Supabase connection successful',
    };
  } catch (error) {
    return {
      success: false,
      error: error.message,
      message: 'Failed to connect to Supabase',
      details: {
        url: supabaseUrl,
        online: navigator.onLine,
        errorType: error.name,
      },
    };
  }
};

// Create a custom storage object with error handling
const customStorage = {
  getItem: (key) => {
    try {
      return localStorage.getItem(key);
    } catch (error) {
      console.error("Error accessing localStorage:", error);
      return null;
    }
  },
  setItem: (key, value) => {
    try {
      localStorage.setItem(key, value);
    } catch (error) {
      console.error("Error writing to localStorage:", error);
    }
  },
  removeItem: (key) => {
    try {
      localStorage.removeItem(key);
    } catch (error) {
      console.error("Error removing from localStorage:", error);
    }
  },
  clear: () => {
    try {
      // Only clear Supabase-related items
      Object.keys(localStorage).forEach((key) => {
        if (key.includes("supabase") || key.includes("sb-")) {
          localStorage.removeItem(key);
        }
      });
    } catch (error) {
      console.error("Error clearing localStorage:", error);
    }
  },
};

// Create a single Supabase client instance for the entire application
export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
    detectSessionInUrl: true,
    // Set redirectTo for OAuth operations
    redirectTo: window.location.origin + "/auth/callback",
    // Use our custom storage implementation
    storage: customStorage,
    // Set shorter storage key duration to prevent stale sessions
    storageKey: `sb-auth-token-${Math.floor(
      Date.now() / (1000 * 60 * 60 * 24)
    )}`,
    flowType: "pkce",
  },
  global: {
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    // Let Supabase handle fetch natively - it has built-in retry logic
    // We'll handle errors in the components instead
  },
  // Add debug option to help with troubleshooting
  debug: import.meta.env.DEV,
  // Set shorter localStorage TTL to prevent stale data
  realtime: {
    params: {
      eventsPerSecond: 10,
    },
  },
});

// Add event listener for auth state changes
supabase.auth.onAuthStateChange((event, session) => {
  // Handle session recovery errors
  if (event === "TOKEN_REFRESHED") {
    // Token refreshed successfully
  }

  if (event === "SIGNED_OUT") {
    // Clear only auth-related items from localStorage, preserve avatar data
    storage.clearAuthKeys();
  }
});