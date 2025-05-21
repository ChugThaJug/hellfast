/**
 * Client-side hooks for SvelteKit
 */
import type { HandleClientError } from '@sveltejs/kit';
import { goto } from '$app/navigation';

// Add init function that was missing from previous build
export function init() {
  // This function is required for Svelte 5 with SvelteKit
  return {};
}

// Handle client-side errors
export const handleError: HandleClientError = ({ error, event }) => {
  // Only handle auth errors
  if (error instanceof Error && error.message.includes('Authentication required')) {
    // Navigate to login page when auth errors happen
    goto('/auth/login');
    return {
      message: 'Please log in to continue'
    };
  }

  // Let other errors go through normal handling
  return {
    message: 'An unexpected error occurred'
  };
};