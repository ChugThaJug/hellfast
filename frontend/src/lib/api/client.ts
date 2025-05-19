// frontend/src/lib/api/client.ts
import { browser } from '$app/environment';
import { goto } from '$app/navigation';

// Simple API URL without any window references
export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

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
    // Only run in browser
    if (!browser) {
      console.log('API request skipped in SSR mode');
      return { success: false, message: 'API request skipped in SSR mode' };
    }
    
    // Get token from local storage
    let token = null;
    if (!options.skipAuth) {
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
    const timeout = options.timeout || 30000; // 30 seconds default timeout
    
    // Create abort controller for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    
    // Execute request
    console.log(`API Request: ${API_URL}${normalizedEndpoint}`);
    const response = await fetch(`${API_URL}${normalizedEndpoint}`, {
      ...options,
      headers,
      signal: controller.signal
    });
    
    // Clear timeout
    clearTimeout(timeoutId);
    
    // Handle unauthorized
    if (response.status === 401) {
      console.error('Authentication error: Token invalid or expired');
      localStorage.removeItem('token');
      goto('/auth/login');
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
  } catch (error: unknown) {
    // Handle timeout errors
    if (error instanceof Error && error.name === 'AbortError') {
      console.error('API request timeout');
      throw new Error('Request timed out. Please try again later.');
    }
    
    console.error('API request failed:', error);
    throw error;
  }
}