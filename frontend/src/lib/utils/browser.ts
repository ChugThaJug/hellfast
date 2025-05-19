/**
 * Utility functions for safely handling browser-specific code
 */

import { browser } from '$app/environment';

/**
 * Safely get window location or fallback to default value during SSR
 */
export function getWindowLocation() {
  if (browser) {
    return window.location;
  }
  return {
    hostname: 'localhost',
    pathname: '/',
    href: 'http://localhost',
    origin: 'http://localhost'
  };
}

/**
 * Safely handle localStorage operations with SSR support
 */
export const safeLocalStorage = {
  getItem: (key: string): string | null => {
    if (browser) {
      return localStorage.getItem(key);
    }
    return null;
  },
  
  setItem: (key: string, value: string): void => {
    if (browser) {
      localStorage.setItem(key, value);
    }
  },
  
  removeItem: (key: string): void => {
    if (browser) {
      localStorage.removeItem(key);
    }
  }
};

/**
 * Safe environment variable access
 */
export function getEnvVar(key: string, fallback: string = ''): string {
  if (import.meta.env && import.meta.env[key]) {
    return import.meta.env[key] as string;
  }
  return fallback;
}

/**
 * Safely determine API URL based on environment
 */
export function getApiUrl(): string {
  console.log('GetApiUrl called, browser env:', browser);
  
  // Server-side case
  if (!browser) {
    const apiUrl = getEnvVar('VITE_API_URL', 'http://localhost:8000');
    console.log('Server-side rendering, using API URL:', apiUrl);
    return apiUrl;
  }
  
  // Client-side case
  const location = getWindowLocation();
  const isCloudflareOrProduction = location.hostname.includes('pages.dev') || 
    location.hostname !== 'localhost';
  
  if (isCloudflareOrProduction) {
    const apiUrl = getEnvVar('VITE_API_URL', 'http://localhost:8000');
    console.log('Production environment, using API URL:', apiUrl);
    return apiUrl;
  }
  
  // Local development - use relative path which gets proxied
  console.log('Local development, using relative API URL');
  return '';
}
