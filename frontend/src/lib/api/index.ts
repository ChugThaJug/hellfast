// frontend/src/lib/api/index.ts
import type { JobStatus, ProcessedVideo, SubscriptionPlan, SubscriptionStatus, User, VideoEntry } from "./schema";
import { fetchWithAuth } from "./client";

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
      console.log("Fetching subscription plans...");
      const plans = await fetchWithAuth('/subscription/plans', {
        timeout: 30000 // Explicitly set longer timeout for this call
      });
      console.log(`Fetched ${plans?.length || 0} subscription plans`);
      return plans || [];
    } catch (error) {
      console.error("Error fetching subscription plans:", error);
      // Return empty plans array if API fails to prevent UI errors
      return [];
    }
  },
  
  // Get subscription status
  getStatus: async (): Promise<SubscriptionStatus> => {
    try {
      console.log("Fetching subscription status...");
      const status = await fetchWithAuth('/subscription/status', {
        timeout: 30000 // Explicitly set longer timeout
      });
      console.log("Fetched subscription status:", status?.plan_id);
      return status;
    } catch (error) {
      console.error("Error fetching subscription status:", error);
      throw error;
    }
  },
  
  // Create subscription
  createSubscription: async (planId: string, yearly: boolean = false): Promise<any> => {
    // Fix the request format to match what the backend expects
    const payload = {
      plan_id: planId,              // Must use snake_case to match backend
      billing_cycle: yearly ? 'yearly' : 'monthly'  // Must provide billing cycle
    };
    
    console.log('Creating subscription with payload:', payload);
    
    return fetchWithAuth('/subscription/create', {
      method: 'POST',
      body: JSON.stringify(payload),
      timeout: 30000 // Explicitly set longer timeout
    });
  },
    
  // Cancel subscription
  cancelSubscription: async (): Promise<{message: string}> => {
    try {
      console.log("Cancelling subscription...");
      const result = await fetchWithAuth('/subscription/cancel', {
        method: 'POST',
        timeout: 30000 // Explicitly set longer timeout
      });
      console.log("Subscription cancellation result:", result);
      return result;
    } catch (error) {
      console.error("Error cancelling subscription:", error);
      throw error;
    }
  }
};