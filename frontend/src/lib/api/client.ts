// frontend/src/lib/api/client.ts
import { browser } from '$app/environment';

// API Base URL from environment or default
const API_BASE_URL = browser 
  ? import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
  : 'http://localhost:8000';

// Options type for fetchWithAuth
interface FetchOptions extends RequestInit {
  skipAuth?: boolean;
  timeout?: number;
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
      console.log(`API Request to ${endpoint} - Auth token present: ${!!token}`);
    }
    
    // Ensure endpoint starts with '/'
    const normalizedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    
    // Prepare headers
    const headers = {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
      ...options.headers
    };
    
    // Set up a timeout if specified
    const timeout = options.timeout || 20000; // 20 seconds default timeout
    
    // Create abort controller for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    
    // Execute request
    console.log(`API Request: ${API_BASE_URL}${normalizedEndpoint}`);
    const response = await fetch(`${API_BASE_URL}${normalizedEndpoint}`, {
      ...options,
      headers,
      signal: controller.signal
    });
    
    // Clear timeout
    clearTimeout(timeoutId);
    
    // Handle common response scenarios
    if (response.status === 401 && browser) {
      console.error('Authentication error: Token invalid or expired');
      // Unauthorized - clear token and redirect to login
      localStorage.removeItem('token');
      
      // Throw specific error for 401
      throw new Error('Authentication required. Please log in.');
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
    // Handle timeout errors
    if (error.name === 'AbortError') {
      console.error('API request timeout');
      throw new Error('Request timed out. Please try again later.');
    }
    
    console.error('API request failed:', error);
    throw error;
  }
}