import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";
import { FINANCIAL_API_BASE_URL } from "../config";

// Create a separate API slice for financial simulation endpoints using port 8002
export const financialApiSlice = createApi({
  reducerPath: "financialApi",
  baseQuery: fetchBaseQuery({
    baseUrl: FINANCIAL_API_BASE_URL,
    timeout: 60000, // 60 second timeout for financial simulations
  }),
  tagTypes: ["FinancialSimulation"],
  endpoints: (builder) => ({
    // Start financial simulation
    startFinancialSimulation: builder.mutation({
      query: (simulationData) => ({
        url: "/start-simulation",
        method: "POST",
        body: simulationData,
      }),
      invalidatesTags: ["FinancialSimulation"],
    }),

    // Check simulation status
    getSimulationStatus: builder.query({
      query: (taskId) => `/simulation-status/${taskId}`,
      providesTags: (result, error, taskId) => [
        { type: "FinancialSimulation", id: taskId },
      ],
    }),

    // Get simulation results by task ID
    getSimulationResultsByTaskId: builder.query({
      query: (taskId) => `/simulation-results/${taskId}`,
      providesTags: (result, error, taskId) => [
        { type: "FinancialSimulation", id: `results-${taskId}` },
      ],
    }),



    // Get real-time simulation updates
    getSimulationRealTimeUpdates: builder.query({
      query: (taskId) => `/simulation-results/${taskId}`,
      providesTags: (result, error, taskId) => [
        { type: "FinancialSimulation", id: `updates-${taskId}` },
      ],
    }),

    // Run direct simulation (synchronous)
    runDirectSimulation: builder.mutation({
      query: (userData) => ({
        url: "/run-direct-simulation",
        method: "POST",
        body: userData,
      }),
      invalidatesTags: ["FinancialSimulation"],
    }),

    // Create financial forecast
    createFinancialForecast: builder.mutation({
      query: (forecastData) => ({
        url: "/forecast",
        method: "POST",
        body: forecastData,
      }),
      invalidatesTags: ["FinancialSimulation"],
    }),
  }),
});

export const {
  useStartFinancialSimulationMutation,
  useGetSimulationStatusQuery,
  useLazyGetSimulationStatusQuery,
  useGetSimulationResultsByTaskIdQuery,
  useLazyGetSimulationResultsByTaskIdQuery,
  useGetSimulationRealTimeUpdatesQuery,
  useLazyGetSimulationRealTimeUpdatesQuery,
  useRunDirectSimulationMutation,
  useCreateFinancialForecastMutation,
} = financialApiSlice;
