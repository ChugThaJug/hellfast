// frontend/src/lib/api/schema.ts
export interface User {
  id: number;
  username: string;
  email: string;
  display_name?: string;
  photo_url?: string;
  firebase_uid?: string;
  is_active: boolean;
}

export interface JobStatus {
  job_id: string;
  video_id: string;
  status: "pending" | "processing" | "completed" | "failed";
  progress: number;
  error?: string;
  mode: "simple" | "detailed";
  output_format: "bullet_points" | "summary" | "step_by_step" | "podcast_article";
  created_at: string;
  completed_at?: string;
}

export interface ProcessedVideo {
  video_id: string;
  title: string;
  output_format: "bullet_points" | "summary" | "step_by_step" | "podcast_article";
  content: any; // JSON content structure depends on output_format
  stats: {
    input_tokens: number;
    output_tokens: number;
    cost: number;
    mode: "simple" | "detailed";
  };
}

export interface VideoEntry {
  id: number;
  video_id: string;
  title: string;
  status: "pending" | "processing" | "completed" | "failed";
  processing_mode: "simple" | "detailed";
  output_format: "bullet_points" | "summary" | "step_by_step" | "podcast_article";
  created_at: string;
  updated_at: string;
}

export interface SubscriptionPlan {
  id: string;
  name: string;
  price: number;
  monthly_quota: number;
  features: string[];
}

export interface SubscriptionStatus {
  plan_id: string;
  status: string;
  current_period_end: string;
  monthly_quota: number;
  used_quota: number;
  features: string[];
}