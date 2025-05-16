// frontend/src/lib/api/index.ts
import type { JobStatus, ProcessedVideo, SubscriptionPlan, SubscriptionStatus, User, VideoEntry } from "./schema";
import { fetchWithAuth } from "./client";
import { isDevelopmentMode, getMockSubscriptionPlans, getMockSubscriptionStatus } from '$lib/utils/development';

// Helper function to extract video ID from YouTube URL
function extractVideoId(url: string): string {
  const regex = /(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})/;
  const match = url.match(regex);
  
  if (match && match[1]) {
    return match[1];
  }
  
  // If no match is found, assume the URL is already an ID
  return url;
}

// Video Processing API
export const videoApi = {
  // Process a YouTube video
  processVideo: (videoUrl: string, mode: string = 'detailed', outputFormat: string = 'step_by_step') =>
    fetchWithAuth(`/youtube/process/${extractVideoId(videoUrl)}`, {
      method: 'POST',
      body: JSON.stringify({ mode, output_format: outputFormat })
    }),
  
  // Get processing job status
  getJobStatus: (jobId: string): Promise<JobStatus> =>
    fetchWithAuth(`/youtube/job-status/${jobId}`),
  
  // Get processed video result
  getVideoResult: (videoId: string): Promise<ProcessedVideo> =>
    fetchWithAuth(`/youtube/video-result/${videoId}`),
    
  // Get user videos
  getUserVideos: (): Promise<VideoEntry[]> =>
    fetchWithAuth('/youtube/user/videos'),
    
  // Delete a video
  deleteVideo: (videoId: string): Promise<{message: string}> =>
    fetchWithAuth(`/youtube/video/${videoId}`, {
      method: 'DELETE'
    })
};

// Authentication API
export const authApi = {
  // Verify token with backend
  verifyToken: (token: string): Promise<User> =>
    fetchWithAuth('/auth/verify-token', {
      method: 'POST',
      body: JSON.stringify({ token })
    }),
  
  // Get user profile
  getProfile: (): Promise<User> =>
    fetchWithAuth('/auth/profile'),
  
  // Development login (no token needed in dev mode)
  devLogin: (): Promise<User> =>
    fetchWithAuth('/auth/verify-token', {
      method: 'POST',
      body: JSON.stringify({}) // Empty body will work in dev mode
    }),
    
  // Handle OAuth callback
  handleOAuthCallback: (code: string): Promise<{access_token: string, token_type: string, user: User}> =>
    fetchWithAuth(`/oauth/google/mobile-callback?code=${code}`, {
      skipAuth: true // No auth needed for this endpoint
    })
};

// Subscription API
export const subscriptionApi = {
  // Get subscription plans
  getPlans: async (): Promise<SubscriptionPlan[]> => {
    try {
      return await fetchWithAuth('/subscription/plans');
    } catch (error) {
      // Use development fallback if in development mode
      if (isDevelopmentMode()) {
        console.warn('Using mock subscription plans in development mode');
        return getMockSubscriptionPlans();
      }
      throw error;
    }
  },
  
  // Get subscription status
  getStatus: async (): Promise<SubscriptionStatus> => {
    try {
      return await fetchWithAuth('/subscription/status');
    } catch (error) {
      // Use development fallback if in development mode
      if (isDevelopmentMode()) {
        console.warn('Using mock subscription status in development mode');
        return getMockSubscriptionStatus();
      }
      throw error;
    }
  },
  
  // Create subscription
  createSubscription: async (data: {plan_id: string, yearly: boolean}): Promise<{checkout_url?: string, message?: string}> => {
    try {
      return await fetchWithAuth('/subscription/create', {
        method: 'POST',
        body: JSON.stringify(data)
      });
    } catch (error) {
      // In development mode, create a mock checkout URL
      if (isDevelopmentMode()) {
        console.warn('Using mock subscription checkout in development mode');
        const frontendUrl = window.location.origin;
        return { 
          checkout_url: `${frontendUrl}/subscription/dev-checkout?plan_id=${data.plan_id}&billing=${data.yearly ? 'yearly' : 'monthly'}` 
        };
      }
      throw error;
    }
  },
    
  // Cancel subscription
  cancelSubscription: (): Promise<{message: string}> =>
    fetchWithAuth('/subscription/cancel', {
      method: 'POST'
    })
};