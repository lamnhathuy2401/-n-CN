import type { Course, DashboardStats, Submission, User } from "./types";

const API_BASE = import.meta.env.VITE_API_URL?.replace(/\/$/, "") || "";

function authHeaders(token?: string | null): HeadersInit {
  const headers: HeadersInit = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
}

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const data = await res.json();
      detail = data.detail || JSON.stringify(data);
    } catch {
      /* ignore */
    }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return res.json() as Promise<T>;
}

export async function login(email: string, password: string): Promise<string> {
  const res = await fetch(`${API_BASE}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const data = await handle<{ access_token: string }>(res);
  return data.access_token;
}

export async function fetchMe(token: string): Promise<User> {
  const res = await fetch(`${API_BASE}/api/auth/me`, {
    headers: authHeaders(token),
  });
  return handle<User>(res);
}

export async function fetchCourses(token: string): Promise<Course[]> {
  const res = await fetch(`${API_BASE}/api/courses`, {
    headers: authHeaders(token),
  });
  return handle<Course[]>(res);
}

export async function fetchSubmissions(token: string): Promise<Submission[]> {
  const res = await fetch(`${API_BASE}/api/submissions`, {
    headers: authHeaders(token),
  });
  return handle<Submission[]>(res);
}

export async function fetchSubmission(token: string, id: number): Promise<Submission> {
  const res = await fetch(`${API_BASE}/api/submissions/${id}`, {
    headers: authHeaders(token),
  });
  return handle<Submission>(res);
}

export async function createSubmission(
  token: string,
  payload: { courseId: number; title: string; description?: string; files: File[] }
): Promise<Submission> {
  const form = new FormData();
  form.append("course_id", String(payload.courseId));
  form.append("title", payload.title);
  if (payload.description) form.append("description", payload.description);
  payload.files.forEach((f) => form.append("files", f));

  const res = await fetch(`${API_BASE}/api/submissions`, {
    method: "POST",
    headers: authHeaders(token),
    body: form,
  });
  return handle<Submission>(res);
}

export async function fetchReviewQueue(token: string): Promise<Submission[]> {
  const res = await fetch(`${API_BASE}/api/reviews/queue`, {
    headers: authHeaders(token),
  });
  return handle<Submission[]>(res);
}

export async function submitReview(
  token: string,
  submissionId: number,
  decision: string,
  note?: string
): Promise<Submission> {
  const res = await fetch(`${API_BASE}/api/reviews/${submissionId}`, {
    method: "POST",
    headers: {
      ...authHeaders(token),
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ decision, note }),
  });
  return handle<Submission>(res);
}

export async function fetchStats(token: string): Promise<DashboardStats> {
  const res = await fetch(`${API_BASE}/api/dashboard/stats`, {
    headers: authHeaders(token),
  });
  return handle<DashboardStats>(res);
}

export function imageUrl(submissionId: number, imageId: number): string {
  return `${API_BASE}/api/submissions/${submissionId}/images/${imageId}/file`;
}
