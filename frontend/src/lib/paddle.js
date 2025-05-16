/**
 * Paddle.js integration helper
 */

// Paddle client token (should be fetched from backend)
const PADDLE_CLIENT_TOKEN = 'test_5c52e2f27695549cb3d902a939c';
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Initialize Paddle.js with proper setup
 * @param {boolean} sandbox - Whether to use sandbox environment
 * @param {string} token - Paddle client token
 * @returns {boolean} - Whether initialization was successful
 */
export function initializePaddle(sandbox = true, token = PADDLE_CLIENT_TOKEN) {
  if (typeof window === 'undefined' || !window.Paddle) {
    console.error('Paddle.js not loaded');
    return false;
  }

  try {
    // Set the environment if in sandbox mode
    if (sandbox) {
      window.Paddle.Environment.set('sandbox');
    }

    // Initialize Paddle with the client token (using Setup for proper configuration)
    window.Paddle.Setup({
      token,
      eventCallback: function(eventData) {
        console.log('Paddle event received:', eventData);
        
        // Handle checkout completion
        if (eventData.name === 'checkout.completed') {
          console.log('Checkout completed successfully:', eventData.data);
          // You could redirect to a success page here
        }
        
        // Handle checkout errors
        if (eventData.name === 'checkout.error') {
          console.error('Checkout error:', eventData.error || eventData.data);
        }
      }
    });

    console.log('Paddle initialized successfully with', sandbox ? 'sandbox' : 'production', 'environment');
    return true;
  } catch (error) {
    console.error('Failed to initialize Paddle:', error);
    return false;
  }
}

/**
 * Open Paddle checkout for a specific plan
 * This is a lightweight wrapper that mostly serves as a placeholder -
 * we're primarily using the backend API for checkout creation
 */
export async function openCheckout(planId, yearly = false, email = null) {
  console.warn('openCheckout is deprecated. Use the createSubscription API directly');
  
  if (!window.Paddle) {
    throw new Error('Paddle.js not loaded');
  }
  
  try {
    // Let the backend handle most of the checkout creation logic
    const response = await fetch(`${API_URL}/subscription/create`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        plan_id: planId,
        billing_cycle: yearly ? 'yearly' : 'monthly'
      })
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to create subscription');
    }
    
    const data = await response.json();
    
    if (data.checkout_url) {
      // We'll just return the data and let the calling code handle the redirect
      return data;
    }
    
    throw new Error('No checkout URL received');
  } catch (error) {
    console.error('Error creating subscription:', error);
    throw error;
  }
}

// Remove the fallback checkout method since we're only using the official Paddle integration
