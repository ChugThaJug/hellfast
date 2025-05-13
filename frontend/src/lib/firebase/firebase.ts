// frontend/src/lib/firebase/firebase.ts
import { browser } from '$app/environment';

// Firebase configuration (replace with your real Firebase config)
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || "demo-api-key",
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || "demo-project.firebaseapp.com",
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || "demo-project",
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || "demo-project.appspot.com",
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || "123456789",
  appId: import.meta.env.VITE_FIREBASE_APP_ID || "1:123456789:web:abcdef"
};

// Firebase initialization
let auth = null;
let app = null;

// Initialize Firebase only in the browser
if (browser) {
  const initializeFirebase = async () => {
    try {
      // Dynamically import Firebase modules (only in browser)
      const { initializeApp } = await import('firebase/app');
      const { getAuth, connectAuthEmulator } = await import('firebase/auth');
      
      // Initialize Firebase
      app = initializeApp(firebaseConfig);
      auth = getAuth(app);
      
      // If in development mode, connect to auth emulator if available
      if (import.meta.env.DEV && import.meta.env.VITE_USE_FIREBASE_EMULATOR === 'true') {
        connectAuthEmulator(auth, 'http://localhost:9099');
        console.log('Connected to Firebase Auth Emulator');
      }
      
      console.log('Firebase initialized successfully');
      return { app, auth };
    } catch (error) {
      console.error('Firebase initialization error:', error);
      return { app: null, auth: null };
    }
  };
  
  // Initialize Firebase immediately
  initializeFirebase();
}

// Export Firebase auth for use in other files
export { auth, app };

// Helper function to get Firebase auth (ensuring it's initialized)
export async function getFirebaseAuth() {
  if (!browser) return null;
  
  if (!auth) {
    // If auth isn't initialized yet, try to initialize it
    const { getAuth } = await import('firebase/auth');
    if (app) {
      auth = getAuth(app);
    } else {
      const { initializeApp } = await import('firebase/app');
      app = initializeApp(firebaseConfig);
      auth = getAuth(app);
    }
  }
  
  return auth;
}