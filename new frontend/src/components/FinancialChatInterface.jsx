import React, { useState, useRef, useEffect } from "react";
import { useTranslation } from "react-i18next";
import {
  MessageSquare,
  Send,
  Bot,
  User,
  DollarSign,
  TrendingUp,
  PieChart,
  Target,
  AlertCircle,
  Lightbulb,
  Activity,
  Shield
} from "lucide-react";
import { toast } from "react-hot-toast";
import { useSendFinancialChatMessageMutation } from "../api/financialChatApiSlice";

/**
 * Financial Chat Interface Component
 * Provides AI-powered chat for financial guidance based on simulation data
 */
const FinancialChatInterface = ({ 
  financialData, 
  simulationResults, 
  userId,
  className = "" 
}) => {
  const { t } = useTranslation();
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // RTK Query mutation
  const [sendFinancialChatMessage] = useSendFinancialChatMessageMutation();

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Validate financial data availability
  const hasFinancialData = financialData && Object.keys(financialData).length > 0;
  const hasSimulationResults = simulationResults && Object.keys(simulationResults).length > 0;

  // Initialize with welcome message
  useEffect(() => {
    if (messages.length === 0) {
      let welcomeContent = "Hello! I'm your AI Financial Advisor powered by Llama AI.";
      let suggestions = [];

      if (hasFinancialData || hasSimulationResults) {
        welcomeContent += " I can analyze your financial simulation data and provide personalized recommendations. What would you like to know about your finances?";
        suggestions = [
          "Analyze my current financial health",
          "How can I improve my savings rate?",
          "Review my spending patterns",
          "What are my biggest financial risks?",
          "Give me investment advice based on my data",
          "How am I doing compared to my goals?"
        ];
      } else {
        welcomeContent += " I notice you don't have any financial simulation data yet. Please start a financial simulation first, then I can provide personalized advice based on your data.";
        suggestions = [
          "How do I start a financial simulation?",
          "What financial data should I track?",
          "Give me general financial advice",
          "What are the basics of budgeting?"
        ];
      }

      const welcomeMessage = {
        id: Date.now(),
        type: "assistant",
        content: welcomeContent,
        timestamp: new Date().toISOString(),
        suggestions: suggestions
      };
      setMessages([welcomeMessage]);
    }
  }, [hasFinancialData, hasSimulationResults]);

  // Prepare financial context for AI
  const prepareFinancialContext = () => {
    // Calculate additional insights
    const currentMonth = simulationResults?.current_month || 1;
    const monthlyData = simulationResults?.monthly_data || [];
    const latestMonth = monthlyData[currentMonth - 1] || {};

    // Calculate trends
    const calculateTrend = (field) => {
      if (monthlyData.length < 2) return "stable";
      const recent = monthlyData.slice(-3).map(m => m[field] || 0);
      const avg = recent.reduce((a, b) => a + b, 0) / recent.length;
      const latest = recent[recent.length - 1];
      if (latest > avg * 1.1) return "increasing";
      if (latest < avg * 0.9) return "decreasing";
      return "stable";
    };

    const context = {
      // Basic profile information
      user_profile: {
        monthly_income: financialData?.monthly_income || latestMonth?.income || 0,
        monthly_expenses: financialData?.monthly_expenses || latestMonth?.expenses || 0,
        savings_goal: financialData?.savings_goal || 0,
        debt_info: financialData?.debt || {},
        investment_accounts: financialData?.investment_accounts || {}
      },

      // Current simulation status
      simulation_status: {
        current_month: currentMonth,
        total_months: simulationResults?.total_months || 12,
        progress_percentage: Math.round((currentMonth / (simulationResults?.total_months || 12)) * 100)
      },

      // Financial performance metrics
      performance_metrics: {
        total_income: simulationResults?.total_income || 0,
        total_expenses: simulationResults?.total_expenses || 0,
        total_savings: simulationResults?.total_savings || 0,
        savings_rate: simulationResults?.savings_rate || 0,
        financial_health_score: simulationResults?.financial_health_score || 0,
        emergency_fund_current: latestMonth?.emergency_fund || 0
      },

      // Trends analysis
      trends: {
        income_trend: calculateTrend('income'),
        expense_trend: calculateTrend('expenses'),
        savings_trend: calculateTrend('savings'),
        emergency_fund_trend: calculateTrend('emergency_fund')
      },

      // Goals and targets
      goals: simulationResults?.goals || {},

      // Recent monthly data (last 3 months)
      recent_performance: monthlyData.slice(-3),

      // Key insights
      insights: {
        months_completed: currentMonth,
        months_remaining: (simulationResults?.total_months || 12) - currentMonth,
        average_monthly_savings: simulationResults?.total_savings ?
          Math.round(simulationResults.total_savings / currentMonth) : 0,
        debt_to_income_ratio: financialData?.debt && financialData?.monthly_income ?
          Math.round((Object.values(financialData.debt).reduce((a, b) => a + b, 0) /
          (financialData.monthly_income * 12)) * 100) : 0
      }
    };

    return context;
  };

  // Handle sending message
  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      type: "user",
      content: inputMessage.trim(),
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    const messageToSend = inputMessage.trim();
    setInputMessage("");
    setIsLoading(true);

    try {
      // Prepare financial context
      const financialContext = prepareFinancialContext();

      // Send message to AI
      const response = await sendFinancialChatMessage({
        message: messageToSend,
        financialContext: financialContext,
        userId: userId
      }).unwrap();

      // Process and enhance the response
      const responseContent = response.message || response.response || "I apologize, but I couldn't process your request at the moment. Please try again.";

      // Generate follow-up suggestions based on the response content
      const generateFollowUpSuggestions = (content) => {
        const suggestions = [];
        if (content.toLowerCase().includes('savings')) {
          suggestions.push("How can I automate my savings?");
        }
        if (content.toLowerCase().includes('debt')) {
          suggestions.push("What's the best debt payoff strategy for me?");
        }
        if (content.toLowerCase().includes('investment')) {
          suggestions.push("What's my risk tolerance for investments?");
        }
        if (content.toLowerCase().includes('budget')) {
          suggestions.push("Help me create a detailed monthly budget");
        }
        if (content.toLowerCase().includes('emergency')) {
          suggestions.push("How much should my emergency fund be?");
        }

        // Add some general follow-ups if no specific ones match
        if (suggestions.length === 0) {
          suggestions.push("What should I focus on next?", "Any other recommendations?");
        }

        return suggestions.slice(0, 3); // Limit to 3 suggestions
      };

      // Create assistant message
      const assistantMessage = {
        id: Date.now() + 1,
        type: "assistant",
        content: responseContent,
        timestamp: new Date().toISOString(),
        confidence: response.confidence || null,
        insights: response.insights || null,
        suggestions: generateFollowUpSuggestions(responseContent)
      };

      setMessages(prev => [...prev, assistantMessage]);

    } catch (error) {
      let errorMessage = "I'm sorry, I'm having trouble connecting to the financial analysis service. Please check your connection and try again.";

      // Provide more specific error messages
      if (error?.status === 404) {
        errorMessage = "The financial analysis service is currently unavailable. Please try again later.";
      } else if (error?.status === 429) {
        errorMessage = "Too many requests. Please wait a moment before asking another question.";
      } else if (error?.status >= 500) {
        errorMessage = "The financial analysis service is experiencing issues. Please try again in a few minutes.";
      }

      // Add error message
      const errorMsg = {
        id: Date.now() + 1,
        type: "assistant",
        content: errorMessage,
        timestamp: new Date().toISOString(),
        isError: true
      };

      setMessages(prev => [...prev, errorMsg]);
      toast.error("Failed to get financial advice. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  // Handle suggestion click
  const handleSuggestionClick = (suggestion) => {
    setInputMessage(suggestion);
    inputRef.current?.focus();
  };

  // Handle key press
  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Format timestamp
  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  // Get key financial metrics for display
  const getKeyMetrics = () => {
    if (!hasFinancialData && !hasSimulationResults) return null;

    const context = prepareFinancialContext();
    return {
      savingsRate: context.performance_metrics?.savings_rate || 0,
      healthScore: context.performance_metrics?.financial_health_score || 0,
      currentMonth: context.simulation_status?.current_month || 0,
      totalMonths: context.simulation_status?.total_months || 12
    };
  };

  const keyMetrics = getKeyMetrics();

  return (
    <div className={`flex flex-col h-full bg-gradient-to-br from-blue-900/20 to-purple-900/20 rounded-lg border border-blue-500/30 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between p-6 border-b border-blue-500/30">
        <div className="flex items-center">
          <div className="w-12 h-12 bg-blue-500/20 rounded-full flex items-center justify-center mr-4">
            <Bot size={24} className="text-blue-400" />
          </div>
          <div>
            <h3 className="text-white font-semibold text-lg">Financial AI Advisor</h3>
            <p className="text-sm text-white/70">Powered by Llama AI</p>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          <DollarSign size={20} className="text-green-400" />
          <TrendingUp size={20} className="text-blue-400" />
          <PieChart size={20} className="text-purple-400" />
        </div>
      </div>

      {/* Financial Metrics Bar */}
      {keyMetrics && (
        <div className="px-6 py-2 bg-gray-800/30 border-b border-blue-500/20">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center space-x-6">
              <div className="flex items-center">
                <Target size={16} className="text-green-400 mr-2" />
                <span className="text-white/80 font-medium">Savings Rate:</span>
                <span className="text-green-400 ml-2 font-semibold text-lg">{keyMetrics.savingsRate}%</span>
              </div>
              <div className="flex items-center">
                <Activity size={16} className="text-blue-400 mr-2" />
                <span className="text-white/80 font-medium">Health Score:</span>
                <span className="text-blue-400 ml-2 font-semibold text-lg">{keyMetrics.healthScore}/100</span>
              </div>
            </div>
            <div className="flex items-center">
              <span className="text-white/80 font-medium">Progress:</span>
              <span className="text-purple-400 ml-2 font-semibold text-lg">
                {keyMetrics.currentMonth}/{keyMetrics.totalMonths} months
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar min-h-[350px]">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.type === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[85%] rounded-lg p-4 ${
                message.type === "user"
                  ? "bg-blue-600/30 border border-blue-500/40 text-white"
                  : message.isError
                  ? "bg-red-900/30 border border-red-500/40 text-red-200"
                  : "bg-gray-800/50 border border-gray-600/40 text-white"
              }`}
            >
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0 mt-1">
                  {message.type === "user" ? (
                    <User size={16} className="text-blue-400" />
                  ) : (
                    <Bot size={16} className={message.isError ? "text-red-400" : "text-green-400"} />
                  )}
                </div>
                <div className="flex-1">
                  <p className="text-sm leading-relaxed mb-2">{message.content}</p>
                  
                  {/* Show suggestions for assistant messages */}
                  {message.suggestions && (
                    <div className="mt-3 space-y-2">
                      <p className="text-xs text-white/70 font-medium">Quick questions:</p>
                      {message.suggestions.map((suggestion, index) => (
                        <button
                          key={index}
                          onClick={() => handleSuggestionClick(suggestion)}
                          className="block w-full text-left text-sm bg-blue-600/20 hover:bg-blue-600/30 border border-blue-500/30 rounded-md px-3 py-2 text-blue-200 transition-colors"
                        >
                          {suggestion}
                        </button>
                      ))}
                    </div>
                  )}
                  
                  <div className="flex items-center justify-between mt-2">
                    <span className="text-xs text-white/50">
                      {formatTime(message.timestamp)}
                    </span>
                    {message.confidence && (
                      <span className="text-xs text-white/70">
                        Confidence: {Math.round(message.confidence * 100)}%
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        ))}
        
        {/* Loading indicator */}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-800/50 border border-gray-600/40 rounded-lg p-3">
              <div className="flex items-center space-x-2">
                <Bot size={16} className="text-green-400" />
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: "0.1s" }}></div>
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: "0.2s" }}></div>
                </div>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Quick Actions */}
      <div className="px-6 py-4 border-t border-blue-500/30">
        <div className="flex flex-wrap gap-3 mb-3">
          <button
            onClick={() => handleSuggestionClick("Analyze my current financial health and provide a detailed assessment")}
            disabled={isLoading}
            className="flex items-center px-3 py-2 text-sm bg-green-600/20 hover:bg-green-600/30 border border-green-500/40 rounded-lg text-green-200 transition-colors disabled:opacity-50 font-medium"
          >
            <Activity size={16} className="mr-2" />
            Health Check
          </button>
          <button
            onClick={() => handleSuggestionClick("How can I improve my savings rate? Give me specific strategies based on my data")}
            disabled={isLoading}
            className="flex items-center px-3 py-2 text-sm bg-blue-600/20 hover:bg-blue-600/30 border border-blue-500/40 rounded-lg text-blue-200 transition-colors disabled:opacity-50 font-medium"
          >
            <Target size={16} className="mr-2" />
            Savings Tips
          </button>
          <button
            onClick={() => handleSuggestionClick("Review my spending patterns and identify areas where I can cut costs")}
            disabled={isLoading}
            className="flex items-center px-3 py-2 text-sm bg-purple-600/20 hover:bg-purple-600/30 border border-purple-500/40 rounded-lg text-purple-200 transition-colors disabled:opacity-50 font-medium"
          >
            <PieChart size={16} className="mr-2" />
            Spending
          </button>
          <button
            onClick={() => handleSuggestionClick("What are my biggest financial risks and how can I mitigate them?")}
            disabled={isLoading}
            className="flex items-center px-3 py-2 text-sm bg-red-600/20 hover:bg-red-600/30 border border-red-500/40 rounded-lg text-red-200 transition-colors disabled:opacity-50 font-medium"
          >
            <AlertCircle size={16} className="mr-2" />
            Risks
          </button>
        </div>
        <div className="flex flex-wrap gap-3">
          <button
            onClick={() => handleSuggestionClick("Am I on track to meet my financial goals? What should I adjust?")}
            disabled={isLoading}
            className="flex items-center px-3 py-2 text-sm bg-yellow-600/20 hover:bg-yellow-600/30 border border-yellow-500/40 rounded-lg text-yellow-200 transition-colors disabled:opacity-50 font-medium"
          >
            <Target size={16} className="mr-2" />
            Goal Progress
          </button>
          <button
            onClick={() => handleSuggestionClick("What investment strategies do you recommend based on my financial situation?")}
            disabled={isLoading}
            className="flex items-center px-3 py-2 text-sm bg-indigo-600/20 hover:bg-indigo-600/30 border border-indigo-500/40 rounded-lg text-indigo-200 transition-colors disabled:opacity-50 font-medium"
          >
            <TrendingUp size={16} className="mr-2" />
            Investments
          </button>
          <button
            onClick={() => handleSuggestionClick("How does my emergency fund look? Should I prioritize building it more?")}
            disabled={isLoading}
            className="flex items-center px-3 py-2 text-sm bg-orange-600/20 hover:bg-orange-600/30 border border-orange-500/40 rounded-lg text-orange-200 transition-colors disabled:opacity-50 font-medium"
          >
            <Shield size={16} className="mr-2" />
            Emergency Fund
          </button>
          <button
            onClick={() => handleSuggestionClick("Give me a comprehensive financial plan for the next 6 months")}
            disabled={isLoading}
            className="flex items-center px-3 py-2 text-sm bg-cyan-600/20 hover:bg-cyan-600/30 border border-cyan-500/40 rounded-lg text-cyan-200 transition-colors disabled:opacity-50 font-medium"
          >
            <Lightbulb size={16} className="mr-2" />
            6-Month Plan
          </button>
        </div>
      </div>

      {/* Input */}
      <div className="p-6 border-t border-blue-500/30">
        <div className="flex items-center space-x-3">
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={t("Ask about your finances...")}
              className="w-full bg-blue-600/20 border border-blue-500/40 rounded-lg py-3 px-4 pr-12 text-white text-base resize-none focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/60"
              rows="1"
              style={{ minHeight: "48px", maxHeight: "120px" }}
              disabled={isLoading}
            />
          </div>
          <button
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || isLoading}
            className="p-3 bg-blue-600/30 hover:bg-blue-600/50 disabled:bg-gray-600/30 disabled:cursor-not-allowed border border-blue-500/40 rounded-lg text-white transition-colors"
          >
            <Send size={20} />
          </button>
        </div>
      </div>
    </div>
  );
};

export default FinancialChatInterface;
