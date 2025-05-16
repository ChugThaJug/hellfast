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
    
    try {
      // Check if Paddle is already loaded
      if (window.Paddle) {
        return true;
      }
      
      // Get environment variables
      const sandbox = import.meta.env.VITE_PADDLE_SANDBOX === 'true';
      const vendorId = import.meta.env.VITE_PADDLE_VENDOR_ID;
      
      if (!vendorId) {
        console.warn('Paddle vendor ID not configured');
      }
      
      // Load Paddle.js script
      return new Promise((resolve) => {
        const script = document.createElement('script');
        script.src = 'https://cdn.paddle.com/paddle/paddle.js';
        script.async = true;
        script.onload = () => {
          try {
            if (!window.Paddle) {
              console.error('Paddle failed to initialize');
              resolve(false);
              return;
            }
            
            // Initialize Paddle
            window.Paddle.Setup({ 
              vendor: vendorId,
              environment: sandbox ? 'sandbox' : 'production'
            });
            
            console.log(`Paddle initialized${sandbox ? ' in sandbox mode' : ''}`);
            
            // Dispatch event for other components to know Paddle is loaded
            window.dispatchEvent(new Event('paddle-initialized'));
            
            resolve(true);
          } catch (error) {
            console.error('Error initializing Paddle:', error);
            resolve(false);
          }
        };
        
        script.onerror = () => {
          console.error('Failed to load Paddle.js');
          resolve(false);
        };
        
        document.head.appendChild(script);
        
        // Set a timeout to resolve false if Paddle doesn't load
        setTimeout(() => {
          if (!window.Paddle) {
            console.error('Paddle failed to load within timeout');
            resolve(false);
          }
        }, 5000);
      });
    } catch (error) {
      console.error('Error initializing Paddle:', error);
      return false;
    }
  },
  
  // Open Paddle checkout with provided URL
  async openCheckout(checkoutUrl: string, options?: CheckoutOptions): Promise<boolean> {
    if (!browser) return false;
    
    try {
      // Make sure Paddle is initialized
      const initialized = await this.initialize();
      if (!initialized || !window.Paddle) {
        console.error('Paddle not initialized, falling back to redirect');
        window.location.href = checkoutUrl; // Fallback to redirect
        return false;
      }
      
      // Parse the URL to extract parameters
      const url = new URL(checkoutUrl);
      
      // Extract price ID from the items parameter
      let priceId = '';
      try {
        const path = url.pathname;
        const parts = path.split('/');
        if (parts.length >= 3) {
          priceId = parts[parts.length - 1];
        }
      } catch (e) {
        console.warn('Could not extract price ID from checkout URL:', e);
      }
      
      if (!priceId && url.searchParams.has('priceId')) {
        priceId = url.searchParams.get('priceId') || '';
      }
      
      // Extract other parameters
      const planId = url.searchParams.get('plan_id') || '';
      const successUrl = url.searchParams.get('success_url') || '';
      const cancelUrl = url.searchParams.get('cancel_url') || '';
      
      // Open Paddle checkout
      if (priceId) {
        // If we have a price ID, open Paddle checkout directly
        window.Paddle.Checkout.open({
          items: [{ priceId, quantity: 1 }],
          customData: { plan_id: planId },
          successCallback: options?.successCallback || (() => {
            if (successUrl) {
              window.location.href = successUrl;
            } else {
              window.location.href = `/subscription/success?plan_id=${planId}`;
            }
          }),
          closeCallback: options?.closeCallback || (() => {
            if (cancelUrl) {
              window.location.href = cancelUrl;
            }
          }),
          errorCallback: options?.errorCallback
        });
        return true;
      } else {
        // Otherwise use the full checkout URL
        window.Paddle.Checkout.open({
          override: checkoutUrl,
          successCallback: options?.successCallback,
          closeCallback: options?.closeCallback,
          errorCallback: options?.errorCallback
        });
        return true;
      }
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
      Setup: (options: { 
        vendor: string;
        environment?: 'sandbox' | 'production';
      }) => void;
      Environment?: {
        set: (env: 'sandbox' | 'production') => void;
      };
      Checkout: {
        open: (options: any) => void;
      };
    };
  }
}