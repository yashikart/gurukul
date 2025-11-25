import React, { useEffect } from "react";
import { useUser } from "@clerk/clerk-react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
import { useDispatch } from "react-redux";
import Layout from "./components/Layout";
import { ThemeProvider } from "./components/ThemeProvider";
import { TimeProvider } from "./context/TimeContext";
import { LoaderProvider } from "./context/LoaderContext";
import { Toaster } from "react-hot-toast";
import Home from "./pages/Home";
import Dashboard from "./pages/Dashboard";
import Subjects from "./pages/Subjects";
import Summarizer from "./pages/Summarizer";
import About from "./pages/About";
import Settings from "./pages/Settings";
import Chatbot from "./pages/Chatbot";
import Test from "./pages/Test";
import QuizPage from "./pages/QuizPage";
import Lectures from "./pages/Lectures";
import AgentSimulator from "./pages/AgentSimulator";
import AvatarSelection from "./pages/AvatarSelection";
import ForecastingDashboard from "./pages/ForecastingDashboard";
import SimpleForecastingDashboard from "./pages/SimpleForecastingDashboard";
import FinancialChatDemo from "./pages/FinancialChatDemo";
import MobileInputDemo from "./pages/MobileInputDemo";
import NotFound from "./pages/NotFound";
import SignIn from "./pages/SignIn";
import SignUp from "./pages/SignUp";
import { SignIn as ClerkSignIn, SignUp as ClerkSignUp } from "@clerk/clerk-react";
import ForgotPassword from "./pages/ForgotPassword";
import GetStarted from "./pages/GetStarted";
import AuthCallback from "./pages/AuthCallback";
import ProtectedRoute from "./components/ProtectedRoute";
import PublicRoute from "./components/PublicRoute";
import SummaryView from "./pages/SummaryView";
import { setUser, clearUser } from "./store/authSlice";

// Development utilities available in console if needed
// if (import.meta.env.DEV) {
//   import("./utils/testStorage");
//   import("./utils/pinModeTestUtils");
// }

export default function App() {
  const dispatch = useDispatch();
  const { isSignedIn, user } = useUser();

  // Sync Clerk user into Redux store
  useEffect(() => {
    if (isSignedIn && user) {
      dispatch(
        setUser({
          id: user.id,
          email: user.primaryEmailAddress?.emailAddress || null,
          user_metadata: {
            avatar_url: user.imageUrl,
            full_name: user.fullName || user.username || null,
          },
        })
      );
    } else {
      dispatch(clearUser());
    }
  }, [isSignedIn, user, dispatch]);

  return (
    <ThemeProvider>
      <TimeProvider>
        <LoaderProvider>
          <Toaster
            position="bottom-right"
            gutter={16}
            containerStyle={{
              bottom: 24,
              right: 24,
            }}
            toastOptions={{
              // Default options for all toasts
              duration: 3000,
              style: {
                background: "rgba(15, 15, 25, 0.85)",
                color: "#fff",
                backdropFilter: "blur(10px)",
                borderRadius: "16px",
                padding: "16px 20px",
                fontSize: "15px",
                fontWeight: "500",
                maxWidth: "400px",
                transform: "perspective(600px) rotateY(0deg)",
                boxShadow:
                  "0 4px 6px rgba(0, 0, 0, 0.1), " +
                  "0 10px 15px rgba(0, 0, 0, 0.1), " +
                  "0 0 0 1px rgba(255, 255, 255, 0.05) inset, " +
                  "0 0 30px rgba(255, 153, 51, 0.05)",
                border: "1px solid rgba(255, 255, 255, 0.1)",
                transition: "all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)",
              },
              // Custom styles for each type of toast
              success: {
                style: {
                  background:
                    "linear-gradient(135deg, rgba(15, 15, 25, 0.95), rgba(25, 25, 35, 0.95))",
                  borderTop: "1px solid rgba(255, 255, 255, 0.1)",
                  borderLeft: "1px solid rgba(255, 255, 255, 0.1)",
                  borderRight: "1px solid rgba(0, 0, 0, 0.1)",
                  borderBottom: "1px solid rgba(0, 0, 0, 0.1)",
                  boxShadow:
                    "0 10px 20px rgba(0, 0, 0, 0.15), " +
                    "0 3px 6px rgba(0, 0, 0, 0.1), " +
                    "0 0 0 1px rgba(255, 153, 51, 0.1), " +
                    "0 1px 0 0 rgba(255, 153, 51, 0.1) inset, " +
                    "0 -30px 30px rgba(255, 153, 51, 0.05) inset",
                  transform: "perspective(600px) rotateY(-2deg) translateZ(0)",
                },
                iconTheme: {
                  primary: "#FF9933",
                  secondary: "rgba(15, 15, 25, 0.95)",
                },
              },
              error: {
                style: {
                  background:
                    "linear-gradient(135deg, rgba(15, 15, 25, 0.95), rgba(25, 25, 35, 0.95))",
                  borderTop: "1px solid rgba(255, 255, 255, 0.1)",
                  borderLeft: "1px solid rgba(255, 255, 255, 0.1)",
                  borderRight: "1px solid rgba(0, 0, 0, 0.1)",
                  borderBottom: "1px solid rgba(0, 0, 0, 0.1)",
                  boxShadow:
                    "0 10px 20px rgba(0, 0, 0, 0.15), " +
                    "0 3px 6px rgba(0, 0, 0, 0.1), " +
                    "0 0 0 1px rgba(233, 69, 96, 0.1), " +
                    "0 1px 0 0 rgba(233, 69, 96, 0.1) inset, " +
                    "0 -30px 30px rgba(233, 69, 96, 0.05) inset",
                  transform: "perspective(600px) rotateY(-2deg) translateZ(0)",
                },
                iconTheme: {
                  primary: "#e94560",
                  secondary: "rgba(15, 15, 25, 0.95)",
                },
                duration: 4000,
              },
              loading: {
                style: {
                  background:
                    "linear-gradient(135deg, rgba(15, 15, 25, 0.95), rgba(25, 25, 35, 0.95))",
                  borderTop: "1px solid rgba(255, 255, 255, 0.1)",
                  borderLeft: "1px solid rgba(255, 255, 255, 0.1)",
                  borderRight: "1px solid rgba(0, 0, 0, 0.1)",
                  borderBottom: "1px solid rgba(0, 0, 0, 0.1)",
                  boxShadow:
                    "0 10px 20px rgba(0, 0, 0, 0.15), " +
                    "0 3px 6px rgba(0, 0, 0, 0.1), " +
                    "0 0 0 1px rgba(59, 130, 246, 0.1), " +
                    "0 1px 0 0 rgba(59, 130, 246, 0.1) inset, " +
                    "0 -30px 30px rgba(59, 130, 246, 0.05) inset",
                  transform: "perspective(600px) rotateY(-2deg) translateZ(0)",
                },
                iconTheme: {
                  primary: "#3b82f6",
                  secondary: "rgba(15, 15, 25, 0.95)",
                },
              },
            }}
          />
          <Router>
            <Routes>
              <Route path="/signin" element={<SignIn />} />
              <Route path="/signup" element={<SignUp />} />
              {/* Alternatively, Clerk's prebuilt components: */}
              {/* <Route path="/clerk/sign-in" element={<ClerkSignIn routing="path" path="/clerk/sign-in" />} /> */}
              {/* <Route path="/clerk/sign-up" element={<ClerkSignUp routing="path" path="/clerk/sign-up" />} /> */}
              <Route path="/forgotpassword" element={<ForgotPassword />} />
              <Route path="/auth/callback" element={<AuthCallback />} />
              <Route
                path="/"
                element={
                  <PublicRoute>
                    <GetStarted />
                  </PublicRoute>
                }
              />
              <Route
                path="/*"
                element={
                  <ProtectedRoute>
                    <Layout>
                      <Routes>
                        <Route path="/home" element={<Home />} />
                        <Route path="/dashboard" element={<Dashboard />} />
                        <Route path="/subjects" element={<Subjects />} />
                        <Route path="/learn" element={<Summarizer />} />
                        <Route
                          path="/learn/summary"
                          element={<SummaryView />}
                        />
                        <Route path="/chatbot" element={<Chatbot />} />
                        <Route path="/test" element={<Test />} />
                        <Route path="/quiz/:subject/:topic" element={<QuizPage />} />
                        <Route path="/lectures" element={<Lectures />} />
                        <Route
                          path="/agent-simulator"
                          element={<AgentSimulator />}
                        />
                        <Route
                          path="/avatar-selection"
                          element={<AvatarSelection />}
                        />
                        <Route
                          path="/forecasting"
                          element={<ForecastingDashboard />}
                        />
                        <Route
                          path="/forecasting-simple"
                          element={<SimpleForecastingDashboard />}
                        />
                        <Route
                          path="/financial-chat-demo"
                          element={<FinancialChatDemo />}
                        />
                        <Route
                          path="/mobile-input-demo"
                          element={<MobileInputDemo />}
                        />
                        <Route path="/about" element={<About />} />
                        <Route path="/settings" element={<Settings />} />
                        <Route path="*" element={<NotFound />} />
                      </Routes>
                    </Layout>
                  </ProtectedRoute>
                }
              />
            </Routes>
          </Router>
        </LoaderProvider>
      </TimeProvider>
    </ThemeProvider>
  );
}
