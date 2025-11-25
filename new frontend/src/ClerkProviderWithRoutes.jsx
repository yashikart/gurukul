import { ClerkProvider } from "@clerk/clerk-react";
import { useNavigate } from "react-router-dom";

export function ClerkProviderWithRoutes({ children }) {
  const navigate = useNavigate();
  const clerkPubKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;

  if (!clerkPubKey) {
    console.warn("Clerk authentication disabled - missing publishable key");
    return children;
  }

  return (
    <ClerkProvider
      publishableKey={clerkPubKey}
      navigate={(to) => navigate(to)}
      appearance={{
        variables: {
          colorPrimary: "#3b82f6"
        }
      }}
      fallbackRedirectUrl="/dashboard"
      signUpFallbackRedirectUrl="/dashboard"
      signInFallbackRedirectUrl="/dashboard"
    >
      {children}
    </ClerkProvider>
  );
}