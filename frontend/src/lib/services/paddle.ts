// frontend/src/lib/services/paddle.ts
import { browser } from '$app/environment';

// Interface for Paddle Checkout options
interface CheckoutOptions {
  successCallback?: (data: any) => void;
  closeCallback?: () => void;
  errorCallback?: (error: any) => void;
}

// Paddle service functions
export const paddleService = {
  // Initialize Paddle on page load
  async initialize(): Promise<boolean> {
    if (!browser) return false;
    
    // Check if Paddle is already loaded
    if (window.Paddle) {
      return true;
    }
    
    // Load Paddle.js dynamically
    return new Promise((resolve) => {
      // Listen for paddle-initialized event
      window.addEventListener('paddle-initialized', () => {
        resolve(true);
      }, { once: true });
      
      // Check if Paddle is already loaded every 100ms
      const checkInterval = setInterval(() => {
        if (window.Paddle) {
          clearInterval(checkInterval);
          resolve(true);
        }
      }, 100);
      
      // Set a timeout to resolve false if Paddle doesn't load
      setTimeout(() => {
        clearInterval(checkInterval);
        if (!window.Paddle) {
          console.error('Paddle failed to load within timeout');
          resolve(false);
        }
      }, 5000);
    });
  },
  
  // Open Paddle checkout with provided URL
  async openCheckout(checkoutUrl: string, options?: CheckoutOptions): Promise<boolean> {
    if (!browser) return false;
    
    // Make sure Paddle is initialized
    const initialized = await this.initialize();
    if (!initialized || !window.Paddle) {
      console.error('Paddle not initialized');
      return false;
    }
    
    try {
      // Extract transaction ID from checkout URL
      const url = new URL(checkoutUrl);
      const txnParam = url.searchParams.get('txn');
      
      if (!txnParam) {
        console.error('Missing transaction ID in checkout URL');
        window.location.href = checkoutUrl; // Fallback to redirect
        return false;
      }
      
      // Open Paddle checkout
      window.Paddle.Checkout.open({
        override: checkoutUrl,
        successCallback: options?.successCallback,
        closeCallback: options?.closeCallback,
        errorCallback: options?.errorCallback
      });
      
      return true;
    } catch (error) {
      console.error('Error opening Paddle checkout:', error);
      
      // Fallback to redirect
      window.location.href = checkoutUrl;
      return false;
    }
  },
  
  // Helper to check if Paddle is available
  isPaddleAvailable(): boolean {
    return browser && !!window.Paddle;
  }
};

// Type definitions for window.Paddle
declare global {
  interface Window {
    Paddle?: {
      Setup: (options: { vendor: string }) => void;
      Environment: {
        set: (env: 'sandbox' | 'production') => void;
      };
      Checkout: {
        open: (options: any) => void;
      };
    };
  }
}