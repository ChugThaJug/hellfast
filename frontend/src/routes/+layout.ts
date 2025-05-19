/**
 * Root layout load function to handle authentication state on initial load
 */
import type { LayoutLoad } from './$types';
import { safeLocalStorage } from '$lib/utils/browser';
import { browser } from '$app/environment';

export const ssr = false; // Disable SSR at root layout level
export const prerender = false;

export const load: LayoutLoad = async () => {
  // Check authentication status
  const token = safeLocalStorage.getItem('token');
  
  // Return authentication status for all pages to use
  return {
    isAuthenticated: Boolean(token),
    platform: {
      browser: browser
    }
  };
};
