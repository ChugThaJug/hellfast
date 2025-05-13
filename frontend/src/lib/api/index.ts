// src/lib/api/index.ts
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Helper function for authenticated requests
async function fetchWithAuth(endpoint: string, options: RequestInit = {}) {
  const token = localStorage.getItem('token');
  
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    ...options.headers
  };
  
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers
  });
  
  if (!response.ok) {
    let errorData;
    try {
      errorData = await response.json();
    } catch (e) {
      throw new Error(`HTTP error ${response.status}`);
    }
    throw new Error(errorData.detail || `HTTP error ${response.status}`);
  }
  
  return response.json();
}

// Video Processing API
export const videoApi = {
  // Process a YouTube video
  processVideo: (videoUrl: string, mode: string = 'detailed', outputFormat: string = 'step_by_step') =>
    fetchWithAuth('/youtube/process/' + extractVideoId(videoUrl), {
      method: 'POST',
      body: JSON.stringify({ mode, output_format: outputFormat })
    }),
  
  // Get processing job status
  getJobStatus: (jobId: string) =>
    fetchWithAuth(`/youtube/job-status/${jobId}`),
  
  // Get processed video result
  getVideoResult: (videoId: string) =>
    fetchWithAuth(`/youtube/video-result/${videoId}`),
    
  // Get user videos
  getUserVideos: () =>
    fetchWithAuth('/youtube/user/videos')
};

// Authentication API
export const authApi = {
  // Login with Firebase token
  loginWithFirebase: (token: string) =>
    fetchWithAuth('/firebase/verify-token', {
      method: 'POST',
      body: JSON.stringify({ token })
    }),
  
  // Get user profile
  getProfile: () =>
    fetchWithAuth('/firebase/profile'),
    
  // Google OAuth login
  getGoogleAuthUrl: () =>
    fetchWithAuth('/oauth/google/login'),
    
  // Handle OAuth callback
  handleOAuthCallback: (code: string) =>
    fetchWithAuth(`/oauth/google/mobile-callback?code=${code}`)
};

// Subscription API
export const subscriptionApi = {
  // Get subscription plans
  getPlans: () =>
    fetchWithAuth('/subscription/plans'),
  
  // Get subscription status
  getStatus: () =>
    fetchWithAuth('/subscription/status'),
  
  // Create subscription
  createSubscription: (planId: string) =>
    fetchWithAuth('/subscription/create', {
      method: 'POST',
      body: JSON.stringify({ plan_id: planId })
    }),
    
  // Cancel subscription
  cancelSubscription: () =>
    fetchWithAuth('/subscription/cancel', {
      method: 'POST'
    })
};

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