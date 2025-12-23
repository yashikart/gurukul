// API functions will go here
import { API_BASE_URL, CHAT_API_BASE_URL } from "../config";

// Export orchestration API functions
export {
  useGenerateEnhancedLessonMutation,
  useGetUserProgressQuery,
  useLazyGetUserProgressQuery,
  useGetUserAnalyticsQuery,
  useLazyGetUserAnalyticsQuery,
  useTriggerInterventionMutation,
  useGetIntegrationStatusQuery,
  useLazyGetIntegrationStatusQuery,
  useCheckOrchestrationHealthQuery,
  useLazyCheckOrchestrationHealthQuery,
  checkOrchestrationAvailability,
  formatEnhancedLessonData,
  formatUserProgressData,
} from "./orchestrationApiSlice";

export const getSubjects = async () => {
  const response = await fetch(`${API_BASE_URL}/subjects`);
  if (!response.ok) {
    throw new Error("Failed to fetch subjects");
  }
  return response.json();
};

export const getLectures = async () => {
  const response = await fetch(`${API_BASE_URL}/lectures`);
  if (!response.ok) {
    throw new Error("Failed to fetch lectures");
  }
  return response.json();
};

export const getTests = async () => {
  const response = await fetch(`${API_BASE_URL}/tests`);
  if (!response.ok) {
    throw new Error("Failed to fetch tests");
  }
  return response.json();
};

// Function to post message to chatpost endpoint
export const sendChatMessage = async (
  aiMessage,
  userQuery,
  userId = null,
  llmModel = "grok"
) => {
  // Ensure we have a valid user ID or use guest-user for anonymous users
  const userIdentifier = userId || "guest-user";

  // For debugging
  console.log("DEBUG - sendChatMessage called with:", {
    aiMessage: aiMessage ? aiMessage.substring(0, 50) + "..." : "null",
    userQuery: userQuery ? userQuery.substring(0, 50) + "..." : "null",
    userIdentifier,
    llmModel,
  });

  //*Prepare to send chat message

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15000); // Increased to 15 second timeout

    // Create URL parameters
    const params = new URLSearchParams({
      user_id: userIdentifier,
    });

    // Create request body - exactly matching what the backend expects
    const requestBody = {
      message: userQuery, // The user's message (not the AI response)
      llm: llmModel, // The selected AI model (grok, llama, chatgpt, uniguru)
      type: "chat_message",
      // Note: timestamp will be added by the server
    };

    // Send POST request to chatpost endpoint
    console.log(
      "DEBUG - POST Request Body:",
      JSON.stringify(requestBody, null, 2)
    );

    const response = await fetch(
      `${CHAT_API_BASE_URL}/chatpost?${params.toString()}`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestBody),
        signal: controller.signal,
      }
    );

    clearTimeout(timeoutId);

    // Log the raw response for debugging
    console.log("DEBUG - POST Response Status:", response.status);
    console.log("DEBUG - POST Response Status Text:", response.statusText);
    console.log(
      "DEBUG - POST Response Headers:",
      Object.fromEntries([...response.headers.entries()])
    );

    if (!response.ok) {
      // Handle specific error codes
      if (response.status === 503) {
        console.log("DEBUG - POST 503 Service Unavailable");
        // Return a minimal success response instead of throwing
        return { success: false, error: "Server temporarily unavailable" };
      } else if (response.status === 404) {
        console.log("DEBUG - POST 404 Not Found");
        return { success: false, error: "Endpoint not found" };
      } else if (response.status >= 500) {
        console.log("DEBUG - POST Server Error:", response.status);
        return { success: false, error: "Server error" };
      } else {
        // Try to get more information about the error
        try {
          const errorText = await response.text();
          console.error("DEBUG - POST Error Response Body:", errorText);

          // Try to parse as JSON if possible
          try {
            const errorJson = JSON.parse(errorText);
            console.error("DEBUG - POST Error JSON:", errorJson);
            throw new Error(`Server error: ${JSON.stringify(errorJson)}`);
          } catch (/* unused */ _parseError) {
            // Not JSON, use as text
            console.error("DEBUG - Error response is not valid JSON");
            throw new Error(
              `HTTP error! status: ${response.status}, message: ${errorText}`
            );
          }
        } catch (/* unused */ _errorReadError) {
          // If we can't read the error response, fall back to basic error
          console.error("DEBUG - Failed to read error response");
          throw new Error(`HTTP error! status: ${response.status}`);
        }
      }
    }

    // Get the response data
    try {
      // First get the raw text for debugging
      const responseText = await response.text();
      console.log("DEBUG - POST Raw Response:", responseText);

      // Try to parse as JSON
      let responseData;
      try {
        responseData = JSON.parse(responseText);
        console.log("DEBUG - POST Parsed Response:", responseData);
        return responseData;
      } catch (parseError) {
        console.error("DEBUG - POST JSON Parse Error:", parseError);
        // If it's not valid JSON, return the text as is
        return { success: true, message: responseText };
      }
    } catch (responseError) {
      console.error("DEBUG - POST Response Reading Error:", responseError);
      return { success: false, error: "Failed to read response" };
    }
  } catch (error) {
    // For sendChatMessage, we'll handle errors more gracefully since this is a secondary operation
    // that shouldn't break the main chat functionality if it fails
    console.error("DEBUG - POST Catch Block Error:", error);
    console.error("DEBUG - POST Error Stack:", error.stack);

    if (error.name === "AbortError") {
      return { success: false, error: "Request timed out" };
    } else if (
      error instanceof TypeError &&
      error.message === "Failed to fetch"
    ) {
      return { success: false, error: "Connection failed" };
    }

    // Return error but don't throw it to prevent breaking the main chat flow
    return { success: false, error: error.message };
  }
};

//*Function to fetch response from chatbot endpoint
export const fetchChatbotResponse = async (message, userId = null) => {
  // Ensure we have a valid user ID or use guest-user for anonymous users
  const userIdentifier = userId || "guest-user";

  // Prepare to fetch chatbot response

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15000); // Increased timeout to 15 seconds

    // Convert the message data to URL parameters
    // Note: Based on the backend code, we don't actually need to send any parameters
    // The backend will find the latest query with no response
    const params = new URLSearchParams();

    // Only add user_id if provided (though it's not used by the backend)
    if (userIdentifier) {
      params.append("user_id", userIdentifier);
    }

    // For debugging, log what we're doing
    console.log(
      "DEBUG - Not sending message parameter as backend will find the latest query"
    );

    // Send GET request to chatbot endpoint

    const response = await fetch(
      `${CHAT_API_BASE_URL}/chatbot?${params.toString()}`,
      {
        method: "GET",
        headers: {
          Accept: "application/json",
        },
        signal: controller.signal,
      }
    );

    clearTimeout(timeoutId);

    if (!response.ok) {
      // Try to get the error response body for more details
      try {
        const errorText = await response.text();

        // Try to parse as JSON if possible
        try {
          const errorJson = JSON.parse(errorText);

          // Check for specific FastAPI validation error format
          if (errorJson.detail && Array.isArray(errorJson.detail)) {
            const validationErrors = errorJson.detail
              .map((err) => `${err.msg} at ${err.loc.join(".")}`)
              .join(", ");
            throw new Error(`Validation error: ${validationErrors}`);
          }

          // Check for "No queries found" error
          if (
            errorJson.error &&
            (errorJson.error === "No queries yet" ||
              errorJson.error === "No queries found for this user")
          ) {
            // This is a special case we'll handle in the main function
            return { text: JSON.stringify(errorJson) };
          }
        } catch {
          // Not JSON, use as text (ignoring parse error)
        }

        // Handle specific error codes with more context
        if (response.status === 503) {
          throw new Error(
            `The server is temporarily unavailable (503). Response: ${errorText.substring(
              0,
              100
            )}`
          );
        } else if (response.status === 404) {
          throw new Error(
            `The chatbot endpoint was not found (404). Response: ${errorText.substring(
              0,
              100
            )}`
          );
        } else if (response.status >= 500) {
          throw new Error(
            `Server error (${response.status}). Response: ${errorText.substring(
              0,
              100
            )}`
          );
        } else if (response.status === 422) {
          throw new Error(
            `Validation error (422). Response: ${errorText.substring(0, 100)}`
          );
        } else {
          throw new Error(
            `HTTP error! Status: ${
              response.status
            }, Response: ${errorText.substring(0, 100)}`
          );
        }
      } catch (errorReadError) {
        // If we can't read the error response, fall back to basic error
        console.error("DEBUG - Failed to read error response:", errorReadError);
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
    }

    // Get the raw response text first for debugging
    const responseText = await response.text();
    console.log("DEBUG - Chatbot Raw Response:", responseText);

    // Try to parse the response as JSON
    let data;
    try {
      data = JSON.parse(responseText);
      console.log(
        "DEBUG - Chatbot Parsed Response:",
        JSON.stringify(data, null, 2)
      );

      // Log the structure of the response for debugging
      if (data && typeof data === "object") {
        console.log("DEBUG - Response keys:", Object.keys(data));

        // Check for nested response structure
        if (data.response && typeof data.response === "object") {
          console.log(
            "DEBUG - Response.response keys:",
            Object.keys(data.response)
          );

          // Check if there's a message in the response
          if (data.response.message) {
            console.log(
              "DEBUG - Found message in response.response:",
              data.response.message
            );
          }
        }
      }
    } catch (parseError) {
      console.error("DEBUG - JSON Parse Error:", parseError);
      console.error("DEBUG - JSON Parse Error Stack:", parseError.stack);
      console.error("DEBUG - Raw text that failed to parse:", responseText);
      throw new Error(
        `Failed to parse response as JSON: ${responseText.substring(0, 100)}...`
      );
    }

    // Check if the response is empty or doesn't contain a message
    if (!data || (typeof data === "object" && Object.keys(data).length === 0)) {
      throw new Error(
        "The server returned an empty response. Please try again."
      );
    }

    // Check for specific error messages related to first-time queries
    if (
      data.error &&
      (data.error === "No queries yet" ||
        data.error === "No queries found for this user")
    ) {
      // Return a default response for the first query
      return {
        message:
          "Hello! I'm your AI assistant. How can I help you today? (Note: This is the first query to the server)",
        isFirstQuery: true,
      };
    }

    // Check if the response has the expected structure
    if (data && data.response && data.response.message) {
      console.log("DEBUG - Response has the expected structure");
      // The response is in the expected format, return it as is
      return data;
    }

    // Check if the message property exists
    if (!data.message && !data.response) {
      // If there's an error message, include it in the thrown error
      if (data.error) {
        throw new Error(`Server error: ${data.error}. Please try again.`);
      } else {
        throw new Error(
          "The server response is missing required data. Please try again."
        );
      }
    }

    // If data.response exists but data.message doesn't, use response as message
    if (!data.message && data.response) {
      data.message = data.response;
    }

    return data;
  } catch (error) {
    if (error.name === "AbortError") {
      throw new Error(
        "Request timed out - the server is not responding. Please check your network connection or try again later."
      );
    } else if (
      error instanceof TypeError &&
      error.message === "Failed to fetch"
    ) {
      throw new Error(
        `Unable to connect to the server at ${CHAT_API_BASE_URL}/chatbot - please check if the server is running or your network connection.`
      );
    }
    throw error;
  }
};

// Function to upload file for summarization
export const uploadFileForSummary = async (file) => {
  const formData = new FormData();
  formData.append("file", file);

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout

    const response = await fetch(`${CHAT_API_BASE_URL}/process-pdf`, {
      method: "POST",
      body: formData,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  } catch (error) {
    if (error.name === "AbortError") {
      throw new Error("File upload timed out - the server is not responding");
    }
    throw error;
  }
};

// Function to get file summary
export const getFileSummary = async (fileId) => {
  const response = await fetch(`${API_BASE_URL}/get-summary/${fileId}`);
  if (!response.ok) {
    throw new Error("Failed to fetch summary");
  }
  return response.json();
};

// Function to fetch the last PDF summary
export const getLastPdfSummary = async () => {
  const response = await fetch(`${API_BASE_URL}/get-last-pdf`);
  if (!response.ok) {
    throw new Error("Failed to fetch summary");
  }
  return response.json();
};

// Function to convert text to speech
export const convertTextToSpeech = async (text) => {
  const response = await fetch(`${API_BASE_URL}/text-to-speech`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ text }),
  });

  if (!response.ok) {
    throw new Error("Failed to convert text to speech");
  }

  return response.blob(); // Returns audio blob
};

// Function to send financial simulation data (asynchronous)
export const sendFinancialSimulationData = async (userData) => {
  try {
    // Set a timeout for the fetch request
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout

    // Format the data according to the standardized schema
    const requestBody = {
      user_id: userData.user_id || "guest-user",
      user_name: userData.user_name || "Guest User", // Must contain actual name, not placeholder
      income: userData.income || 0,
      expenses: userData.expenses || [],
      total_expenses: userData.total_expenses || 0,
      goal: userData.goal || "",
      financial_type: userData.financial_type || "moderate", // "conservative", "moderate", or "aggressive"
      risk_level: userData.risk_level || "medium", // "low", "medium", or "high"
    };

    console.log("DEBUG - Sending financial simulation data:", requestBody);

    // Send the data to the API
    const response = await fetch(`${API_BASE_URL}/start-simulation`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(requestBody),
      signal: controller.signal,
    });

    // Clear the timeout
    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorText = await response.text();
      console.error("DEBUG - Financial Simulation Error Response:", errorText);
      throw new Error(`API error: ${response.status} - ${errorText}`);
    }

    // Get the response data
    try {
      const responseText = await response.text();
      console.log("DEBUG - Financial Simulation Raw Response:", responseText);

      // Try to parse as JSON
      if (responseText) {
        try {
          const responseData = JSON.parse(responseText);
          console.log(
            "DEBUG - Financial Simulation Parsed Response:",
            responseData
          );

          // Return standardized response
          return {
            success: true,
            message: responseData.message || "Simulation started",
            task_id: responseData.task_id,
            user_id: userData.user_id,
            user_name: userData.user_name,
            ...responseData,
          };
        } catch (parseError) {
          console.error(
            "DEBUG - Financial Simulation JSON Parse Error:",
            parseError
          );
          // If it's not valid JSON, return the text as is
          return { success: true, message: responseText };
        }
      } else {
        // Empty response but status was OK
        return { success: true, message: "Simulation started successfully" };
      }
    } catch (responseError) {
      console.error(
        "DEBUG - Financial Simulation Response Reading Error:",
        responseError
      );
      return { success: false, error: "Failed to read response" };
    }
  } catch (error) {
    console.error("DEBUG - Financial Simulation Error:", error);

    if (error.name === "AbortError") {
      return {
        success: false,
        error: "Request to financial simulation API timed out",
      };
    } else if (
      error instanceof TypeError &&
      error.message === "Failed to fetch"
    ) {
      return {
        success: false,
        error: "Could not connect to financial simulation server",
      };
    }

    return { success: false, error: error.message };
  }
};

// Function to run direct simulation (synchronous)
export const runDirectSimulation = async (userData) => {
  try {
    // Set a timeout for the fetch request
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout for synchronous request

    // Format the data according to the standardized schema
    const requestBody = {
      user_id: userData.user_id || "guest-user",
      user_name: userData.user_name || "Guest User",
      income: userData.income || 0,
      expenses: userData.expenses || [],
      total_expenses: userData.total_expenses || 0,
      goal: userData.goal || "",
      financial_type: userData.financial_type || "moderate",
      risk_level: userData.risk_level || "medium",
    };

    console.log("DEBUG - Running direct simulation:", requestBody);

    // Send the data to the API
    const response = await fetch(`${API_BASE_URL}/simulate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(requestBody),
      signal: controller.signal,
    });

    // Clear the timeout
    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorText = await response.text();
      console.error("DEBUG - Direct Simulation Error Response:", errorText);
      throw new Error(`API error: ${response.status} - ${errorText}`);
    }

    // Get the response data
    try {
      const responseText = await response.text();
      console.log("DEBUG - Direct Simulation Raw Response:", responseText);

      // Try to parse as JSON
      if (responseText) {
        try {
          const responseData = JSON.parse(responseText);
          console.log(
            "DEBUG - Direct Simulation Parsed Response:",
            responseData
          );

          // Return standardized response
          return {
            success: true,
            user_id: userData.user_id,
            user_name: userData.user_name,
            data: responseData.data || responseData,
            ...responseData,
          };
        } catch (parseError) {
          console.error(
            "DEBUG - Direct Simulation JSON Parse Error:",
            parseError
          );
          // If it's not valid JSON, return the text as is
          return { success: true, message: responseText };
        }
      } else {
        // Empty response but status was OK
        return { success: true, message: "Simulation completed successfully" };
      }
    } catch (responseError) {
      console.error(
        "DEBUG - Direct Simulation Response Reading Error:",
        responseError
      );
      return { success: false, error: "Failed to read response" };
    }
  } catch (error) {
    console.error("DEBUG - Direct Simulation Error:", error);

    if (error.name === "AbortError") {
      return {
        success: false,
        error: "Request to financial simulation API timed out",
      };
    } else if (
      error instanceof TypeError &&
      error.message === "Failed to fetch"
    ) {
      return {
        success: false,
        error: "Could not connect to financial simulation server",
      };
    }

    return { success: false, error: error.message };
  }
};

// Function to check the status of a financial simulation
export const checkSimulationStatus = async (taskId, userId = null) => {
  try {
    // Set a timeout for the fetch request
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout

    // Ensure we have a valid user ID or use guest-user for anonymous users
    const userIdentifier = userId || "guest-user";

    console.log(
      "DEBUG - Checking simulation status for task:",
      taskId,
      "User ID:",
      userIdentifier
    );

    // Add user_id as a query parameter
    const url = new URL(`${API_BASE_URL}/simulation-status/${taskId}`);
    url.searchParams.append("user_id", userIdentifier);

    // Fetch the simulation status from the API
    const response = await fetch(url.toString(), {
      method: "GET",
      headers: {
        Accept: "application/json",
      },
      signal: controller.signal,
    });

    // Clear the timeout
    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorText = await response.text();
      console.error("DEBUG - Simulation Status Error Response:", errorText);
      throw new Error(`API error: ${response.status} - ${errorText}`);
    }

    // Get the response data
    try {
      const responseText = await response.text();
      console.log("DEBUG - Simulation Status Raw Response:", responseText);

      // Try to parse as JSON
      if (responseText) {
        try {
          const responseData = JSON.parse(responseText);
          console.log(
            "DEBUG - Simulation Status Parsed Response:",
            responseData
          );

          // Return standardized response
          return {
            success: true,
            task_id: taskId,
            user_id: userIdentifier,
            task_status:
              responseData.status || responseData.task_status || "unknown",
            task_details:
              responseData.details || responseData.task_details || {},
            progress: responseData.progress || 0,
            estimated_completion: responseData.estimated_completion || null,
            ...responseData,
          };
        } catch (parseError) {
          console.error(
            "DEBUG - Simulation Status JSON Parse Error:",
            parseError
          );
          // If it's not valid JSON, return the text as is
          return {
            success: false,
            error: "Invalid JSON response",
            message: responseText,
          };
        }
      } else {
        // Empty response but status was OK
        return {
          success: false,
          error: "Empty response from server",
        };
      }
    } catch (responseError) {
      console.error("DEBUG - Simulation Status Reading Error:", responseError);
      return { success: false, error: "Failed to read response" };
    }
  } catch (error) {
    console.error("DEBUG - Simulation Status Error:", error);

    if (error.name === "AbortError") {
      return {
        success: false,
        error: "Request to check simulation status timed out",
      };
    } else if (
      error instanceof TypeError &&
      error.message === "Failed to fetch"
    ) {
      return {
        success: false,
        error: "Could not connect to financial simulation server",
      };
    }

    return { success: false, error: error.message };
  }
};

// Function to get simulation results by task ID
export const getSimulationResultsByTaskId = async (taskId, userId = null) => {
  try {
    // Set a timeout for the fetch request
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout

    // Ensure we have a valid user ID or use anonymous-user for anonymous users
    const userIdentifier = userId || "anonymous-user";

    console.log(
      "DEBUG - Getting simulation results for task:",
      taskId,
      "User ID:",
      userIdentifier
    );

    // Add user_id as a query parameter
    const url = new URL(`${API_BASE_URL}/simulation-results/${taskId}`);
    url.searchParams.append("user_id", userIdentifier);

    // Fetch the simulation results from the API
    const response = await fetch(url.toString(), {
      method: "GET",
      headers: {
        Accept: "application/json",
      },
      signal: controller.signal,
    });

    // Clear the timeout
    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorText = await response.text();
      console.error("DEBUG - Simulation Results Error Response:", errorText);
      throw new Error(`API error: ${response.status} - ${errorText}`);
    }

    // Get the response data
    try {
      const responseText = await response.text();
      console.log("DEBUG - Simulation Results Raw Response:", responseText);

      // Try to parse as JSON
      if (responseText) {
        try {
          const responseData = JSON.parse(responseText);
          console.log(
            "DEBUG - Simulation Results Parsed Response:",
            responseData
          );

          // Process the standardized cashflow data if available
          const processedData = processFinancialSimulationData(
            responseData.data || {},
            responseData.user_name || "Guest User"
          );

          // Return standardized response with user name included
          return {
            success: true,
            task_id: taskId,
            user_id: userIdentifier,
            user_name: responseData.user_name || "Guest User",
            task_status:
              responseData.status || responseData.task_status || "unknown",
            data: processedData,
            partial_results: responseData.partial_results || false,
            progress: responseData.progress || 0,
            ...responseData,
          };
        } catch (parseError) {
          console.error(
            "DEBUG - Simulation Results JSON Parse Error:",
            parseError
          );
          // If it's not valid JSON, return the text as is
          return {
            success: false,
            error: "Invalid JSON response",
            message: responseText,
          };
        }
      } else {
        // Empty response but status was OK
        return {
          success: false,
          error: "Empty response from server",
        };
      }
    } catch (responseError) {
      console.error("DEBUG - Simulation Results Reading Error:", responseError);
      return { success: false, error: "Failed to read response" };
    }
  } catch (error) {
    console.error("DEBUG - Simulation Results Error:", error);

    if (error.name === "AbortError") {
      return {
        success: false,
        error: "Request to get simulation results timed out",
      };
    } else if (
      error instanceof TypeError &&
      error.message === "Failed to fetch"
    ) {
      return {
        success: false,
        error: "Could not connect to financial simulation server",
      };
    }

    return { success: false, error: error.message };
  }
};

// Function to get financial simulation results (final results)
export const getFinancialSimulationResults = async (userId) => {
  try {
    // Set a timeout for the fetch request
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout

    // Ensure we have a valid user ID or use guest-user for anonymous users
    const userIdentifier = userId || "guest-user";

    console.log(
      "DEBUG - Getting final simulation results for user:",
      userIdentifier
    );

    // Fetch the simulation results from the API
    const response = await fetch(
      `${API_BASE_URL}/get-simulation-result/${userIdentifier}`,
      {
        method: "GET",
        headers: {
          Accept: "application/json",
        },
        signal: controller.signal,
      }
    );

    // Clear the timeout
    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorText = await response.text();
      console.error(
        "DEBUG - Financial Simulation Results Error Response:",
        errorText
      );
      throw new Error(`API error: ${response.status} - ${errorText}`);
    }

    // Get the response data
    try {
      const responseText = await response.text();
      console.log(
        "DEBUG - Financial Simulation Results Raw Response:",
        responseText
      );

      // Try to parse as JSON
      if (responseText) {
        try {
          const responseData = JSON.parse(responseText);
          console.log(
            "DEBUG - Financial Simulation Results Parsed Response:",
            responseData
          );

          // Process the standardized cashflow data if available
          const processedData = processFinancialSimulationData(
            responseData.data || {},
            responseData.user_name || "Guest User"
          );

          // Return standardized response with user name included
          return {
            success: true,
            user_id: userIdentifier,
            user_name: responseData.user_name || "Guest User",
            data: processedData,
            source: responseData.source || "mongodb",
            is_complete: responseData.is_complete || true,
            ...responseData,
          };
        } catch (parseError) {
          console.error(
            "DEBUG - Financial Simulation Results JSON Parse Error:",
            parseError
          );
          // If it's not valid JSON, return the text as is
          return {
            success: false,
            error: "Invalid JSON response",
            message: responseText,
          };
        }
      } else {
        // Empty response but status was OK
        return { success: false, error: "Empty response from server" };
      }
    } catch (responseError) {
      console.error(
        "DEBUG - Financial Simulation Results Reading Error:",
        responseError
      );
      return { success: false, error: "Failed to read response" };
    }
  } catch (error) {
    console.error("DEBUG - Financial Simulation Results Error:", error);

    if (error.name === "AbortError") {
      return {
        success: false,
        error: "Request to get simulation results timed out",
      };
    } else if (
      error instanceof TypeError &&
      error.message === "Failed to fetch"
    ) {
      return {
        success: false,
        error: "Could not connect to financial simulation server",
      };
    }

    return { success: false, error: error.message };
  }
};

// Helper function to process financial simulation data into standardized format
const processFinancialSimulationData = (data, userName = "Guest User") => {
  // If data is not an object or is null/undefined, return empty object
  if (!data || typeof data !== "object") {
    return {};
  }

  // Create a deep copy to avoid modifying the original data
  const processedData = JSON.parse(JSON.stringify(data));

  // Check if we have simulated_cashflow data to process
  if (
    processedData.simulated_cashflow &&
    Array.isArray(processedData.simulated_cashflow)
  ) {
    // Ensure each cashflow entry has the standardized format
    processedData.simulated_cashflow = processedData.simulated_cashflow.map(
      (cashflow) => {
        // Make sure all required sections exist with default values if missing
        return {
          month: cashflow.month || 1,
          user_name: cashflow.user_name || userName,
          income: {
            salary: cashflow.income?.salary || 0,
            investments: cashflow.income?.investments || 0,
            other: cashflow.income?.other || 0,
            total: cashflow.income?.total || 0,
            ...cashflow.income,
          },
          expenses: {
            housing: cashflow.expenses?.housing || 0,
            utilities: cashflow.expenses?.utilities || 0,
            groceries: cashflow.expenses?.groceries || 0,
            transportation: cashflow.expenses?.transportation || 0,
            healthcare: cashflow.expenses?.healthcare || 0,
            entertainment: cashflow.expenses?.entertainment || 0,
            dining_out: cashflow.expenses?.dining_out || 0,
            subscriptions: cashflow.expenses?.subscriptions || 0,
            other: cashflow.expenses?.other || 0,
            total: cashflow.expenses?.total || 0,
            ...cashflow.expenses,
          },
          savings: {
            amount: cashflow.savings?.amount || 0,
            percentage_of_income: cashflow.savings?.percentage_of_income || 0,
            target_met: cashflow.savings?.target_met || false,
            ...cashflow.savings,
          },
          balance: {
            starting: cashflow.balance?.starting || 0,
            ending: cashflow.balance?.ending || 0,
            change: cashflow.balance?.change || 0,
            ...cashflow.balance,
          },
          analysis: cashflow.analysis || {
            spending_categories: {
              essential: 0,
              non_essential: 0,
              ratio: 0,
            },
            savings_rate: "Unknown",
            cash_flow: "Unknown",
          },
          notes: cashflow.notes || "",
        };
      }
    );
  }

  return processedData;
};

// Function to run a direct simulation with real-time updates
export const getSimulationRealTimeUpdates = async (taskId, userId = null) => {
  try {
    // Set a timeout for the fetch request
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout

    // Ensure we have a valid user ID or use guest-user for anonymous users
    const userIdentifier = userId || "guest-user";

    console.log(
      "DEBUG - Getting real-time simulation updates for task:",
      taskId,
      "User ID:",
      userIdentifier
    );

    // Add user_id as a query parameter
    const url = new URL(`${API_BASE_URL}/simulation-results/${taskId}/updates`);
    url.searchParams.append("user_id", userIdentifier);

    // Fetch the simulation updates from the API
    const response = await fetch(url.toString(), {
      method: "GET",
      headers: {
        Accept: "application/json",
      },
      signal: controller.signal,
    });

    // Clear the timeout
    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorText = await response.text();
      console.error("DEBUG - Simulation Updates Error Response:", errorText);
      throw new Error(`API error: ${response.status} - ${errorText}`);
    }

    // Get the response data
    try {
      const responseText = await response.text();
      console.log("DEBUG - Simulation Updates Raw Response:", responseText);

      // Try to parse as JSON
      if (responseText) {
        try {
          const responseData = JSON.parse(responseText);
          console.log(
            "DEBUG - Simulation Updates Parsed Response:",
            responseData
          );

          // Process the standardized cashflow data if available
          const processedData = processFinancialSimulationData(
            responseData.data || {},
            responseData.user_name || "Guest User"
          );

          // Return standardized response with user name included
          return {
            success: true,
            task_id: taskId,
            user_id: userIdentifier,
            user_name: responseData.user_name || "Guest User",
            task_status:
              responseData.status || responseData.task_status || "unknown",
            data: processedData,
            partial_results: responseData.partial_results || true, // These are always partial results
            progress: responseData.progress || 0,
            ...responseData,
          };
        } catch (parseError) {
          console.error(
            "DEBUG - Simulation Updates JSON Parse Error:",
            parseError
          );
          // If it's not valid JSON, return the text as is
          return {
            success: false,
            error: "Invalid JSON response",
            message: responseText,
          };
        }
      } else {
        // Empty response but status was OK
        return {
          success: false,
          error: "Empty response from server",
        };
      }
    } catch (responseError) {
      console.error("DEBUG - Simulation Updates Reading Error:", responseError);
      return { success: false, error: "Failed to read response" };
    }
  } catch (error) {
    console.error("DEBUG - Simulation Updates Error:", error);

    if (error.name === "AbortError") {
      return {
        success: false,
        error: "Request to get simulation updates timed out",
      };
    } else if (
      error instanceof TypeError &&
      error.message === "Failed to fetch"
    ) {
      return {
        success: false,
        error: "Could not connect to financial simulation server",
      };
    }

    return { success: false, error: error.message };
  }
};

// Function to send user learning data
export const sendUserLearningData = async (
  message,
  userId = null,
  pdfId = null,
  wait = false // Default to asynchronous processing
) => {
  try {
    // Set a timeout for the fetch request
    const controller = new AbortController();
    const timeoutId = setTimeout(
      () => controller.abort(),
      wait ? 30000 : 10000
    ); // Longer timeout for synchronous requests

    // Ensure we have a valid user ID or use guest-user for anonymous users
    const userIdentifier = userId || "guest-user";

    // Use a default pdf_id if none is provided
    const documentId = pdfId || "default-document";

    console.log("DEBUG - Sending learning data:", {
      query: message ? message.substring(0, 50) + "..." : "null",
      user_id: userIdentifier,
      pdf_id: documentId,
      wait: wait,
    });

    // Create request body in the required format
    const requestBody = {
      user_id: userIdentifier,
      query: message,
      wait: wait, // Add wait parameter to control async/sync processing
    };

    // Only include pdf_id if it's provided and not a default value
    if (pdfId && pdfId !== "agent-simulator" && pdfId !== "default-document") {
      requestBody.pdf_id = pdfId;
    }

    // Send the data to the API
    const response = await fetch(`${API_BASE_URL}/user/learning`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(requestBody),
      signal: controller.signal,
    });

    // Clear the timeout
    clearTimeout(timeoutId);

    // Log the response status
    console.log("DEBUG - Learning API Response Status:", response.status);

    if (!response.ok) {
      const errorText = await response.text();
      console.error("DEBUG - Learning API Error Response:", errorText);
      throw new Error(`API error: ${response.status} - ${errorText}`);
    }

    // Get the response data
    try {
      const responseText = await response.text();
      console.log("DEBUG - Learning API Raw Response:", responseText);

      // Try to parse as JSON
      if (responseText) {
        try {
          const responseData = JSON.parse(responseText);
          console.log("DEBUG - Learning API Parsed Response:", responseData);

          // Check if this is an async response with a task_id
          if (responseData.learning_task_id && !wait) {
            return {
              success: true,
              isAsync: true,
              learning_task_id: responseData.learning_task_id,
              status: responseData.status || "queued", // Use "queued" as default status
              response:
                responseData.response || "Your question is being processed...",
              ...responseData,
            };
          }

          return {
            success: true,
            isAsync: false,
            ...responseData,
          };
        } catch (parseError) {
          console.error("DEBUG - Learning API JSON Parse Error:", parseError);
          // If it's not valid JSON, return the text as is
          return { success: true, message: responseText };
        }
      } else {
        // Empty response but status was OK
        return { success: true, message: "Request processed successfully" };
      }
    } catch (responseError) {
      console.error(
        "DEBUG - Learning API Response Reading Error:",
        responseError
      );
      return { success: false, error: "Failed to read response" };
    }
  } catch (error) {
    console.error("DEBUG - Learning API Error:", error);

    if (error.name === "AbortError") {
      return { success: false, error: "Request timed out" };
    } else if (
      error instanceof TypeError &&
      error.message === "Failed to fetch"
    ) {
      return { success: false, error: "Connection failed" };
    }

    return { success: false, error: error.message };
  }
};

// Function to check the status of a learning task
export const checkLearningTaskStatus = async (taskId, userId = null) => {
  try {
    // Set a timeout for the fetch request
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout

    // Ensure we have a valid user ID or use guest-user for anonymous users
    const userIdentifier = userId || "guest-user";

    console.log("DEBUG - Checking learning task status:", {
      learning_task_id: taskId,
      user_id: userIdentifier,
    });

    // Add user_id as a query parameter
    const url = new URL(`${API_BASE_URL}/user/learning/${taskId}`);
    url.searchParams.append("user_id", userIdentifier);

    // Send the request to check task status
    const response = await fetch(url.toString(), {
      method: "GET",
      headers: {
        Accept: "application/json",
      },
      signal: controller.signal,
    });

    // Clear the timeout
    clearTimeout(timeoutId);

    // Log the response status
    console.log("DEBUG - Task Status API Response Status:", response.status);

    if (!response.ok) {
      const errorText = await response.text();
      console.error("DEBUG - Task Status API Error Response:", errorText);
      throw new Error(`API error: ${response.status} - ${errorText}`);
    }

    // Get the response data
    try {
      const responseText = await response.text();
      console.log("DEBUG - Task Status API Raw Response:", responseText);

      // Try to parse as JSON
      if (responseText) {
        try {
          const responseData = JSON.parse(responseText);
          console.log("DEBUG - Task Status API Parsed Response:", responseData);

          // Return the response with standardized fields
          return {
            success: true,
            learning_task_id: taskId,
            status: responseData.status || "unknown",
            response: responseData.response || null,
            chat_history: responseData.chat_history || [],
            ...responseData,
          };
        } catch (parseError) {
          console.error(
            "DEBUG - Task Status API JSON Parse Error:",
            parseError
          );
          // If it's not valid JSON, return the text as is
          return {
            success: true,
            learning_task_id: taskId,
            message: responseText,
            status: "unknown",
          };
        }
      } else {
        // Empty response but status was OK
        return {
          success: true,
          learning_task_id: taskId,
          message: "Task status checked successfully",
          status: "unknown",
        };
      }
    } catch (responseError) {
      console.error(
        "DEBUG - Task Status API Response Reading Error:",
        responseError
      );
      return {
        success: false,
        task_id: taskId,
        error: "Failed to read response",
        status: "failed",
      };
    }
  } catch (error) {
    console.error("DEBUG - Task Status API Error:", error);

    if (error.name === "AbortError") {
      return {
        success: false,
        task_id: taskId,
        error: "Request timed out",
        status: "failed",
      };
    } else if (
      error instanceof TypeError &&
      error.message === "Failed to fetch"
    ) {
      return {
        success: false,
        task_id: taskId,
        error: "Connection failed",
        status: "failed",
      };
    }

    return {
      success: false,
      task_id: taskId,
      error: error.message,
      status: "failed",
    };
  }
};

// Function to notify when a PDF is removed
export const notifyPdfRemoved = async (pdfId, userId = null) => {
  try {
    // Set a timeout for the fetch request
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout

    // Ensure we have a valid user ID or use guest-user for anonymous users
    const userIdentifier = userId || "guest-user";

    console.log("DEBUG - Notifying PDF removal:", {
      pdf_id: pdfId,
      user_id: userIdentifier,
    });

    const response = await fetch(`${API_BASE_URL}/pdf/removed`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        user_id: userIdentifier,
        pdf_id: pdfId,
      }),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorText = await response.text();
      console.error("DEBUG - PDF Removal Error Response:", errorText);
      return {
        success: false,
        error: `API error: ${response.status} - ${errorText}`,
      };
    }

    // Get the response data
    try {
      const responseText = await response.text();
      console.log("DEBUG - PDF Removal Raw Response:", responseText);

      // Try to parse as JSON
      if (responseText) {
        try {
          const responseData = JSON.parse(responseText);
          console.log("DEBUG - PDF Removal Parsed Response:", responseData);
          return {
            success: true,
            ...responseData,
          };
        } catch (parseError) {
          console.error("DEBUG - PDF Removal JSON Parse Error:", parseError);
          // If it's not valid JSON, return the text as is
          return { success: true, message: responseText };
        }
      } else {
        // Empty response but status was OK
        return {
          success: true,
          message: "PDF removal notification sent successfully",
        };
      }
    } catch (responseError) {
      console.error(
        "DEBUG - PDF Removal Response Reading Error:",
        responseError
      );
      return { success: false, error: "Failed to read response" };
    }
  } catch (error) {
    console.error("DEBUG - PDF Removal Error:", error);

    if (error.name === "AbortError") {
      return {
        success: false,
        error: "PDF removal notification timed out",
      };
    } else if (
      error instanceof TypeError &&
      error.message === "Failed to fetch"
    ) {
      return { success: false, error: "Connection failed" };
    }

    return { success: false, error: error.message };
  }
};

// Function to upload PDF for chat
export const uploadPdfForChat = async (file, userId = null) => {
  try {
    // Set a timeout for the fetch request
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout

    // Ensure we have a valid user ID or use guest-user for anonymous users
    const userIdentifier = userId || "guest-user";

    // Create FormData with the required format: {"user_id": "string", "pdf_file": selectedpdf.pdf}
    const formData = new FormData();
    formData.append("pdf_file", file);
    formData.append("user_id", userIdentifier);

    console.log("DEBUG - Uploading PDF for chat:", {
      filename: file.name,
      filesize: file.size,
      user_id: userIdentifier,
    });

    const response = await fetch(`${API_BASE_URL}/pdf/chat`, {
      method: "POST",
      body: formData,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorText = await response.text();
      console.error("DEBUG - PDF Upload Error Response:", errorText);
      throw new Error(`API error: ${response.status} - ${errorText}`);
    }

    // Get the response data
    try {
      const responseText = await response.text();
      console.log("DEBUG - PDF Upload Raw Response:", responseText);

      // Try to parse as JSON
      if (responseText) {
        try {
          const responseData = JSON.parse(responseText);
          console.log("DEBUG - PDF Upload Parsed Response:", responseData);
          return {
            success: true,
            pdf_id: responseData.pdf_id || responseData.id,
            ...responseData,
          };
        } catch (parseError) {
          console.error("DEBUG - PDF Upload JSON Parse Error:", parseError);
          // If it's not valid JSON, return the text as is
          return { success: true, message: responseText };
        }
      } else {
        // Empty response but status was OK
        return { success: true, message: "PDF uploaded successfully" };
      }
    } catch (responseError) {
      console.error(
        "DEBUG - PDF Upload Response Reading Error:",
        responseError
      );
      return { success: false, error: "Failed to read response" };
    }
  } catch (error) {
    console.error("DEBUG - PDF Upload Error:", error);

    if (error.name === "AbortError") {
      return {
        success: false,
        error: "PDF upload timed out - the server is not responding",
      };
    } else if (
      error instanceof TypeError &&
      error.message === "Failed to fetch"
    ) {
      return { success: false, error: "Connection failed" };
    }

    return { success: false, error: error.message };
  }
};
