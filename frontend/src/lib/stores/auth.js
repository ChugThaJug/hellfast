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
    
    // Login with token directly (for OAuth callback)
    loginWithToken: async (token) => {
      update(state => ({ ...state, loading: true, error: null }));
      try {
        console.log("Logging in with token...");
        
        // Verify token with backend
        const user = await authApi.verifyToken(token);
        
        if (browser) {
          // Store token in localStorage
          localStorage.setItem('token', token);
          console.log("Token stored successfully");
        }
        
        set({ 
          user, 
          authenticated: true, 
          loading: false,
          error: null 
        });
        return user;
      } catch (error) {
        console.error("Token login error:", error);
        const errorMessage = error instanceof Error ? error.message : 'Login failed';
        set({ 
          user: null, 
          authenticated: false, 
          loading: false,
          error: errorMessage 
        });
        throw error;
      }
    },
    
    // Logout
    logout: async () => {
      if (browser) {
        localStorage.removeItem('token');
      }
      
      set({ 
        user: null, 
        authenticated: false, 
        loading: false,
        error: null 
      });
      
      // Redirect to home
      goto('/');
    },
    
    // Set error
    setError: (error) => {
      update(state => ({ ...state, error }));
    },
    
    // Clear error
    clearError: () => {
      update(state => ({ ...state, error: null }));
    },
    
    // Initialize auth from localStorage token
    initialize: async () => {
      if (!browser) return;
      
      update(state => ({ ...state, loading: true }));
      
      const token = localStorage.getItem('token');
      console.log("Auth initialization - Token exists:", !!token);
      
      if (!token) {
        set({ 
          user: null, 
          authenticated: false, 
          loading: false,
          error: null 
        });
        return;
      }
      
      try {
        // Try to get user profile from backend
        console.log("Fetching user profile...");
        const user = await authApi.getProfile();
        console.log("User profile fetched:", user);
        
        set({ 
          user, 
          authenticated: true, 
          loading: false,
          error: null 
        });
      } catch (error) {
        console.error('Auth initialization error:', error);
        localStorage.removeItem('token');
        set({ 
          user: null, 
          authenticated: false, 
          loading: false,
          error: null 
        });
      }
    }
  };
}

export const auth = createAuthStore();

// Initialize auth on import (for browser environments)
if (browser) {
  console.log("Initializing auth store on import");
  auth.initialize();
}