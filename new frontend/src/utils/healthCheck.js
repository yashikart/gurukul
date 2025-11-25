/**
 * Health Check Utility
 * 
 * This module provides functions to check the health of backend services
 * and ensure the frontend is properly connected to all required APIs.
 */

import { API_BASE_URL, CHAT_API_BASE_URL, FINANCIAL_API_BASE_URL, AGENT_API_BASE_URL } from '../config';

/**
 * Check the health of a specific backend service
 * @param {string} url - The URL to check
 * @returns {Promise<{status: boolean, message: string}>} - Health check result
 */
export const checkServiceHealth = async (url) => {
  try {
    const response = await fetch(`${url}/health`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
      timeout: 5000, // 5 second timeout
    });
    
    if (response.ok) {
      return { status: true, message: 'Service is healthy' };
    } else {
      return { status: false, message: `Service returned status: ${response.status}` };
    }
  } catch (error) {
    return { status: false, message: `Connection error: ${error.message}` };
  }
};

/**
 * Check the health of all backend services
 * @returns {Promise<{allHealthy: boolean, services: Object}>} - Health check results
 */
export const checkAllServices = async () => {
  const services = {
    base: { url: API_BASE_URL, name: 'Base Backend' },
    chat: { url: CHAT_API_BASE_URL, name: 'Chat API' },
    financial: { url: FINANCIAL_API_BASE_URL, name: 'Financial Simulator' },
    agent: { url: AGENT_API_BASE_URL, name: 'Agent API' },
  };
  
  const results = {};
  let allHealthy = true;
  
  for (const [key, service] of Object.entries(services)) {
    const health = await checkServiceHealth(service.url);
    results[key] = {
      name: service.name,
      healthy: health.status,
      message: health.message,
    };
    
    if (!health.status) {
      allHealthy = false;
    }
  }
  
  return {
    allHealthy,
    services: results,
  };
};

/**
 * Log health check results to console
 * @param {Object} healthResults - Results from checkAllServices
 */
export const logHealthResults = (healthResults) => {
  console.group('Backend Services Health Check');
  console.log(`Overall Status: ${healthResults.allHealthy ? '✅ Healthy' : '❌ Issues Detected'}`);
  
  for (const [key, service] of Object.entries(healthResults.services)) {
    console.log(
      `${service.name}: ${service.healthy ? '✅ Healthy' : '❌ Unhealthy'} - ${service.message}`
    );
  }
  
  console.groupEnd();
};

/**
 * Perform a health check and return a user-friendly message
 * @returns {Promise<{healthy: boolean, message: string}>} - User-friendly health status
 */
export const getUserFriendlyHealthStatus = async () => {
  const health = await checkAllServices();
  
  if (health.allHealthy) {
    return {
      healthy: true,
      message: 'All systems operational',
    };
  }
  
  // Count unhealthy services
  const unhealthyCount = Object.values(health.services).filter(s => !s.healthy).length;
  const totalCount = Object.values(health.services).length;
  
  return {
    healthy: false,
    message: `${unhealthyCount} of ${totalCount} services are experiencing issues`,
  };
};