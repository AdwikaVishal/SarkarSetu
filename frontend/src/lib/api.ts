// Frontend API Client
// Centralized fetch-based client with auth, auto-refresh, error handling
// Source: docs/AUTH_INTEGRATION.md, docs/API_CONTRACT.md

import type {
  // Auth
  RegisterRequest,
  LoginRequest,
  RefreshRequest,
  LogoutRequest,
  TokenResponse,
  UserResponse,
  MeResponse,
  // Business
  BusinessProfileCreate,
  BusinessProfileUpdate,
  BusinessProfileResponse,
  BusinessProfileListResponse,
  BusinessStructure,
  BusinessStage,
  OperatingMode,
  // Chat
  ChatMessageRequest,
  ChatMessageResponse,
  IntentInfo,
  ExtractedEntitySummary,
  ResponseType,
  ConversationCreate,
  ConversationResponse,
  MessageResponse,
  ConversationMessagesResponse,
  ConversationStatusResponse,
  // Eligibility
  EligibilityAssessRequest,
  EligibilityAssessmentResponse,
  ConditionResult,
  AssessmentStatus,
  EligibilityRuleSetResponse,
  // Knowledge
  KnowledgeSearchRequest,
  KnowledgeSearchResponse,
  RetrievalSourceResponse,
  // Roadmaps
  RoadmapGenerateRequest,
  RoadmapRegenerateRequest,
  RoadmapResponse,
  RoadmapListResponse,
  RoadmapProgress,
  RoadmapDetailResponse,
  RoadmapTaskResponse,
  RoadmapTaskUpdate,
  TaskStatus,
  TaskCategory,
  TaskPriority,
  RoadmapStatus,
  // Workflows
  WorkflowExecutionRequest,
  WorkflowExecutionResponse,
  WorkflowStepResult,
  WorkflowStatus,
  StepStatus,
  ClarificationResponse,
  ResumeWorkflowRequest,
  WorkflowServiceTypeInfo,
  WorkflowServiceTypeResponse,
  // AI/Intent
  AIGenerateRequest,
  AIGenerateResponse,
  AIJSONRequest,
  AIJSONResponse,
  AIStructuredRequest,
  AIStructuredResponse,
  IntentClassifyRequest,
  IntentClassifyResponse,
  IntentExtractRequest,
  IntentExtractResponse,
  IntentAnalyzeRequest,
  IntentAnalyzeResponse,
  AIHealthResponse,
  // Health
  HealthResponse,
  HealthDBResponse,
  // Documents
  DocumentUploadResponse,
  DocumentResponse,
  DocumentListResponse,
  DocumentMatchingResponse,
  DocumentDeleteResponse,
  MatchingDocument,
  // Recommendations
  RecommendationRequest,
  RecommendationResponse,
  RecommendationDetail,
  RecommendationListResponse,
  SchemeDetail,
} from "@/types/api";

// Re-export all types for convenience
export type {
  RegisterRequest,
  LoginRequest,
  RefreshRequest,
  LogoutRequest,
  TokenResponse,
  UserResponse,
  MeResponse,
  BusinessProfileCreate,
  BusinessProfileUpdate,
  BusinessProfileResponse,
  BusinessProfileListResponse,
  BusinessStructure,
  BusinessStage,
  OperatingMode,
  ChatMessageRequest,
  ChatMessageResponse,
  IntentInfo,
  ExtractedEntitySummary,
  ResponseType,
  ConversationCreate,
  ConversationResponse,
  MessageResponse,
  ConversationMessagesResponse,
  ConversationStatusResponse,
  EligibilityAssessRequest,
  EligibilityAssessmentResponse,
  ConditionResult,
  AssessmentStatus,
  EligibilityRuleSetResponse,
  KnowledgeSearchRequest,
  KnowledgeSearchResponse,
  RetrievalSourceResponse,
  RoadmapGenerateRequest,
  RoadmapRegenerateRequest,
  RoadmapResponse,
  RoadmapListResponse,
  RoadmapProgress,
  RoadmapDetailResponse,
  RoadmapTaskResponse,
  RoadmapTaskUpdate,
  TaskStatus,
  TaskCategory,
  TaskPriority,
  RoadmapStatus,
  WorkflowExecutionRequest,
  WorkflowExecutionResponse,
  WorkflowStepResult,
  WorkflowStatus,
  StepStatus,
  ClarificationResponse,
  ResumeWorkflowRequest,
  WorkflowServiceTypeInfo,
  WorkflowServiceTypeResponse,
  AIGenerateRequest,
  AIGenerateResponse,
  AIJSONRequest,
  AIJSONResponse,
  AIStructuredRequest,
  AIStructuredResponse,
  IntentClassifyRequest,
  IntentClassifyResponse,
  IntentExtractRequest,
  IntentExtractResponse,
  IntentAnalyzeRequest,
  IntentAnalyzeResponse,
  AIHealthResponse,
  HealthResponse,
  HealthDBResponse,
  DocumentUploadResponse,
  DocumentResponse,
  DocumentListResponse,
  DocumentMatchingResponse,
  DocumentDeleteResponse,
  MatchingDocument,
  RecommendationRequest,
  RecommendationResponse,
  RecommendationDetail,
  RecommendationListResponse,
  SchemeDetail,
};

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const API_PREFIX = "/api/v1";

// Token storage keys
const ACCESS_TOKEN_KEY = "sarkarsetu_access_token";
const REFRESH_TOKEN_KEY = "sarkarsetu_refresh_token";

// ============================================================================
// Error Classes
// ============================================================================

export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
    public data?: unknown,
    public validationErrors?: Array<{
      type: string;
      loc: Array<string | number>;
      msg: string;
      input: unknown;
    }>
  ) {
    super(detail);
    this.name = "ApiError";
  }

  static fromResponse(response: Response, data: unknown): ApiError {
    const rawDetail = (data as Record<string, unknown>)?.detail;
    let detail: string;
    let validationErrors: ApiError["validationErrors"] | undefined;

    if (Array.isArray(rawDetail)) {
      // FastAPI 422 validation error array: [{type, loc, msg, input}, ...]
      validationErrors = rawDetail as ApiError["validationErrors"];
      const messages = validationErrors.map((e) => {
        const locPath = e.loc
          .slice(1) // skip "body"
          .map((p) => String(p))
          .join(".");
        return locPath ? `${locPath}: ${e.msg}` : e.msg;
      });
      detail = messages.join("; ");
    } else if (typeof rawDetail === "string") {
      detail = rawDetail;
    } else if (rawDetail !== null && rawDetail !== undefined) {
      detail = String(rawDetail);
    } else {
      detail = `HTTP ${response.status}`;
    }

    return new ApiError(response.status, detail, data, validationErrors);
  }
}

export class AuthError extends ApiError {
  constructor(detail: string, public shouldRedirect: boolean = false) {
    super(401, detail);
    this.name = "AuthError";
  }
}

export class NetworkError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "NetworkError";
  }
}

// ============================================================================
// Token Management
// ============================================================================

function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

function setTokens(access: string, refresh: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(ACCESS_TOKEN_KEY, access);
  localStorage.setItem(REFRESH_TOKEN_KEY, refresh);
}

function clearTokens(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

function isTokenExpired(token: string): boolean {
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    return payload.exp * 1000 < Date.now();
  } catch {
    return true;
  }
}

// ============================================================================
// Core Fetch Wrapper
// ============================================================================

// Retryable HTTP status codes (transient errors that may succeed on retry).
const RETRYABLE_STATUSES = new Set([408, 429, 500, 502, 503, 504]);

// Maximum retry attempts for transient errors.
const MAX_RETRIES = 3;

// Base delay in ms for exponential backoff.
const RETRY_BASE_DELAY = 1000;

async function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function fetchWithAuth<T>(
  endpoint: string,
  options: RequestInit = {},
  retryCount = 0
): Promise<T> {
  const accessToken = getAccessToken();

  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  if (accessToken) {
    (headers as Record<string, string>)["Authorization"] = `Bearer ${accessToken}`;
  }

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${API_PREFIX}${endpoint}`, {
      ...options,
      headers,
      credentials: "omit", // JWT in header, not cookies
    });
  } catch (fetchErr) {
    // Network failure - retry with backoff if under max retries.
    if (retryCount < MAX_RETRIES) {
      const backoff = RETRY_BASE_DELAY * 2 ** retryCount;
      await sleep(backoff);
      return fetchWithAuth<T>(endpoint, options, retryCount + 1);
    }
    throw new NetworkError(
      fetchErr instanceof Error ? fetchErr.message : "Network request failed"
    );
  }

  // Handle 401 - try token refresh
  if (response.status === 401 && retryCount === 0) {
    const refreshed = await tryRefreshToken();
    if (refreshed) {
      return fetchWithAuth<T>(endpoint, options, 1);
    }
    // Refresh failed - clear tokens and throw auth error
    clearTokens();
    throw new AuthError("Session expired. Please log in again.", true);
  }

  // Retry on transient server errors (503, 429, etc.)
  if (RETRYABLE_STATUSES.has(response.status) && retryCount < MAX_RETRIES) {
    const backoff = RETRY_BASE_DELAY * 2 ** retryCount;
    await sleep(backoff);
    return fetchWithAuth<T>(endpoint, options, retryCount + 1);
  }

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw ApiError.fromResponse(response, data);
  }

  return data as T;
}

async function fetchMultipart<T>(
  endpoint: string,
  formData: FormData,
  retryCount = 0
): Promise<T> {
  const accessToken = getAccessToken();

  const headers: HeadersInit = {};
  if (accessToken) {
    headers["Authorization"] = `Bearer ${accessToken}`;
  }

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${API_PREFIX}${endpoint}`, {
      method: "POST",
      body: formData,
      headers,
      credentials: "omit",
    });
  } catch (fetchErr) {
    if (retryCount < MAX_RETRIES) {
      const backoff = RETRY_BASE_DELAY * 2 ** retryCount;
      await sleep(backoff);
      return fetchMultipart<T>(endpoint, formData, retryCount + 1);
    }
    throw new NetworkError(
      fetchErr instanceof Error ? fetchErr.message : "Network request failed"
    );
  }

  if (response.status === 401 && retryCount === 0) {
    const refreshed = await tryRefreshToken();
    if (refreshed) {
      return fetchMultipart<T>(endpoint, formData, 1);
    }
    clearTokens();
    throw new AuthError("Session expired. Please log in again.", true);
  }

  if (RETRYABLE_STATUSES.has(response.status) && retryCount < MAX_RETRIES) {
    const backoff = RETRY_BASE_DELAY * 2 ** retryCount;
    await sleep(backoff);
    return fetchMultipart<T>(endpoint, formData, retryCount + 1);
  }

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw ApiError.fromResponse(response, data);
  }

  return data as T;
}

async function tryRefreshToken(): Promise<boolean> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return false;

  try {
    const response = await fetch(`${API_BASE_URL}${API_PREFIX}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
      credentials: "omit",
    });

    if (!response.ok) return false;

    const data = (await response.json()) as TokenResponse;
    setTokens(data.access_token, data.refresh_token);
    return true;
  } catch {
    return false;
  }
}

// ============================================================================
// Public API Methods
// ============================================================================

export const api = {
  // ---------------------------------------------------------------------------
  // Auth
  // ---------------------------------------------------------------------------
  async register(data: RegisterRequest): Promise<TokenResponse> {
    const response = await fetchWithAuth<TokenResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    });
    setTokens(response.access_token, response.refresh_token);
    return response;
  },

  async login(data: LoginRequest): Promise<TokenResponse> {
    const response = await fetchWithAuth<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify(data),
    });
    setTokens(response.access_token, response.refresh_token);
    return response;
  },

  async refresh(data: RefreshRequest): Promise<TokenResponse> {
    const response = await fetchWithAuth<TokenResponse>("/auth/refresh", {
      method: "POST",
      body: JSON.stringify(data),
    });
    setTokens(response.access_token, response.refresh_token);
    return response;
  },

  async logout(data: LogoutRequest): Promise<{ message: string }> {
    const response = await fetchWithAuth<{ message: string }>("/auth/logout", {
      method: "POST",
      body: JSON.stringify(data),
    });
    clearTokens();
    return response;
  },

  async me(): Promise<MeResponse> {
    return fetchWithAuth<MeResponse>("/auth/me");
  },

  // ---------------------------------------------------------------------------
  // Business Profiles
  // ---------------------------------------------------------------------------
  async createBusiness(data: BusinessProfileCreate): Promise<BusinessProfileResponse> {
    return fetchWithAuth<BusinessProfileResponse>("/businesses/", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async listBusinesses(): Promise<BusinessProfileListResponse> {
    return fetchWithAuth<BusinessProfileListResponse>("/businesses/");
  },

  async listArchivedBusinesses(): Promise<BusinessProfileListResponse> {
    return fetchWithAuth<BusinessProfileListResponse>("/businesses/archived");
  },

  async getBusiness(id: string): Promise<BusinessProfileResponse> {
    return fetchWithAuth<BusinessProfileResponse>(`/businesses/${id}`);
  },

  async updateBusiness(id: string, data: BusinessProfileUpdate): Promise<BusinessProfileResponse> {
    return fetchWithAuth<BusinessProfileResponse>(`/businesses/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  async archiveBusiness(id: string): Promise<{ message: string }> {
    return fetchWithAuth<{ message: string }>(`/businesses/${id}`, {
      method: "DELETE",
    });
  },

  async restoreBusiness(id: string): Promise<BusinessProfileResponse> {
    return fetchWithAuth<BusinessProfileResponse>(`/businesses/${id}/restore`, {
      method: "POST",
    });
  },

  async setDefaultBusiness(id: string): Promise<BusinessProfileResponse> {
    return fetchWithAuth<BusinessProfileResponse>(`/businesses/${id}/default`, {
      method: "PATCH",
    });
  },

  // ---------------------------------------------------------------------------
  // Conversations
  // ---------------------------------------------------------------------------
  async createConversation(data: ConversationCreate): Promise<ConversationResponse> {
    return fetchWithAuth<ConversationResponse>("/conversations/", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async listConversations(skip = 0, limit = 50): Promise<ConversationResponse[]> {
    return fetchWithAuth<ConversationResponse[]>(`/conversations/?skip=${skip}&limit=${limit}`);
  },

  async getConversation(id: string): Promise<ConversationResponse> {
    return fetchWithAuth<ConversationResponse>(`/conversations/${id}`);
  },

  async updateConversation(
    id: string,
    data: Partial<ConversationCreate>
  ): Promise<ConversationResponse> {
    return fetchWithAuth<ConversationResponse>(`/conversations/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  async archiveConversation(id: string): Promise<{ message: string }> {
    return fetchWithAuth<{ message: string }>(`/conversations/${id}`, {
      method: "DELETE",
    });
  },

  async deleteConversation(id: string): Promise<{ message: string }> {
    return fetchWithAuth<{ message: string }>(`/conversations/${id}`, {
      method: "DELETE",
    });
  },

  async restoreConversation(id: string): Promise<ConversationResponse> {
    return fetchWithAuth<ConversationResponse>(`/conversations/${id}/restore`, {
      method: "POST",
    });
  },

  async getMessages(
    conversationId: string,
    limit = 50,
    offset = 0
  ): Promise<ConversationMessagesResponse> {
    return fetchWithAuth<ConversationMessagesResponse>(
      `/conversations/${conversationId}/messages?limit=${limit}&offset=${offset}`
    );
  },

  async createMessage(
    conversationId: string,
    content: string,
    intent?: string,
    messageMetadata?: Record<string, unknown>
  ): Promise<MessageResponse> {
    return fetchWithAuth<MessageResponse>(`/conversations/${conversationId}/messages`, {
      method: "POST",
      body: JSON.stringify({ content, intent, message_metadata: messageMetadata }),
    });
  },

  // ---------------------------------------------------------------------------
  // Chat
  // ---------------------------------------------------------------------------
  async sendMessage(data: ChatMessageRequest): Promise<ChatMessageResponse> {
    return fetchWithAuth<ChatMessageResponse>("/chat/message", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async getConversationStatus(conversationId: string): Promise<ConversationStatusResponse> {
    return fetchWithAuth<ConversationStatusResponse>(`/chat/conversations/${conversationId}/status`);
  },

  // ---------------------------------------------------------------------------
  // Eligibility
  // ---------------------------------------------------------------------------
  async assessEligibility(data: EligibilityAssessRequest): Promise<EligibilityAssessmentResponse> {
    return fetchWithAuth<EligibilityAssessmentResponse>("/eligibility/assess", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async getAssessment(assessmentId: string): Promise<EligibilityAssessmentResponse> {
    return fetchWithAuth<EligibilityAssessmentResponse>(`/eligibility/assessments/${assessmentId}`);
  },

  async listBusinessAssessments(businessId: string): Promise<EligibilityAssessmentResponse[]> {
    return fetchWithAuth<EligibilityAssessmentResponse[]>(`/eligibility/businesses/${businessId}/assessments`);
  },

  async getRuleSet(serviceType: string): Promise<EligibilityRuleSetResponse> {
    return fetchWithAuth<EligibilityRuleSetResponse>(`/eligibility/rule-sets/${serviceType}`);
  },

  // ---------------------------------------------------------------------------
  // Knowledge Search (Citations)
  // ---------------------------------------------------------------------------
  async searchKnowledge(data: KnowledgeSearchRequest): Promise<KnowledgeSearchResponse> {
    return fetchWithAuth<KnowledgeSearchResponse>("/knowledge/search", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  // ---------------------------------------------------------------------------
  // Roadmaps
  // ---------------------------------------------------------------------------
  async generateRoadmap(data: RoadmapGenerateRequest): Promise<RoadmapResponse> {
    return fetchWithAuth<RoadmapResponse>("/roadmaps/generate", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async listRoadmaps(businessProfileId?: string, status?: string): Promise<RoadmapListResponse> {
    const params = new URLSearchParams();
    if (businessProfileId) params.append("business_profile_id", businessProfileId);
    if (status) params.append("status", status);
    const query = params.toString() ? `?${params.toString()}` : "";
    return fetchWithAuth<RoadmapListResponse>(`/roadmaps/${query}`);
  },

  async getRoadmap(id: string): Promise<RoadmapDetailResponse> {
    return fetchWithAuth<RoadmapDetailResponse>(`/roadmaps/${id}`);
  },

  async regenerateRoadmap(id: string, data: RoadmapRegenerateRequest = {}): Promise<RoadmapResponse> {
    return fetchWithAuth<RoadmapResponse>(`/roadmaps/${id}/regenerate`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async getRoadmapProgress(id: string): Promise<RoadmapProgress> {
    return fetchWithAuth<RoadmapProgress>(`/roadmaps/${id}/progress`);
  },

  async updateTask(
    roadmapId: string,
    taskId: string,
    data: RoadmapTaskUpdate
  ): Promise<RoadmapTaskResponse> {
    return fetchWithAuth<RoadmapTaskResponse>(`/roadmaps/${roadmapId}/tasks/${taskId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  async completeTask(roadmapId: string, taskId: string): Promise<RoadmapTaskResponse> {
    return fetchWithAuth<RoadmapTaskResponse>(
      `/roadmaps/${roadmapId}/tasks/${taskId}/complete`,
      { method: "POST" }
    );
  },

  async skipTask(roadmapId: string, taskId: string): Promise<RoadmapTaskResponse> {
    return fetchWithAuth<RoadmapTaskResponse>(
      `/roadmaps/${roadmapId}/tasks/${taskId}/skip`,
      { method: "POST" }
    );
  },

  // ---------------------------------------------------------------------------
  // Workflows
  // ---------------------------------------------------------------------------
  async startWorkflow(data: WorkflowExecutionRequest): Promise<WorkflowExecutionResponse> {
    return fetchWithAuth<WorkflowExecutionResponse>("/workflows/", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async getWorkflow(workflowId: string): Promise<WorkflowExecutionResponse> {
    return fetchWithAuth<WorkflowExecutionResponse>(`/workflows/${workflowId}`);
  },

  async respondWorkflow(
    workflowId: string,
    data: ClarificationResponse
  ): Promise<WorkflowExecutionResponse> {
    return fetchWithAuth<WorkflowExecutionResponse>(`/workflows/${workflowId}/respond`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async resumeWorkflow(
    workflowId: string,
    data: ResumeWorkflowRequest = {}
  ): Promise<WorkflowExecutionResponse> {
    return fetchWithAuth<WorkflowExecutionResponse>(`/workflows/${workflowId}/resume`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async cancelWorkflow(workflowId: string): Promise<WorkflowExecutionResponse> {
    return fetchWithAuth<WorkflowExecutionResponse>(`/workflows/${workflowId}/cancel`, {
      method: "POST",
    });
  },

  async listWorkflows(): Promise<WorkflowExecutionResponse[]> {
    return fetchWithAuth<WorkflowExecutionResponse[]>("/workflows/history");
  },

  async listWorkflowTypes(): Promise<WorkflowServiceTypeResponse> {
    return fetchWithAuth<WorkflowServiceTypeResponse>("/workflows/");
  },

  // ---------------------------------------------------------------------------
  // AI / Intent (require GEMINI_ENABLED=true on backend)
  // ---------------------------------------------------------------------------
  async aiGenerate(data: AIGenerateRequest): Promise<AIGenerateResponse> {
    return fetchWithAuth<AIGenerateResponse>("/ai/generate", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async aiJson(data: AIJSONRequest): Promise<AIJSONResponse> {
    return fetchWithAuth<AIJSONResponse>("/ai/json", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async aiStructured(data: AIStructuredRequest): Promise<AIStructuredResponse> {
    return fetchWithAuth<AIStructuredResponse>("/ai/structured", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async classifyIntent(data: IntentClassifyRequest): Promise<IntentClassifyResponse> {
    return fetchWithAuth<IntentClassifyResponse>("/intent/classify", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async extractEntities(data: IntentExtractRequest): Promise<IntentExtractResponse> {
    return fetchWithAuth<IntentExtractResponse>("/intent/extract", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async analyzeIntent(data: IntentAnalyzeRequest): Promise<IntentAnalyzeResponse> {
    return fetchWithAuth<IntentAnalyzeResponse>("/intent/analyze", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async aiHealth(): Promise<AIHealthResponse> {
    return fetchWithAuth<AIHealthResponse>("/ai/health");
  },

  // ---------------------------------------------------------------------------
  // Health
  // ---------------------------------------------------------------------------
  async health(): Promise<HealthResponse> {
    return fetchWithAuth<HealthResponse>("/health");
  },

  async healthDb(): Promise<HealthDBResponse> {
    return fetchWithAuth<HealthDBResponse>("/health/db");
  },

  // ---------------------------------------------------------------------------
  // Documents
  // ---------------------------------------------------------------------------
  async uploadDocument(
    file: File,
    businessProfileId?: string
  ): Promise<DocumentUploadResponse> {
    const formData = new FormData();
    formData.append("file", file);
    const params = businessProfileId
      ? `?business_profile_id=${businessProfileId}`
      : "";
    return fetchMultipart<DocumentUploadResponse>(`/documents/upload${params}`, formData);
  },

  async listDocuments(businessProfileId?: string): Promise<DocumentListResponse> {
    const params = businessProfileId
      ? `?business_profile_id=${businessProfileId}`
      : "";
    return fetchWithAuth<DocumentListResponse>(`/documents/${params}`);
  },

  async getDocument(id: string): Promise<DocumentResponse> {
    return fetchWithAuth<DocumentResponse>(`/documents/${id}`);
  },

  async getDocumentMatching(
    id: string,
    service: string
  ): Promise<DocumentMatchingResponse> {
    return fetchWithAuth<DocumentMatchingResponse>(
      `/documents/${id}/matching?service=${service}`
    );
  },

  async deleteDocument(id: string): Promise<DocumentDeleteResponse> {
    return fetchWithAuth<DocumentDeleteResponse>(`/documents/${id}`, {
      method: "DELETE",
    });
  },

  // ---------------------------------------------------------------------------
  // Recommendations
  // ---------------------------------------------------------------------------
  async getRecommendations(
    data: RecommendationRequest
  ): Promise<RecommendationResponse> {
    return fetchWithAuth<RecommendationResponse>("/recommendations/", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async listRecommendations(
    businessProfileId?: string
  ): Promise<RecommendationListResponse> {
    const params = businessProfileId
      ? `?business_profile_id=${businessProfileId}`
      : "";
    return fetchWithAuth<RecommendationListResponse>(
      `/recommendations/${params}`
    );
  },

  async getRecommendation(
    id: string
  ): Promise<RecommendationResponse> {
    return fetchWithAuth<RecommendationResponse>(`/recommendations/${id}`);
  },

  // ---------------------------------------------------------------------------
  // Token Helpers
  // ---------------------------------------------------------------------------
  getAccessToken,
  getRefreshToken,
  setTokens,
  clearTokens,
  isTokenExpired,
  isAuthenticated: () => !!getAccessToken() && !isTokenExpired(getAccessToken()!),
};