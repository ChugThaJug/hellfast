// frontend/src/lib/utils/development.ts
import { browser } from '$app/environment';

/**
 * Check if we're running in development mode
 */
export function isDevelopmentMode(): boolean {
  if (!browser) return false;
  
  // Check if we're in development build
  const isDev = import.meta.env.DEV === true;
  
  // Also check for specific environment variables that might indicate dev mode
  const useDevAuth = import.meta.env.VITE_USE_DEV_AUTH === 'true';
  
  return isDev || useDevAuth;
}

/**
 * Helper for development mode to handle missing API functionality
 */
export function handleDevelopmentFallback<T>(fallbackData: T, error: any): T {
  if (isDevelopmentMode()) {
    console.warn('Development mode fallback activated due to error:', error);
    return fallbackData;
  }
  throw error;
}

/**
 * Generate mock data for subscription plans in development mode
 */
export function getMockSubscriptionPlans() {
  return [
    {
      id: "free",
      name: "Free",
      price: 0,
      monthly_quota: 3,
      features: ["simple_mode", "bullet_points", "summary"],
      max_video_length: 10
    },
    {
      id: "pro",
      name: "Pro",
      price: 4.99,
      yearly_price: 49.99,
      monthly_quota: 15,
      features: ["simple_mode", "detailed_mode", "bullet_points", "summary", "step_by_step"],
      max_video_length: 30
    },
    {
      id: "max",
      name: "Max",
      price: 9.99,
      yearly_price: 99.99,
      monthly_quota: 50,
      features: ["simple_mode", "detailed_mode", "bullet_points", "summary", "step_by_step", "podcast_article", "api_access"],
      max_video_length: 120
    }
  ];
}

/**
 * Generate mock subscription status for development mode
 */
export function getMockSubscriptionStatus() {
  return {
    plan_id: "free",
    status: "active",
    current_period_end: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
    monthly_quota: 3,
    used_quota: 0,
    features: ["simple_mode", "bullet_points", "summary"],
    max_video_length: 10
  };
}