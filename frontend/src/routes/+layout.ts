/**
 * Root layout load function to handle authentication state on initial load
 */
import type { LayoutLoad } from './$types';
import { browser } from '$app/environment';

export const ssr = false; // Disable SSR at root layout level
export const prerender = false;

export const load: LayoutLoad = async () => {
  // Check authentication status - safely use localStorage only in browser
  let token = null;
  if (browser) {
    token = localStorage.getItem('token');
  }
  
  // Return authentication status for all pages to use
  return {
    isAuthenticated: Boolean(token),
    platform: {
      browser: browser
    }
  };
};
