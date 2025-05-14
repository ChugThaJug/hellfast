// frontend/src/lib/stores/auth.ts
import { writable } from 'svelte/store';
import type { User } from '$lib/api/schema';
import { browser } from '$app/environment';
import { authApi } from '$lib/api';
import { goto } from '$app/navigation';

interface AuthState {
  user: User | null;
  authenticated: boolean;
  loading: boolean;
  error: string | null;
}

function createAuthStore() {
  const { subscribe, set, update } = writable<AuthState>({
    user: null,
    authenticated: false,
    loading: true,
    error: null
  });

  return {
    subscribe,
    
    // Login with email/password not supported anymore - redirects to OAuth
    login: async () => {
      // Redirect to OAuth page
      if (browser) {
        const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
        window.location.href = `${apiBaseUrl}/oauth/google/login`;
      }
    },
    
    // Login with token directly (for OAuth callback)
    loginWithToken: async (token: string) => {
      update(state => ({ ...state, loading: true, error: null }));
      try {
        const user = await authApi.verifyToken(token);
        if (browser) {
          localStorage.setItem('token', token);
        }
        set({ 
          user, 
          authenticated: true, 
          loading: false,
          error: null 
        });
        return user;
      } catch (error) {
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
    
    // Development login - always succeeds
    loginDevelopment: async () => {
      update(state => ({ ...state, loading: true, error: null }));
      try {
        const user = await authApi.devLogin();
        if (browser) {
          localStorage.setItem('token', 'dev-token'); // Dev token
        }
        set({ 
          user, 
          authenticated: true, 
          loading: false,
          error: null 
        });
        return user;
      } catch (error) {
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
    setError: (error: string) => {
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
        const user = await authApi.getProfile();
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
  auth.initialize();
}