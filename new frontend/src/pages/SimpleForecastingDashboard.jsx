import React, { useState, useEffect } from 'react';
import { TrendingUp, Activity, Brain, AlertTriangle, CheckCircle, Clock, Target, BarChart3, RefreshCw } from 'lucide-react';
import GlassContainer from '../components/GlassContainer';
import GlassButton from '../components/GlassButton';
import toast from 'react-hot-toast';

// Utility function for robust date formatting
const formatDateSafely = (dateString) => {
  try {
    // Handle various date formats
    let date;

    if (dateString.includes('T')) {
      // ISO format with time
      date = new Date(dateString);
    } else {
      // Date only format - add time to avoid timezone issues
      date = new Date(dateString + 'T12:00:00'); // Use noon to avoid timezone issues
    }

    if (isNaN(date.getTime())) {
      console.error('Invalid date:', dateString);
      return dateString; // Return original if parsing fails
    }

    return `${(date.getMonth() + 1).toString().padStart(2, '0')}/${date.getDate().toString().padStart(2, '0')}/${date.getFullYear()}`;
  } catch (error) {
    console.error('Date formatting error:', error, 'for date:', dateString);
    return dateString; // Return original if error occurs
  }
};

// Generate consistent future dates
const generateFutureDates = (startDaysFromNow = 1, count = 30) => {
  const dates = [];
  const today = new Date();

  for (let i = 0; i < count; i++) {
    const futureDate = new Date(today.getTime() + ((startDaysFromNow + i) * 24 * 60 * 60 * 1000));
    dates.push(futureDate.toISOString().split('T')[0]);
  }

  return dates;
};

const SimpleForecastingDashboard = () => {
  const [forecastData, setForecastData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [systemStatus, setSystemStatus] = useState(null);
  const [selectedMetricType, setSelectedMetricType] = useState('general');
  const [forecastPeriods, setForecastPeriods] = useState(30);
  const [refreshKey, setRefreshKey] = useState(0); // Force re-render

  // Sample data for demonstration
  const generateSampleData = (type) => {
    const data = [];
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - 60); // 60 days of historical data

    for (let i = 0; i < 60; i++) {
      // More robust date calculation
      const date = new Date(startDate.getTime() + (i * 24 * 60 * 60 * 1000));
      
      let value;
      switch (type) {
        case 'probability':
          value = Math.max(0, Math.min(1, 0.3 + 0.4 * Math.sin(i / 10) + Math.random() * 0.2));
          break;
        case 'load':
          value = 50 + 30 * Math.sin(i / 7) + 20 * Math.sin(i / 30) + Math.random() * 10;
          break;
        default:
          value = 100 + 50 * Math.sin(i / 15) + Math.random() * 20;
      }

      data.push({
        date: date.toISOString().split('T')[0],
        value: Math.round(value * 100) / 100
      });
    }
    return data;
  };

  const checkSystemStatus = async () => {
    try {
      const response = await fetch('http://localhost:8006/forecast/status');
      if (response.ok) {
        const status = await response.json();
        setSystemStatus(status);
        return status.forecasting_enabled;
      }
    } catch (error) {
      console.error('Failed to check system status:', error);
      setSystemStatus({ forecasting_enabled: false, error: error.message });
      return false;
    }
  };

  const forceRefreshForecast = () => {
    console.log('🔄 Force refreshing forecast data...');
    setForecastData(null);
    setRefreshKey(prev => prev + 1); // Force component re-render

    // Test date generation immediately
    const testToday = new Date();
    console.log('🧪 Test - Current date:', testToday.toISOString());

    const testFutureDates = [];
    for (let i = 1; i <= 5; i++) {
      const futureDate = new Date(testToday.getTime() + (i * 24 * 60 * 60 * 1000));
      const dateString = futureDate.toISOString().split('T')[0];
      testFutureDates.push(dateString);
      console.log(`🧪 Test date ${i}:`, dateString, '-> formatted:', formatDateSafely(dateString));
    }

    generateForecast();
  };

  const generateForecast = async () => {
    setLoading(true);
    setForecastData(null); // Clear previous data
    console.log('🔄 Generating fresh forecast with current dates...');

    try {
      // Check if backend is available
      const isSystemReady = await checkSystemStatus();

      if (!isSystemReady) {
        // Use demo data if backend is not available
        toast.error('Backend not available - showing demo data');
        const demoData = generateDemoForecast();
        setForecastData(demoData);
        setLoading(false);
        return;
      }

      const sampleData = generateSampleData(selectedMetricType);
      
      const response = await fetch('http://localhost:8006/forecast', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          data: sampleData,
          metric_type: selectedMetricType,
          forecast_periods: forecastPeriods,
          user_id: 'demo_user'
        })
      });

      if (response.ok) {
        const result = await response.json();
        setForecastData(result);
        toast.success('Forecast generated successfully!');
      } else {
        throw new Error(`HTTP ${response.status}`);
      }
    } catch (error) {
      console.error('Forecast generation failed:', error);
      toast.error('Using demo data - backend unavailable');
      const demoData = generateDemoForecast();
      setForecastData(demoData);
    }
    setLoading(false);
  };

  const generateDemoForecast = () => {
    const forecastData = [];

    // Force fresh date generation every time
    const today = new Date();
    console.log('🔄 Current date:', today.toISOString());

    const futureDates = [];
    for (let i = 1; i <= forecastPeriods; i++) {
      const futureDate = new Date(today.getTime() + (i * 24 * 60 * 60 * 1000));
      const dateString = futureDate.toISOString().split('T')[0];
      futureDates.push(dateString);
    }

    // Debug: log the generated dates
    console.log('🗓️ Generated future dates:', futureDates.slice(0, 5));

    futureDates.forEach((dateString, i) => {
      let baseValue;
      switch (selectedMetricType) {
        case 'probability':
          baseValue = 0.4 + 0.3 * Math.sin((i + 1) / 10);
          break;
        case 'load':
          baseValue = 60 + 25 * Math.sin((i + 1) / 7);
          break;
        default:
          baseValue = 120 + 40 * Math.sin((i + 1) / 15);
      }

      const noise = (Math.random() - 0.5) * 0.1 * baseValue;
      const predicted_value = Math.max(0, baseValue + noise);

      forecastData.push({
        date: dateString,
        predicted_value: Math.round(predicted_value * 100) / 100,
        lower_bound: Math.round((predicted_value * 0.9) * 100) / 100,
        upper_bound: Math.round((predicted_value * 1.1) * 100) / 100
      });

      // Debug: log first few dates with detailed info
      if (i < 5) {
        const formattedDate = formatDateSafely(dateString);
        console.log(`📅 Date ${i + 1}: Raw="${dateString}" | Formatted="${formattedDate}" | Year=${new Date(dateString).getFullYear()}`);
      }
    });

    return {
      content: {
        status: 'success',
        forecast_data: forecastData,
        model_used: 'demo_prophet',
        accuracy_metrics: {
          mae: 2.45,
          rmse: 3.12,
          mape: 1.95
        },
        summary: {
          mean_prediction: forecastData.reduce((sum, d) => sum + d.predicted_value, 0) / forecastData.length,
          trend: forecastData[forecastData.length - 1].predicted_value > forecastData[0].predicted_value ? 'increasing' : 'decreasing'
        },
        recommendations: [
          'Demo forecast generated successfully',
          'Start the backend service to see real Prophet/ARIMA forecasting',
          'This demonstrates the forecasting dashboard capabilities'
        ]
      }
    };
  };

  useEffect(() => {
    console.log('🔍 SimpleForecastingDashboard mounted');
    checkSystemStatus();
  }, []);

  const getMetricTypeColor = () => {
    switch (selectedMetricType) {
      case 'probability': return '#FF9933'; // Saffron
      case 'load': return '#2E4A3F'; // Forest Green
      default: return '#FFFFFF'; // White
    }
  };

  // Simple ASCII chart component with proper date formatting
  const SimpleChart = ({ data }) => {
    if (!data || data.length === 0) return null;

    // Debug: log the first few data items to see what we're working with
    console.log('SimpleChart data sample:', data.slice(0, 3));

    const maxValue = Math.max(...data.map(d => d.predicted_value));
    const minValue = Math.min(...data.map(d => d.predicted_value));
    const range = maxValue - minValue;

    return (
      <div className="p-4 rounded-lg border-2" style={{
        background: 'rgba(255, 255, 255, 0.1)',
        backdropFilter: 'blur(12px)',
        border: '2px solid rgba(255, 215, 0, 0.3)'
      }}>
        <h4 className="font-semibold mb-3" style={{ color: '#FFFFFF' }}>Forecast Visualization</h4>
        <div className="space-y-1">
          {data.slice(0, 10).map((item, index) => {
            const percentage = range > 0 ? ((item.predicted_value - minValue) / range) * 100 : 50;
            return (
              <div key={index} className="flex items-center space-x-2 text-sm">
                <span className="w-20 text-xs font-medium" style={{ color: '#FFFFFF' }}>
                  {(() => {
                    // Force fresh date calculation for display
                    const today = new Date();
                    const displayDate = new Date(today.getTime() + ((index + 1) * 24 * 60 * 60 * 1000));
                    const formatted = `${(displayDate.getMonth() + 1).toString().padStart(2, '0')}/${displayDate.getDate().toString().padStart(2, '0')}/${displayDate.getFullYear()}`;
                    return formatted;
                  })()}
                </span>
                <div className="flex-1 rounded-full h-4 relative" style={{
                  background: 'rgba(255, 255, 255, 0.2)',
                  border: '1px solid rgba(255, 215, 0, 0.2)'
                }}>
                  <div
                    className="h-full rounded-full transition-all duration-300"
                    style={{
                      width: `${percentage}%`,
                      backgroundColor: getMetricTypeColor(),
                      boxShadow: `0 0 8px ${getMetricTypeColor()}40`
                    }}
                  />
                  <span className="absolute inset-0 flex items-center justify-center text-xs font-bold" style={{ color: '#000000' }}>
                    {item.predicted_value.toFixed(2)}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
        {data.length > 10 && (
          <p className="text-white/50 text-xs mt-2">
            Showing first 10 of {data.length} forecast points
          </p>
        )}
      </div>
    );
  };

  console.log('🎯 Rendering SimpleForecastingDashboard', { systemStatus, forecastData, loading });

  return (
    <div className="min-h-screen overflow-auto" style={{
      backgroundImage: 'url(/bg/bg.png)',
      backgroundSize: 'cover',
      backgroundPosition: 'center',
      backgroundRepeat: 'no-repeat',
      backgroundAttachment: 'fixed',
      backgroundColor: '#FDF6E3'
    }}>
      <div className="max-w-7xl mx-auto p-6 space-y-8">
        
        {/* Header */}
        <GlassContainer className="p-8" noFixedHeight={true}>
          <div className="flex items-center justify-between">
            <div className="space-y-3">
              <h1 className="text-4xl font-bold flex items-center" style={{ color: '#FFFFFF' }}>
                <TrendingUp className="mr-4 h-10 w-10" style={{ color: '#FF9933' }} />
                Advanced Forecasting Dashboard (Simple Version)
              </h1>
              <p className="text-lg" style={{ color: '#FFFFFF' }}>
                Prophet & ARIMA Time Series Forecasting - No External Dependencies
              </p>
            </div>
            <div className="flex items-center space-x-4">
              {systemStatus && (
                <div className={`flex items-center space-x-3 px-4 py-2 rounded-full font-medium border-2 ${
                  systemStatus.forecasting_enabled
                    ? 'border-[#FF9933] text-[#FFFFFF]'
                    : 'border-[#FFD700] text-[#FFFFFF]'
                }`} style={{
                  background: systemStatus.forecasting_enabled
                    ? 'rgba(255, 153, 51, 0.15)'
                    : 'rgba(255, 215, 0, 0.15)',
                  backdropFilter: 'blur(12px)'
                }}>
                  <div className={`w-3 h-3 rounded-full animate-pulse`} style={{
                    backgroundColor: systemStatus.forecasting_enabled ? '#FF9933' : '#FFD700'
                  }}></div>
                  <span className="text-sm font-semibold">
                    {systemStatus.forecasting_enabled ? 'System Ready' : 'Demo Mode'}
                  </span>
                </div>
              )}
            </div>
          </div>
        </GlassContainer>

        {/* Controls */}
        <GlassContainer className="p-8" noFixedHeight={true}>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 items-end">
            <div>
              <label className="block text-sm font-medium mb-3" style={{ color: '#FFFFFF' }}>Metric Type</label>
              <select
                value={selectedMetricType}
                onChange={(e) => setSelectedMetricType(e.target.value)}
                className="w-full rounded-lg px-4 py-3 transition-all border-2"
                style={{
                  background: 'rgba(255, 255, 255, 0.15)',
                  backdropFilter: 'blur(12px)',
                  border: '2px solid rgba(255, 215, 0, 0.3)',
                  color: '#FFFFFF',
                  fontWeight: '500'
                }}
              >
                <option value="general" style={{ background: '#FDF6E3', color: '#000000' }}>General</option>
                <option value="probability" style={{ background: '#FDF6E3', color: '#000000' }}>Probability (0-1)</option>
                <option value="load" style={{ background: '#FDF6E3', color: '#000000' }}>Load/Performance</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-3" style={{ color: '#FFFFFF' }}>Forecast Periods</label>
              <input
                type="number"
                value={forecastPeriods}
                onChange={(e) => setForecastPeriods(parseInt(e.target.value))}
                min="7"
                max="365"
                className="w-full rounded-lg px-4 py-3 transition-all border-2"
                style={{
                  background: 'rgba(255, 255, 255, 0.15)',
                  backdropFilter: 'blur(12px)',
                  border: '2px solid rgba(255, 215, 0, 0.3)',
                  color: '#FFFFFF',
                  fontWeight: '500'
                }}
              />
            </div>

            <GlassButton
              onClick={generateForecast}
              disabled={loading}
              className="flex items-center space-x-2"
            >
              <TrendingUp size={16} />
              <span>{loading ? 'Generating...' : 'Generate Forecast'}</span>
            </GlassButton>

            <GlassButton
              onClick={forceRefreshForecast}
              disabled={loading}
              variant="secondary"
              className="flex items-center space-x-2"
            >
              <RefreshCw size={16} />
              <span>Refresh Dates</span>
            </GlassButton>
          </div>
        </GlassContainer>

        {/* Forecast Results */}
        {forecastData && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            
            {/* Main Chart */}
            <div className="lg:col-span-2">
              <GlassContainer className="p-8">
                <h3 className="text-2xl font-bold mb-6 flex items-center" style={{ color: '#FFFFFF' }}>
                  <Activity className="mr-3 h-6 w-6" style={{ color: '#FF9933' }} />
                  Forecast Visualization
                </h3>

                <SimpleChart key={refreshKey} data={forecastData.content.forecast_data} />
              </GlassContainer>
            </div>

            {/* Summary Stats */}
            <div className="space-y-4">
              <GlassContainer className="p-6">
                <h4 className="text-lg font-bold mb-3" style={{ color: '#FFFFFF' }}>Forecast Summary</h4>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span style={{ color: '#FFFFFF' }}>Model Used:</span>
                    <span className="font-semibold" style={{ color: '#FFFFFF' }}>
                      {forecastData.content.model_used?.toUpperCase() || 'N/A'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span style={{ color: '#FFFFFF' }}>Mean Prediction:</span>
                    <span className="font-semibold" style={{ color: '#FFFFFF' }}>
                      {forecastData.content.summary?.mean_prediction?.toFixed(2) || 'N/A'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span style={{ color: '#FFFFFF' }}>Trend:</span>
                    <span className="font-semibold" style={{
                      color: forecastData.content.summary?.trend === 'increasing'
                        ? '#FF9933'
                        : '#D6A76C'
                    }}>
                      {forecastData.content.summary?.trend || 'N/A'}
                    </span>
                  </div>
                </div>
              </GlassContainer>

              <GlassContainer className="p-4">
                <h4 className="text-lg font-bold text-white mb-3">Accuracy Metrics</h4>
                <div className="space-y-3">
                  {forecastData.content.accuracy_metrics && Object.entries(forecastData.content.accuracy_metrics).map(([key, value]) => (
                    <div key={key} className="flex justify-between">
                      <span className="text-white/70">{key.toUpperCase()}:</span>
                      <span className="text-white font-semibold">
                        {typeof value === 'number' ? value.toFixed(3) : value}
                      </span>
                    </div>
                  ))}
                </div>
              </GlassContainer>

              <GlassContainer className="p-4">
                <h4 className="text-lg font-bold text-white mb-3">Recommendations</h4>
                <div className="space-y-2">
                  {forecastData.content.recommendations?.map((rec, index) => (
                    <div key={index} className="flex items-start space-x-2">
                      <CheckCircle size={16} className="text-green-400 mt-0.5 flex-shrink-0" />
                      <span className="text-white/80 text-sm">{rec}</span>
                    </div>
                  ))}
                </div>
              </GlassContainer>
            </div>
          </div>
        )}

        {/* About Advanced Forecasting Dashboard */}
        <GlassContainer className="p-6" noFixedHeight={true}>
          <h3 className="text-xl font-bold text-white mb-4 flex items-center">
            <Target className="mr-2" />
            About the Advanced Forecasting Dashboard
          </h3>
          
          <div className="space-y-4">
            <div>
              <h4 className="text-lg font-semibold text-white mb-3">What is it?</h4>
              <p className="text-white/80 leading-relaxed">
                The Advanced Forecasting Dashboard is an AI-powered time series prediction system that combines Prophet and ARIMA models 
                to deliver accurate financial and market forecasting. It features intelligent model selection, real-time performance metrics, 
                and adaptive algorithms that automatically choose the best forecasting approach based on your data characteristics.
              </p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="text-lg font-semibold text-white mb-3">Key Features</h4>
                <div className="space-y-2 text-sm text-white/80">
                  <div className="flex items-center space-x-2">
                    <CheckCircle size={16} className="text-green-400" />
                    <span>Smart Model Selection (Prophet vs ARIMA)</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle size={16} className="text-green-400" />
                    <span>Real-time Accuracy Metrics (MAE, RMSE, MAPE)</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle size={16} className="text-green-400" />
                    <span>Interactive Visualizations & Charts</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle size={16} className="text-green-400" />
                    <span>Confidence Intervals & Trend Analysis</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle size={16} className="text-green-400" />
                    <span>Demo Mode with Offline Capabilities</span>
                  </div>
                </div>
              </div>
              
              <div>
                <h4 className="text-lg font-semibold text-white mb-3">Model Capabilities</h4>
                <div className="space-y-2 text-sm text-white/80">
                  <div className="flex items-start space-x-2">
                    <CheckCircle size={16} className="text-blue-400 mt-0.5" />
                    <div><strong>Prophet:</strong> Handles seasonal patterns, trends, and holidays</div>
                  </div>
                  <div className="flex items-start space-x-2">
                    <CheckCircle size={16} className="text-blue-400 mt-0.5" />
                    <div><strong>ARIMA:</strong> Optimal for stationary data and short-term forecasts</div>
                  </div>
                  <div className="flex items-start space-x-2">
                    <CheckCircle size={16} className="text-blue-400 mt-0.5" />
                    <div><strong>Ensemble:</strong> Combines multiple models for better accuracy</div>
                  </div>
                  <div className="flex items-start space-x-2">
                    <CheckCircle size={16} className="text-blue-400 mt-0.5" />
                    <div><strong>Fallback:</strong> Multiple error handling mechanisms</div>
                  </div>
                </div>
              </div>
            </div>
            
            <div>
              <h4 className="text-lg font-semibold text-white mb-3">Use Cases</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-white/80">
                <div className="space-y-1">
                  <div>• Financial market analysis and stock predictions</div>
                  <div>• Investment strategy optimization</div>
                  <div>• Risk assessment and probability forecasting</div>
                </div>
                <div className="space-y-1">
                  <div>• System performance and load forecasting</div>
                  <div>• Educational analytics and progress tracking</div>
                  <div>• General time series data prediction</div>
                </div>
              </div>
            </div>
          </div>
        </GlassContainer>

      </div>
    </div>
  );
};

export default SimpleForecastingDashboard;
