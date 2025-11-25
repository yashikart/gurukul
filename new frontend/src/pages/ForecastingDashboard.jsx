import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { TrendingUp, Activity, Brain, AlertTriangle, CheckCircle, Clock, Target } from 'lucide-react';
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
      date = new Date(dateString + 'T00:00:00');
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

const ForecastingDashboard = () => {
  const [forecastData, setForecastData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [modelComparison, setModelComparison] = useState(null);
  const [systemStatus, setSystemStatus] = useState(null);
  const [selectedMetricType, setSelectedMetricType] = useState('general');
  const [forecastPeriods, setForecastPeriods] = useState(30);

  // Sample data for demonstration with current dates
  const generateSampleData = (type) => {
    const data = [];
    const today = new Date();

    // Generate 30 days of historical data (past dates)
    for (let i = -30; i < 0; i++) {
      const date = new Date(today.getTime() + (i * 24 * 60 * 60 * 1000));

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

  const generateForecast = async () => {
    setLoading(true);
    setForecastData(null); // Clear previous data
    console.log('🔄 Generating fresh forecast data...');

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
          user_id: 'demo_user',
          timestamp: Date.now() // Force fresh data
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

      // Debug: log first few dates
      if (i < 3) {
        console.log(`Generated forecast date ${i + 1}:`, dateString, 'formatted:', formatDateSafely(dateString));
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

  const compareModels = async () => {
    setLoading(true);
    try {
      const sampleData = generateSampleData(selectedMetricType);
      
      const response = await fetch('http://localhost:8006/compare-models', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          data: sampleData,
          metric_type: selectedMetricType,
          language: 'en'
        })
      });

      if (response.ok) {
        const result = await response.json();
        setModelComparison(result);
        toast.success('Model comparison completed!');
      } else {
        throw new Error(`HTTP ${response.status}`);
      }
    } catch (error) {
      console.error('Model comparison failed:', error);
      toast.error('Model comparison failed - using demo data');
      
      // Demo comparison data
      setModelComparison({
        status: 'success',
        best_model: 'prophet',
        performance_summary: {
          prophet: { mae: 2.45, rmse: 3.12, mape: 1.95, r2: 0.85 },
          arima: { mae: 3.21, rmse: 4.05, mape: 2.87, r2: 0.78 }
        }
      });
    }
    setLoading(false);
  };

  useEffect(() => {
    checkSystemStatus();
  }, []);

  const formatChartData = () => {
    if (!forecastData?.content?.forecast_data) return [];

    return forecastData.content.forecast_data.map((item, index) => {
      // Force fresh date calculation for display
      const today = new Date();
      const displayDate = new Date(today.getTime() + ((index + 1) * 24 * 60 * 60 * 1000));
      const formattedDate = `${(displayDate.getMonth() + 1).toString().padStart(2, '0')}/${displayDate.getDate().toString().padStart(2, '0')}/${displayDate.getFullYear()}`;

      return {
        date: formattedDate,
        predicted: item.predicted_value,
        lower: item.lower_bound,
        upper: item.upper_bound
      };
    });
  };

  const getMetricTypeColor = () => {
    switch (selectedMetricType) {
      case 'probability': return '#FF9933'; // Saffron
      case 'load': return '#2E4A3F'; // Forest Green
      default: return '#FFFFFF'; // White
    }
  };

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
                Advanced Forecasting Dashboard
              </h1>
              <p className="text-lg" style={{ color: '#FFFFFF' }}>
                Prophet & ARIMA Time Series Forecasting with Smart Model Selection
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
                onFocus={(e) => {
                  e.target.style.borderColor = '#FF9933';
                  e.target.style.boxShadow = '0 0 0 2px rgba(255, 153, 51, 0.2)';
                }}
                onBlur={(e) => {
                  e.target.style.borderColor = 'rgba(255, 215, 0, 0.3)';
                  e.target.style.boxShadow = 'none';
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
                placeholder="Enter days to forecast"
                onFocus={(e) => {
                  e.target.style.borderColor = '#FF9933';
                  e.target.style.boxShadow = '0 0 0 2px rgba(255, 153, 51, 0.2)';
                }}
                onBlur={(e) => {
                  e.target.style.borderColor = 'rgba(255, 215, 0, 0.3)';
                  e.target.style.boxShadow = 'none';
                }}
              />
            </div>

            <button
              onClick={generateForecast}
              disabled={loading}
              className="flex items-center justify-center space-x-3 py-3 px-6 text-base font-bold rounded-lg transition-all duration-300 border-2 disabled:opacity-50"
              style={{
                background: 'linear-gradient(135deg, rgba(255, 153, 51, 0.4) 0%, rgba(255, 165, 0, 0.3) 50%, rgba(255, 69, 0, 0.2) 100%)',
                backdropFilter: 'blur(16px)',
                border: '2px solid rgba(255, 153, 51, 0.6)',
                boxShadow: '0 8px 32px rgba(255, 153, 51, 0.25), 0 0 0 1px rgba(255, 165, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.4)',
                color: '#FFFFFF',
                textShadow: '0 2px 4px rgba(0, 0, 0, 0.3)'
              }}
              onMouseEnter={(e) => {
                if (!loading) {
                  e.target.style.transform = 'translateY(-2px)';
                  e.target.style.boxShadow = '0 12px 40px rgba(255, 153, 51, 0.35), 0 0 0 1px rgba(255, 165, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.5)';
                }
              }}
              onMouseLeave={(e) => {
                if (!loading) {
                  e.target.style.transform = 'translateY(0)';
                  e.target.style.boxShadow = '0 8px 32px rgba(255, 153, 51, 0.25), 0 0 0 1px rgba(255, 165, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.4)';
                }
              }}
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  <span>Generating...</span>
                </>
              ) : (
                <>
                  <TrendingUp size={20} />
                  <span>Generate Forecast</span>
                </>
              )}
            </button>

            <button
              onClick={compareModels}
              disabled={loading}
              className="flex items-center justify-center space-x-3 py-3 px-6 text-base font-bold rounded-lg transition-all duration-300 border-2 disabled:opacity-50"
              style={{
                background: 'linear-gradient(135deg, rgba(93, 0, 30, 0.4) 0%, rgba(139, 69, 19, 0.3) 50%, rgba(160, 82, 45, 0.2) 100%)',
                backdropFilter: 'blur(16px)',
                border: '2px solid rgba(160, 82, 45, 0.6)',
                boxShadow: '0 8px 32px rgba(93, 0, 30, 0.25), 0 0 0 1px rgba(160, 82, 45, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.4)',
                color: '#FFFFFF',
                textShadow: '0 2px 4px rgba(0, 0, 0, 0.3)'
              }}
              onMouseEnter={(e) => {
                if (!loading) {
                  e.target.style.transform = 'translateY(-2px)';
                  e.target.style.boxShadow = '0 12px 40px rgba(93, 0, 30, 0.35), 0 0 0 1px rgba(160, 82, 45, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.5)';
                }
              }}
              onMouseLeave={(e) => {
                if (!loading) {
                  e.target.style.transform = 'translateY(0)';
                  e.target.style.boxShadow = '0 8px 32px rgba(93, 0, 30, 0.25), 0 0 0 1px rgba(160, 82, 45, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.4)';
                }
              }}
            >
              <Brain size={20} />
              <span>Compare Models</span>
            </button>
          </div>
        </GlassContainer>

        {/* Forecast Results */}
        {forecastData && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

            {/* Main Chart */}
            <div className="lg:col-span-2">
              <GlassContainer className="p-8" noFixedHeight={true}>
                <h3 className="text-2xl font-bold mb-6 flex items-center" style={{ color: '#FFFFFF' }}>
                  <Activity className="mr-3 h-6 w-6" style={{ color: '#FF9933' }} />
                  Forecast Visualization
                </h3>

                <div className="h-96 mb-4">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={formatChartData()}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.2)" />
                      <XAxis
                        dataKey="date"
                        stroke="#FFFFFF"
                        fontSize={12}
                        fontWeight="500"
                      />
                      <YAxis stroke="#FFFFFF" fontSize={12} fontWeight="500" />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: 'rgba(0, 0, 0, 0.85)',
                          border: '2px solid #FFD700',
                          borderRadius: '12px',
                          color: '#FFFFFF',
                          backdropFilter: 'blur(12px)',
                          fontWeight: '500'
                        }}
                      />
                      <Legend />
                      <Line
                        type="monotone"
                        dataKey="predicted"
                        stroke={getMetricTypeColor()}
                        strokeWidth={3}
                        name="Predicted Value"
                        dot={{ fill: getMetricTypeColor(), strokeWidth: 2, r: 4 }}
                      />
                      <Line
                        type="monotone"
                        dataKey="lower"
                        stroke="#D6A76C"
                        strokeWidth={2}
                        strokeDasharray="5 5"
                        name="Lower Bound"
                        dot={false}
                      />
                      <Line
                        type="monotone"
                        dataKey="upper"
                        stroke="#D6A76C"
                        strokeWidth={2}
                        strokeDasharray="5 5"
                        name="Upper Bound"
                        dot={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </GlassContainer>
            </div>

            {/* Summary Stats */}
            <div className="space-y-4">
              <GlassContainer className="p-4" noFixedHeight={true}>
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

              <GlassContainer className="p-4" noFixedHeight={true}>
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

              <GlassContainer className="p-4" noFixedHeight={true}>
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

        {/* Model Comparison */}
        {modelComparison && (
          <GlassContainer className="p-6" noFixedHeight={true}>
            <h3 className="text-xl font-bold text-white mb-4 flex items-center">
              <Brain className="mr-2" />
              Model Performance Comparison
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="text-lg font-semibold text-white mb-3">Performance Metrics</h4>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={[
                      {
                        metric: 'MAE',
                        Prophet: modelComparison.performance_summary?.prophet?.mae || 0,
                        ARIMA: modelComparison.performance_summary?.arima?.mae || 0
                      },
                      {
                        metric: 'RMSE',
                        Prophet: modelComparison.performance_summary?.prophet?.rmse || 0,
                        ARIMA: modelComparison.performance_summary?.arima?.rmse || 0
                      },
                      {
                        metric: 'MAPE',
                        Prophet: modelComparison.performance_summary?.prophet?.mape || 0,
                        ARIMA: modelComparison.performance_summary?.arima?.mape || 0
                      }
                    ]}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                      <XAxis dataKey="metric" stroke="rgba(255,255,255,0.7)" />
                      <YAxis stroke="rgba(255,255,255,0.7)" />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: 'rgba(0,0,0,0.8)',
                          border: '1px solid rgba(255,255,255,0.2)',
                          borderRadius: '8px',
                          color: 'white'
                        }}
                      />
                      <Legend />
                      <Bar dataKey="Prophet" fill="#8884d8" />
                      <Bar dataKey="ARIMA" fill="#82ca9d" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div>
                <h4 className="text-lg font-semibold text-white mb-3">Best Model</h4>
                <div className="bg-gradient-to-r from-green-500/20 to-blue-500/20 rounded-lg p-4 border border-white/20">
                  <div className="text-center">
                    <div className="text-3xl font-bold text-white mb-2">
                      {modelComparison.best_model?.toUpperCase() || 'N/A'}
                    </div>
                    <div className="text-white/70">
                      Recommended Model
                    </div>
                  </div>
                </div>

                <div className="mt-4 space-y-2">
                  <div className="text-sm text-white/70">
                    <strong>Prophet:</strong> Best for seasonal data and trend analysis
                  </div>
                  <div className="text-sm text-white/70">
                    <strong>ARIMA:</strong> Optimal for stationary data and short-term forecasts
                  </div>
                </div>
              </div>
            </div>
          </GlassContainer>
        )}

        {/* About Advanced Forecasting Dashboard */}
        <GlassContainer className="p-6" noFixedHeight={true}>
          <h3 className="text-xl font-bold text-white mb-4 flex items-center">
            <Target className="mr-2" />
            About the Advanced Forecasting Dashboard
          </h3>

          <div className="space-y-6">
            {/* Overview */}
            <div>
              <h4 className="text-lg font-semibold text-white mb-3">What is the Advanced Forecasting Dashboard?</h4>
              <div className="text-white/80 leading-relaxed">
                The Advanced Forecasting Dashboard is a sophisticated time series prediction system that leverages both Prophet and ARIMA models 
                to provide accurate financial and market forecasting. Built on Facebook's Prophet library and statsmodels' ARIMA implementation, 
                it features intelligent model selection, ensemble modeling, and comprehensive performance evaluation to deliver reliable predictions 
                for various financial instruments and market data.
              </div>
            </div>

            {/* Key Features Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="text-lg font-semibold text-white mb-3">Core Features</h4>
                <div className="space-y-2 text-sm text-white/80">
                  <div className="flex items-center space-x-2">
                    <CheckCircle size={16} className="text-green-400" />
                    <span>Smart Model Selection - Automatically chooses between Prophet and ARIMA</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle size={16} className="text-green-400" />
                    <span>Ensemble Modeling - Combines multiple forecasting approaches</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle size={16} className="text-green-400" />
                    <span>Real-time Performance Metrics - MAE, RMSE, MAPE evaluation</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle size={16} className="text-green-400" />
                    <span>Interactive Visualizations - Advanced charts and trend analysis</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle size={16} className="text-green-400" />
                    <span>Confidence Intervals - Uncertainty quantification for predictions</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle size={16} className="text-green-400" />
                    <span>Multilingual Support - Forecasts with localized explanations</span>
                  </div>
                </div>
              </div>

              <div>
                <h4 className="text-lg font-semibold text-white mb-3">Model Capabilities</h4>
                <div className="space-y-2 text-sm text-white/80">
                  <div className="flex items-center space-x-2">
                    <CheckCircle size={16} className="text-blue-400" />
                    <span><strong>Prophet Model:</strong> Handles seasonal patterns and trend analysis</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle size={16} className="text-blue-400" />
                    <span><strong>ARIMA Model:</strong> Optimal for stationary data and short-term forecasts</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle size={16} className="text-blue-400" />
                    <span><strong>Adaptive Selection:</strong> Chooses best model based on data characteristics</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle size={16} className="text-blue-400" />
                    <span><strong>Fallback Mechanisms:</strong> Multiple layers of error handling</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle size={16} className="text-blue-400" />
                    <span><strong>Cross-validation:</strong> Rigorous model performance testing</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Technical Specifications */}
            <div>
              <h4 className="text-lg font-semibold text-white mb-3">Technical Architecture</h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                <div className="bg-gradient-to-r from-blue-500/20 to-purple-500/20 rounded-lg p-4 border border-white/20">
                  <h5 className="font-semibold text-white mb-2">Data Processing</h5>
                  <ul className="text-white/70 space-y-1">
                    <li>• Automatic data quality assessment</li>
                    <li>• Missing value handling</li>
                    <li>• Outlier detection and treatment</li>
                    <li>• Seasonality pattern recognition</li>
                  </ul>
                </div>
                <div className="bg-gradient-to-r from-green-500/20 to-blue-500/20 rounded-lg p-4 border border-white/20">
                  <h5 className="font-semibold text-white mb-2">Model Performance</h5>
                  <ul className="text-white/70 space-y-1">
                    <li>• Prophet: 2-5 seconds typical response</li>
                    <li>• ARIMA: 1-3 seconds parameter optimization</li>
                    <li>• Caching for improved performance</li>
                    <li>• &lt;1 second fallback forecasts</li>
                  </ul>
                </div>
                <div className="bg-gradient-to-r from-orange-500/20 to-red-500/20 rounded-lg p-4 border border-white/20">
                  <h5 className="font-semibold text-white mb-2">Quality Assurance</h5>
                  <ul className="text-white/70 space-y-1">
                    <li>• Continuous accuracy monitoring</li>
                    <li>• Confidence level categorization</li>
                    <li>• Resource usage optimization</li>
                    <li>• Comprehensive test framework</li>
                  </ul>
                </div>
              </div>
            </div>

            {/* Use Cases */}
            <div>
              <h4 className="text-lg font-semibold text-white mb-3">Primary Use Cases</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2 text-sm text-white/80">
                  <div className="flex items-start space-x-2">
                    <DollarSign size={16} className="text-yellow-400 mt-0.5 flex-shrink-0" />
                    <div>
                      <strong>Financial Market Analysis:</strong> Stock price predictions, market trend analysis, and investment strategy optimization
                    </div>
                  </div>
                  <div className="flex items-start space-x-2">
                    <Activity size={16} className="text-green-400 mt-0.5 flex-shrink-0" />
                    <div>
                      <strong>Performance Metrics:</strong> System load forecasting, performance trend analysis, and capacity planning
                    </div>
                  </div>
                </div>
                <div className="space-y-2 text-sm text-white/80">
                  <div className="flex items-start space-x-2">
                    <Target size={16} className="text-blue-400 mt-0.5 flex-shrink-0" />
                    <div>
                      <strong>Risk Assessment:</strong> Probability-based forecasting for risk management and decision support
                    </div>
                  </div>
                  <div className="flex items-start space-x-2">
                    <Brain size={16} className="text-purple-400 mt-0.5 flex-shrink-0" />
                    <div>
                      <strong>Educational Analytics:</strong> Learning progress prediction and personalized content recommendation
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </GlassContainer>

      </div>
    </div>
  );
};

export default ForecastingDashboard;
