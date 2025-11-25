import React from "react";
import { ErrorBoundary } from "react-error-boundary";
import { toast } from "react-hot-toast";

function AuthErrorFallback({ error, resetErrorBoundary }) {
  React.useEffect(() => {
    console.error("Authentication error:", error);
    toast.error("Authentication error occurred. Please refresh the page.");
  }, [error]);

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="text-center">
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-6 max-w-md mx-auto">
          <h2 className="text-xl font-semibold text-red-400 mb-2">
            Authentication Error
          </h2>
          <p className="text-gray-300 mb-4">
            Something went wrong with authentication. Please try refreshing the page.
          </p>
          <button
            onClick={resetErrorBoundary}
            className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    </div>
  );
}

export default function AuthErrorBoundary({ children }) {
  return (
    <ErrorBoundary
      FallbackComponent={AuthErrorFallback}
      onError={(error, errorInfo) => {
        console.error("Auth error boundary caught an error:", error, errorInfo);
      }}
      onReset={() => {
        // Clear any auth-related localStorage items
        Object.keys(localStorage).forEach(key => {
          if (key.includes('clerk') || key.includes('auth') || key.includes('sb-')) {
            localStorage.removeItem(key);
          }
        });
        window.location.reload();
      }}
    >
      {children}
    </ErrorBoundary>
  );
}