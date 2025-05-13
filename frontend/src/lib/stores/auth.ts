// frontend/src/lib/stores/auth.ts
import { writable } from 'svelte/store';
import type { User } from '$lib/api/schema';
import { browser } from '$app/environment';
import { authApi } from '$lib/api';
import { goto } from '$app/navigation';
import { getFirebaseAuth } from '$lib/firebase/firebase';

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

  async function loginWithFirebase(email: string, password: string) {
    if (!browser) return;
    
    update(state => ({ ...state, loading: true, error: null }));
    
    try {
      // Get Firebase auth
      const auth = await getFirebaseAuth();
      if (!auth) {
        throw new Error('Firebase auth not initialized');
      }
      
      // Import Firebase auth functions
      const { signInWithEmailAndPassword } = await import('firebase/auth');
      
      // Sign in with Firebase
      const userCredential = await signInWithEmailAndPassword(auth, email, password);
      
      // Get Firebase token
      const token = await userCredential.user.getIdToken();
      
      // Authenticate with backend using Firebase token
      const user = await authApi.loginWithFirebase(token);
      
      // Save token and update state
      localStorage.setItem('token', token);
      set({ 
        user, 
        authenticated: true, 
        loading: false,
        error: null 
      });
      
      return user;
    } catch (error) {
      console.error('Firebase login error:', error);
      const errorMessage = error instanceof Error ? error.message : 'Login failed';
      set({ 
        user: null, 
        authenticated: false, 
        loading: false,
        error: errorMessage 
      });
      throw error;
    }
  }

  async function loginWithGoogle() {
    if (!browser) return;
    
    update(state => ({ ...state, loading: true, error: null }));
    
    try {
      // Get Firebase auth
      const auth = await getFirebaseAuth();
      if (!auth) {
        throw new Error('Firebase auth not initialized');
      }
      
      // Import Firebase auth functions
      const { GoogleAuthProvider, signInWithPopup } = await import('firebase/auth');
      
      // Create Google provider
      const provider = new GoogleAuthProvider();
      
      // Sign in with Google popup
      const userCredential = await signInWithPopup(auth, provider);
      
      // Get Firebase token
      const token = await userCredential.user.getIdToken();
      
      // Authenticate with backend using Firebase token
      const user = await authApi.loginWithFirebase(token);
      
      // Save token and update state
      localStorage.setItem('token', token);
      set({ 
        user, 
        authenticated: true, 
        loading: false,
        error: null 
      });
      
      return user;
    } catch (error) {
      console.error('Google login error:', error);
      const errorMessage = error instanceof Error ? error.message : 'Google login failed';
      set({ 
        user: null, 
        authenticated: false, 
        loading: false,
        error: errorMessage 
      });
      throw error;
    }
  }
  
  return {
    subscribe,
    
    // Login with email and password
    login: async (email: string, password: string) => {
      // In development mode, use development login
      if (import.meta.env.DEV && import.meta.env.VITE_USE_DEV_AUTH === 'true') {
        return loginDevelopment();
      }
      
      // In production, use Firebase login
      return loginWithFirebase(email, password);
    },
    
    // Login with Google
    loginWithGoogle,
    
    // Login with Firebase token directly
    loginWithToken: async (token: string) => {
      update(state => ({ ...state, loading: true, error: null }));
      try {
        const user = await authApi.loginWithFirebase(token);
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
        const user = await authApi.loginForDevelopment();
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
        
        // Also sign out from Firebase if available
        try {
          const auth = await getFirebaseAuth();
          if (auth) {
            await auth.signOut();
          }
        } catch (error) {
          console.error('Firebase sign out error:', error);
        }
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
    
  // Excerpt from frontend/src/lib/stores/auth.ts - initialize method
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