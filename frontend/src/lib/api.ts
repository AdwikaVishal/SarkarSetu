/**
 * SarkarSetu AI — centralized API client.
 *
 * Reference implementation for the frontend (Person 3). Place this file at
 * `frontend/src/lib/api.ts` (or the equivalent location in your frontend
 * project). All backend communication goes through this client so auth,
 * base URL, error handling, and timeouts are consistent.
 *
 * Backend contract: docs/API_CONTRACT.md
 */

import type {
  ChatMessageRequest,
  ChatMessageResponse,
  ConversationCreate,
  ConversationResponse,
  MessageResponse,
  BusinessProfileCreate,
  BusinessProfileResponse,
  BusinessProfileUpdate,
  KnowledgeSearchRequest,
  KnowledgeSearchResponse,
  RetrievalSourceResponse,
  UserRegister,
  UserLogin,
  TokenResponse,
  RefreshTokenRequest,
  RefreshTokenResponse,
  UserMeResponse,
  LogoutResponse,
  EligibilityAssessmentRequest,
  EligibilityAssessmentResponse,
  RoadmapGenerateRequest,
  RoadmapResponse,
  RoadmapDetailResponse,
  RoadmapTaskUpdate,
  WorkflowExecutionRequest,
  WorkflowExecutionResponse,
  ClarificationResponse,
} from "@/types/api"; // adjust import path to your generated/shared types

const API_URL = process.env.NEXT_PUBLIC_API_URL;
if (!API_URL) {
  throw new Error(
    "NEXT_PUBLIC_API_URL is not defined. See frontend/.env.example"
  );
}

const API_PREFIX = "/api/v1";

type Json = Record<string, unknown> | Array<unknown> | string | number | boolean | null;

interface RequestOptions extends Omit<RequestInit, "body"> {
  params?: Record<string, string | number | boolean | undefined>;
  query?: Record<string, string | number | boolean | undefined>;
}

let accessToken: string | null = null;
let refreshToken: string | null = null;

/**
 * Set the auth tokens (call after login/register/refresh).
 */
export function setAuthTokens(tokens: {
  access_token: string;
  refresh_token: string;
}): void {
  accessToken = tokens.access_token;
  refreshToken = tokens.refresh_token;
}

/**
 * Clear auth tokens (call on logout / refresh failure).
 */
export function clearAuthTokens(): void {
  accessToken = null;
  refreshToken = null;
}

export function getAccessToken(): string | null {
  return accessToken;
}

/**
 * Build a URL with query params.
 */
function buildUrl(path: string, options?: RequestOptions): string {
  const base = `${API_URL}${API_PREFIX}${path}`;
  const searchParams = new URLSearchParams();
  const extras = { ...(options?.params ?? {}), ...(options?.query ?? {}) };
  for (const [key, value] of Object.entries(extras)) {
    if (value === undefined || value === null) continue;
    searchParams.append(key, String(value));
  }
  const qs = searchParams.toString();
  return qs ? `${base}?${qs}` : base;
}

/**
 * Core request with auth, JSON, error handling, and automatic refresh on 401.
 */
async function request<T>(
  path: string,
  options: RequestOptions = {}
): Promise<T> {
  const url = buildUrl(path, options);
  const headers: Record<string, string> = {};

  let body: BodyInit | undefined;
  let isFormData = false;

  if (options.body) {
    if (options.body instanceof FormData) {
      isFormData = true;
      body = options.body;
    } else {
      headers["Content-Type"] = "application/json";
      body = JSON.stringify(options.body);
    }
  }

  if (accessToken) {
    headers["Authorization"] = `Bearer ${accessToken}`;
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 30000);

  try {
    const res = await fetch(url, {
      ...options,
      headers,
      body,
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    // 401 → attempt token refresh once, then retry
    if (res.status === 401 && refreshToken) {
      clearTimeout(timeoutId);
      try {
        const refreshed = await refreshAccessToken();
        if (refreshed) {
          headers["Authorization"] = `Bearer ${accessToken}`;
          const retry = await fetch(url, {
            ...options,
            headers,
            body,
            signal: controller.signal,
          });
          return await parseResponse<T>(retry);
        }
      } catch {
        // refresh failed — fall through to error handling
      }
      clearAuthTokens();
      throw new ApiError("Session expired. Please log in again.", 401);
    }

    return await parseResponse<T>(res);
  } catch (err) {
    clearTimeout(timeoutId);
    if (err instanceof ApiError) throw err;
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new ApiError("Request timed out.", 408);
    }
    throw new ApiError(
      err instanceof Error ? err.message : "Network error.",
      0
    );
  }
}

async function parseResponse<T>(res: Response): Promise<T> {
  const isJson = res.headers
    .get("content-type")
    ?.includes("application/json");

  let body: any;
  if (isJson) {
    body = await res.json();
  } else {
    const text = await res.text();
    body = text ? text : null;
  }

  if (!res.ok) {
    const detail =
      body && typeof body === "object" && "detail" in body
        ? body.detail
        : `Request failed with status ${res.status}`;
    throw new ApiError(String(detail), res.status);
  }

  return body as T;
}

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
  static isApiError(err: unknown): err is ApiError {
    return err instanceof ApiError;
  }
}

/**
 * Refresh access token using the stored refresh token.
 */
async function refreshAccessToken(): Promise<boolean> {
  if (!refreshToken) return false;
  try {
    const res = await fetch(`${API_URL}${API_PREFIX}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    if (!res.ok) return false;
    const data = (await res.json()) as RefreshTokenResponse;
    setAuthTokens({
      access_token: data.access_token,
      refresh_token: data.refresh_token,
    });
    return true;
  } catch {
    return false;
  }
}

/* ------------------------------------------------------------------ */
/* Auth                                                               */
/* ------------------------------------------------------------------ */

export const authApi = {
  register: (data: UserRegister) =>
    request<TokenResponse>("/auth/register", {
      method: "POST",
      body: data,
    }),
  login: (data: UserLogin) =>
    request<TokenResponse>("/auth/login", {
      method: "POST",
      body: data,
    }),
  refresh: (data: RefreshTokenRequest) =>
    request<RefreshTokenResponse>("/auth/refresh", {
      method: "POST",
      body: data,
    }),
  logout: (data: RefreshTokenRequest) =>
    request<LogoutResponse>("/auth/logout", {
      method: "POST",
      body: data,
    }),
  me: () => request<UserMeResponse>("/auth/me", { method: "GET" }),
};

/* ------------------------------------------------------------------ */
/* Business profiles                                                  */
/* ------------------------------------------------------------------ */

export const businessApi = {
  create: (data: BusinessProfileCreate) =>
    request<BusinessProfileResponse>("/businesses/", {
      method: "POST",
      body: data,
    }),
  list: (params?: { skip?: number; limit?: number }) =>
    request<BusinessProfileResponse[]>("/businesses/", {
      method: "GET",
      params,
    }),
  listArchived: () =>
    request<BusinessProfileResponse[]>("/businesses/archived", {
      method: "GET",
    }),
  get: (businessId: string) =>
    request<BusinessProfileResponse>(`/businesses/${businessId}`, {
      method: "GET",
    }),
  update: (businessId: string, data: BusinessProfileUpdate) =>
    request<BusinessProfileResponse>(`/businesses/${businessId}`, {
      method: "PATCH",
      body: data,
    }),
  archive: (businessId: string) =>
    request<void>(`/businesses/${businessId}`, { method: "DELETE" }),
  restore: (businessId: string) =>
    request<BusinessProfileResponse>(
      `/businesses/${businessId}/restore`,
      { method: "POST" }
    ),
  setDefault: (businessId: string) =>
    request<BusinessProfileResponse>(
      `/businesses/${businessId}/default`,
      { method: "PATCH" }
    ),
};

/* ------------------------------------------------------------------ */
/* Chat                                                               */
/* ------------------------------------------------------------------ */

export const chatApi = {
  sendMessage: (data: ChatMessageRequest) =>
    request<ChatMessageResponse>("/chat/message", {
      method: "POST",
      body: data,
    }),
  conversationStatus: (conversationId: string) =>
    request<ConversationResponse>(
      `/chat/conversations/${conversationId}/status`,
      { method: "GET" }
    ),
};

/* ------------------------------------------------------------------ */
/* Conversations                                                      */
/* ------------------------------------------------------------------ */

export const conversationApi = {
  create: (data: ConversationCreate) =>
    request<ConversationResponse>("/conversations/", {
      method: "POST",
      body: data,
    }),
  list: (params?: { skip?: number; limit?: number }) =>
    request<ConversationResponse[]>("/conversations/", {
      method: "GET",
      params,
    }),
  get: (conversationId: string) =>
    request<ConversationResponse>(`/conversations/${conversationId}`, {
      method: "GET",
    }),
  update: (conversationId: string, data: { title?: string; status?: string }) =>
    request<ConversationResponse>(`/conversations/${conversationId}`, {
      method: "PATCH",
      body: data,
    }),
  archive: (conversationId: string) =>
    request<void>(`/conversations/${conversationId}`, {
      method: "DELETE",
    }),
  restore: (conversationId: string) =>
    request<ConversationResponse>(
      `/conversations/${conversationId}/restore`,
      { method: "POST" }
    ),
  createMessage: (conversationId: string, data: { content: string; intent?: string }) =>
    request<MessageResponse>(`/conversations/${conversationId}/messages`, {
      method: "POST",
      body: data,
    }),
  listMessages: (conversationId: string, params?: { skip?: number; limit?: number }) =>
    request<MessageResponse[]>(`/conversations/${conversationId}/messages`, {
      method: "GET",
      params,
    }),
};

/* ------------------------------------------------------------------ */
/* Eligibility                                                        */
/* ------------------------------------------------------------------ */

export const eligibilityApi = {
  assess: (data: EligibilityAssessmentRequest) =>
    request<EligibilityAssessmentResponse>("/eligibility/assess", {
      method: "POST",
      body: data,
    }),
  get: (assessmentId: string) =>
    request<EligibilityAssessmentResponse>(
      `/eligibility/assessments/${assessmentId}`,
      { method: "GET" }
    ),
  listForBusiness: (businessId: string) =>
    request<EligibilityAssessmentResponse[]>(
      `/eligibility/businesses/${businessId}/assessments`,
      { method: "GET" }
    ),
};

/* ------------------------------------------------------------------ */
/* Knowledge search (citations)                                       */
/* ------------------------------------------------------------------ */

export const knowledgeApi = {
  search: (data: KnowledgeSearchRequest) =>
    request<KnowledgeSearchResponse>("/knowledge/search", {
      method: "POST",
      body: data,
    }),
};

/* ------------------------------------------------------------------ */
/* Roadmaps                                                           */
/* ------------------------------------------------------------------ */

export const roadmapApi = {
  generate: (data: RoadmapGenerateRequest) =>
    request<RoadmapResponse>("/roadmaps/generate", {
      method: "POST",
      body: data,
    }),
  list: (params?: { business_profile_id?: string; status?: string }) =>
    request<{ roadmaps: RoadmapResponse[]; total_count: number }>(
      "/roadmaps/",
      { method: "GET", params },
    ),
  get: (roadmapId: string) =>
    request<RoadmapDetailResponse>(`/roadmaps/${roadmapId}`, {
      method: "GET",
    }),
  regenerate: (roadmapId: string, data: { preserve_completed?: boolean; reason?: string }) =>
    request<RoadmapResponse>(`/roadmaps/${roadmapId}/regenerate`, {
      method: "POST",
      body: data,
    }),
  progress: (roadmapId: string) =>
    request<{
      completed_tasks: number;
      total_tasks: number;
      progress_percentage: number;
    }>(`/roadmaps/${roadmapId}/progress`, { method: "GET" }),
  updateTask: (
    roadmapId: string,
    taskId: string,
    data: RoadmapTaskUpdate
  ) =>
    request<any>(`/roadmaps/${roadmapId}/tasks/${taskId}`, {
      method: "PATCH",
      body: data,
    }),
  completeTask: (roadmapId: string, taskId: string) =>
    request<any>(
      `/roadmaps/${roadmapId}/tasks/${taskId}/complete`,
      { method: "POST" }
    ),
  skipTask: (roadmapId: string, taskId: string) =>
    request<any>(
      `/roadmaps/${roadmapId}/tasks/${taskId}/skip`,
      { method: "POST" }
    ),
};

/* ------------------------------------------------------------------ */
/* Workflows                                                          */
/* ------------------------------------------------------------------ */

export const workflowApi = {
  start: (data: WorkflowExecutionRequest) =>
    request<WorkflowExecutionResponse>("/workflows/", {
      method: "POST",
      body: data,
    }),
  get: (workflowId: string) =>
    request<WorkflowExecutionResponse>(`/workflows/${workflowId}`, {
      method: "GET",
    }),
  respond: (workflowId: string, data: ClarificationResponse) =>
    request<WorkflowExecutionResponse>(
      `/workflows/${workflowId}/respond`,
      { method: "POST", body: data }
    ),
  resume: (workflowId: string, data: { message?: string }) =>
    request<WorkflowExecutionResponse>(
      `/workflows/${workflowId}/resume`,
      { method: "POST", body: data }
    ),
  cancel: (workflowId: string) =>
    request<WorkflowExecutionResponse>(
      `/workflows/${workflowId}/cancel`,
      { method: "POST" }
    ),
  listServiceTypes: () =>
    request<{ service_types: Array<{ service_type: string; display_name: string; description: string }> }>(
      "/workflows/",
      { method: "GET" }
    ),
};

/* ------------------------------------------------------------------ */
/* Health                                                             */
/* ------------------------------------------------------------------ */

export const healthApi = {
  check: () => request<{ status: string; application: string; version: string }>(
    "/health",
    { method: "GET" }
  ),
  db: () => request<{ status: string; database: string }>(
    "/health/db",
    { method: "GET" }
  ),
};

export { ApiError };
