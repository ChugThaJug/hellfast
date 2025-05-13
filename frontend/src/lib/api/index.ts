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
  // Login with Firebase token
  loginWithFirebase: (token: string): Promise<User> =>
    fetchWithAuth('/firebase/verify-token', {
      method: 'POST',
      body: JSON.stringify({ token })
    }),
  
  // Login for development (no token needed in dev mode)
  loginForDevelopment: (): Promise<User> =>
    fetchWithAuth('/firebase/verify-token', {
      method: 'POST',
      body: JSON.stringify({}) // Empty body will work in dev mode
    }),
  
  // Get user profile
  getProfile: (): Promise<User> =>
    fetchWithAuth('/firebase/profile'),
    
  // Handle OAuth callback
  handleOAuthCallback: (code: string): Promise<{access_token: string, token_type: string, user: User}> =>
    fetchWithAuth(`/oauth/google/mobile-callback?code=${code}`)
};

// Subscription API
export const subscriptionApi = {
  // Get subscription plans
  getPlans: (): Promise<SubscriptionPlan[]> =>
    fetchWithAuth('/subscription/plans'),
  
  // Get subscription status
  getStatus: (): Promise<SubscriptionStatus> =>
    fetchWithAuth('/subscription/status'),
  
  // Create subscription
  createSubscription: (planId: string): Promise<{checkout_url?: string, message?: string}> =>
    fetchWithAuth('/subscription/create', {
      method: 'POST',
      body: JSON.stringify({ plan_id: planId })
    }),
    
  // Cancel subscription
  cancelSubscription: (): Promise<{message: string}> =>
    fetchWithAuth('/subscription/cancel', {
      method: 'POST'
    })
};