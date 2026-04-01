import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: API_URL,
  headers: { "Content-Type": "application/json" },
});

// ── Types ─────────────────────────────────────────────────────────────────────

export interface Prospect {
  id: string;
  name: string;
  email: string;
  role?: string;
  company?: string;
  industry?: string;
  website?: string;
  linkedin_url?: string;
  notes?: string;
  tags?: string[];
  outreach_status: "new" | "researched" | "drafted" | "sent" | "replied" | "archived";
  created_at: string;
  updated_at: string;
}

export interface ProspectListResponse {
  items: Prospect[];
  total: number;
  page: number;
  page_size: number;
}

export interface ResearchSummary {
  id: string;
  prospect_id: string;
  content: string;
  sources?: string[];
  created_at: string;
}

export interface EmailDraft {
  id: string;
  prospect_id: string;
  subject: string;
  opening_line: string;
  body: string;
  cta: string;
  follow_up?: string;
  tone: string;
  status: "draft" | "approved" | "sent" | "archived";
  is_edited: boolean;
  langfuse_trace_id?: string;
  generation_metadata?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface SentEmail {
  id: string;
  prospect_id: string;
  draft_id: string;
  subject: string;
  body: string;
  sent_at: string;
  send_status: string;
  reply_status: "none" | "replied" | "positive" | "negative";
  replied_at?: string;
  follow_up_scheduled_at?: string;
  follow_up_sent: boolean;
}

export interface AnalyticsSummary {
  total_prospects: number;
  prospects_by_status: Record<string, number>;
  total_drafts: number;
  total_sent: number;
  reply_rate: number;
  avg_rating?: number;
  emails_sent_last_7_days: number;
  emails_sent_last_30_days: number;
}

// ── Prospect API ──────────────────────────────────────────────────────────────

export const prospectsApi = {
  list: (params?: {
    page?: number;
    page_size?: number;
    status?: string;
    search?: string;
  }) => api.get<ProspectListResponse>("/prospects", { params }),

  get: (id: string) => api.get<Prospect>(`/prospects/${id}`),

  create: (data: Partial<Prospect>) => api.post<Prospect>("/prospects", data),

  update: (id: string, data: Partial<Prospect>) =>
    api.patch<Prospect>(`/prospects/${id}`, data),

  delete: (id: string) => api.delete(`/prospects/${id}`),

  uploadCsv: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return api.post<{ created: number; skipped: number }>("/prospects/upload", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },

  research: (id: string) => api.post<ResearchSummary>(`/prospects/${id}/research`),

  getResearch: (id: string) => api.get<ResearchSummary>(`/prospects/${id}/research`),
};

// ── Email API ─────────────────────────────────────────────────────────────────

export const emailsApi = {
  generate: (data: {
    prospect_id: string;
    tone?: string;
    additional_context?: string;
  }) => api.post<EmailDraft>("/emails/generate", data),

  list: (params?: { prospect_id?: string; status?: string }) =>
    api.get<EmailDraft[]>("/emails", { params }),

  get: (id: string) => api.get<EmailDraft>(`/emails/${id}`),

  update: (id: string, data: Partial<EmailDraft>) =>
    api.patch<EmailDraft>(`/emails/${id}`, data),

  send: (data: { draft_id: string; schedule_follow_up_days?: number }) =>
    api.post<SentEmail>("/emails/send", data),

  listSent: (params?: { prospect_id?: string }) =>
    api.get<SentEmail[]>("/emails/sent", { params }),

  getSent: (id: string) => api.get<SentEmail>(`/emails/sent/${id}`),

  updateReplyStatus: (sentId: string, reply_status: string) =>
    api.patch<SentEmail>(`/emails/sent/${sentId}/reply-status`, null, {
      params: { reply_status },
    }),

  submitFeedback: (draftId: string, data: { rating?: number; feedback_text?: string }) =>
    api.post(`/emails/${draftId}/feedback`, data),
};

// ── Analytics API ─────────────────────────────────────────────────────────────

export const analyticsApi = {
  getSummary: () => api.get<AnalyticsSummary>("/analytics"),
};
