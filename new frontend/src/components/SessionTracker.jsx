import React, { useEffect, useRef, useCallback } from "react";
import { timeSync } from "../utils/timeSync";
import { useAuth } from "../context/AuthContext";

// Fallback for crypto.randomUUID in non-secure contexts
const generateUUID = () => {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
};

const SessionTracker = ({ onTimeUpdate }) => {
  const sessionIdRef = useRef(generateUUID());
  const startTimeRef = useRef(Date.now());
  const userIdRef = useRef(null);
  const { user } = useAuth();
  const isSignedIn = !!user;
  const lastRecordedTimeRef = useRef(null);
  const lastUpdateTimeRef = useRef(Date.now());

  // Record time spent with throttling
  const recordTimeSpent = useCallback(async (endReason) => {
    if (!userIdRef.current) return;

    const now = Date.now();
    // Only record if at least 5 seconds have passed since last update
    if (now - lastUpdateTimeRef.current < 5000) return;

    const timeSpent = Math.floor((now - startTimeRef.current) / 1000);
    if (timeSpent < 1 || timeSpent === lastRecordedTimeRef.current) return;

    try {
      // TODO: Replace with your backend API to record time with user ID
      // await api.recordTime({ userId: userIdRef.current, sessionId: sessionIdRef.current, timeSpent, endReason });
      lastRecordedTimeRef.current = timeSpent;
      lastUpdateTimeRef.current = now;
    } catch (err) {
      console.error("Error in recordTimeSpent:", err);
    }
  }, []);

  useEffect(() => {
    const initTracking = async () => {
      if (!isSignedIn || !user) return;
      userIdRef.current = user.id;
      // Optionally inform backend of session start
      // await api.startSession({ userId: userIdRef.current, sessionId: sessionIdRef.current });
    };

    // Reset timeSync when component mounts
    timeSync.reset();

    // Subscribe to timeSync updates
    const unsubscribe = timeSync.subscribe((elapsed) => {
      if (onTimeUpdate) onTimeUpdate(elapsed);
    });

    const handleVisibilityChange = () => {
      if (document.hidden) {
        recordTimeSpent("tab_switch");
      } else {
        timeSync.reset();
      }
    };

    const handleUnload = () => {
      recordTimeSpent("page_close");
    };

    // Set up event listeners
    document.addEventListener("visibilitychange", handleVisibilityChange);
    window.addEventListener("beforeunload", handleUnload);

    // Start tracking
    initTracking();

    // Cleanup
    return () => {
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      window.removeEventListener("beforeunload", handleUnload);
      recordTimeSpent("component_unmount");
      unsubscribe();
    };
  }, [onTimeUpdate, recordTimeSpent, isSignedIn, user]);

  return null;
};

export default SessionTracker;