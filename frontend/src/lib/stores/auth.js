// frontend/src/lib/stores/auth.js
import { writable } from 'svelte/store';
import { browser } from '$app/environment';
import { authApi } from '$lib/api';
import { goto } from '$app/navigation';

function createAuthStore() {
  const { subscribe, set, update } = writable({
    user: null,
    authenticated: false,
    loading: true,
    error: null
  });

  return {
    subscribe,
    
    // Login with OAuth flow
    login: async () => {
      update(state => ({ ...state, loading: true, error: null }));
      try {
        // Store current path for redirection after login
        if (browser) {
          localStorage.setItem('auth_redirect', window.location.pathname);
        }
        
        // Redirect to Google OAuth
        if (browser) {
          const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
          console.log("Redirecting to OAuth:", `${apiBaseUrl}/oauth/google/login`);
          window.location.href = `${apiBaseUrl}/oauth/google/login`;
        }
      } catch (error) {
        console.error("OAuth redirect error:", error);
        update(state => ({ 
          ...state, 
          loading: false, 
          error: error instanceof Error ? error.message : "Login failed" 
        }));
      }
    },
    
    // Other methods remain the same...
  };
}

export const auth = createAuthStore();

// Initialize auth on import (for browser environments)
if (browser) {
  console.log("Initializing auth store on import");
  auth.initialize();
}