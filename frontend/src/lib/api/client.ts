// frontend/src/lib/api/client.ts
import { browser } from '$app/environment';

// API Base URL from environment or default
const API_BASE_URL = browser 
  ? import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
  : 'http://localhost:8000';

// Options type for fetchWithAuth
interface FetchOptions extends RequestInit {
  skipAuth?: boolean;
}

/**
 * Fetch with authentication and error handling
 */
export async function fetchWithAuth(endpoint: string, options: FetchOptions = {}) {
  try {
    // Only get token in browser context
    let token = null;
    if (browser && !options.skipAuth) {
      token = localStorage.getItem('token');
    }
    
    // Ensure endpoint starts with '/'
    const normalizedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    
    // Prepare headers
    const headers = {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
      ...options.headers
    };
    
    // Execute request
    console.log(`API Request: ${API_BASE_URL}${normalizedEndpoint}`);
    const response = await fetch(`${API_BASE_URL}${normalizedEndpoint}`, {
      ...options,
      headers
    });
    
    // Handle common response scenarios
    if (response.status === 401 && browser) {
      // Unauthorized - clear token and redirect to login
      localStorage.removeItem('token');
      window.location.href = '/auth/login?session=expired';
      throw new Error('Session expired. Please log in again.');
    }
    
    // Handle error responses
    if (!response.ok) {
      let errorMessage = `HTTP error ${response.status}`;
      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorMessage;
      } catch (e) {
        // JSON parsing failed, use default error message
      }
      throw new Error(errorMessage);
    }
    
    // Return response data
    return await response.json();
  } catch (error) {
    console.error('API request failed:', error);
    throw error;
  }
}