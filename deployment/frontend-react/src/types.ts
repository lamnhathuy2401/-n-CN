export type Role = "student" | "lecturer" | "admin";

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: Role;
}

export interface Course {
  id: number;
  code: string;
  name: string;
  description?: string | null;
  lecturer_id: number;
}

export interface Analysis {
  prediction?: string | null;
  prob_ai?: number | null;
  prob_real?: number | null;
  threshold_used?: number | null;
  model_available: boolean;
  metadata: Record<string, unknown>;
  risk_score?: number | null;
  risk_level?: string | null;
  signals: Array<{
    name: string;
    value: unknown;
    weight: number;
    contribution: number;
    message: string;
  }>;
}

export interface SubmissionImage {
  id: number;
  original_filename: string;
  content_type?: string | null;
  file_size: number;
  width?: number | null;
  height?: number | null;
  analysis?: Analysis | null;
}

export interface Review {
  id: number;
  reviewer_id: number;
  decision: string;
  note?: string | null;
  created_at: string;
  updated_at: string;
}

export interface Submission {
  id: number;
  course_id: number;
  student_id: number;
  title: string;
  description?: string | null;
  status: string;
  overall_risk_score?: number | null;
  overall_risk_level?: string | null;
  created_at: string;
  updated_at: string;
  images: SubmissionImage[];
  review?: Review | null;
  student_name?: string | null;
  course_name?: string | null;
  disclaimer: string;
}

export interface DashboardStats {
  total_submissions: number;
  pending_review: number;
  approved: number;
  flagged: number;
  needs_clarification: number;
  high_risk: number;
  medium_risk: number;
  low_risk: number;
  model_loaded: boolean;
}
