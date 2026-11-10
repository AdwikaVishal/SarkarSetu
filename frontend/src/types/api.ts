// Frontend TypeScript types mirroring FastAPI schemas
// Source: backend/app/schemas/*.py and API_CONTRACT.md

// ============================================================================
// Base types
// ============================================================================

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
}

export interface ApiErrorValidationError {
  type: string;
  loc: Array<string | number>;
  msg: string;
  input: unknown;
}

export interface ApiError {
  detail: string | Array<ApiErrorValidationError>;
  validationErrors?: ApiErrorValidationError[];
}

// ============================================================================
// Auth
// ============================================================================

export interface RegisterRequest {
  email: string;
  full_name?: string;
  password: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RefreshRequest {
  refresh_token: string;
}

export interface LogoutRequest {
  refresh_token: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  expires_in: number;
  user?: UserResponse;
}

export interface UserResponse {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_verified: boolean;
  created_at: string; // ISO datetime
}

export interface MeResponse {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_verified: boolean;
  created_at: string; // ISO datetime
}

// ============================================================================
// Business Profiles
// ============================================================================

export type BusinessStructure =
  | "Proprietorship"
  | "Partnership"
  | "LLP"
  | "PrivateLimited"
  | "PublicLimited"
  | "OPC"
  | "Cooperative"
  | "Trust"
  | "Society"
  | "Other";

export type BusinessStage = "Idea" | "Startup" | "Growth" | "Mature" | "Scaling";

export type OperatingMode = "online" | "offline" | "both";

export interface BusinessProfileCreate {
  business_name: string;
  business_type: string;
  industry: string;
  state: string;
  district: string;
  annual_turnover?: number;
  employee_count?: number;
  sales_channels?: string[];
  business_structure: BusinessStructure;
  business_stage: BusinessStage;
  description?: string;
  city?: string;
  pincode?: string;
  udyam_number?: string;
  gstin?: string;
  website?: string;
  woman_owned?: boolean;
  social_category?: string;
  products_services?: string[];
  operating_mode?: OperatingMode;
  date_of_establishment?: string; // ISO datetime
}

export interface BusinessProfileUpdate {
  business_name?: string;
  business_type?: string;
  industry?: string;
  state?: string;
  district?: string;
  annual_turnover?: number;
  employee_count?: number;
  sales_channels?: string[];
  business_structure?: BusinessStructure;
  business_stage?: BusinessStage;
  description?: string;
  city?: string;
  pincode?: string;
  udyam_number?: string;
  gstin?: string;
  website?: string;
  woman_owned?: boolean;
  social_category?: string;
  products_services?: string[];
  operating_mode?: OperatingMode;
  date_of_establishment?: string;
}

export interface BusinessProfileResponse {
  id: string;
  user_id: string;
  business_name: string;
  business_type: string;
  industry: string;
  state: string;
  district: string;
  annual_turnover: number | null;
  employee_count: number | null;
  sales_channels: string[] | null;
  business_structure: BusinessStructure;
  business_stage: BusinessStage;
  description: string | null;
  city: string | null;
  pincode: string | null;
  udyam_number: string | null;
  gstin: string | null;
  website: string | null;
  woman_owned: boolean;
  social_category: string | null;
  products_services: string[] | null;
  operating_mode: OperatingMode | null;
  date_of_establishment: string | null;
  is_deleted: boolean;
  deleted_at: string | null;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export interface BusinessProfileListResponse {
  items: BusinessProfileResponse[];
  total: number;
}

// ============================================================================
// Chat / Conversations
// ============================================================================

export interface ChatMessageRequest {
  message: string;
  conversation_id?: string;
  business_profile_id?: string;
  idempotency_key?: string;
}

export interface IntentInfo {
  primary_intent: string;
  secondary_intents: string[];
  confidence: number;
  confidence_level: "high" | "medium" | "low";
  requires_clarification: boolean;
  clarification_question: string | null;
}

export interface ExtractedEntitySummary {
  entity_type: string;
  value: string;
  confidence: number;
  source: string;
  needs_clarification: boolean;
}

export type ResponseType = 
  | "greeting" 
  | "general_guidance" 
  | "clarification" 
  | "intent_uncertain" 
  | "workflow_not_available" 
  | "out_of_scope" 
  | "error";

export interface ChatMessageResponse {
  conversation_id: string;
  user_message_id: string;
  assistant_message_id: string;
  assistant_response: string;
  intent: IntentInfo;
  extracted_entities: ExtractedEntitySummary[];
  clarification_required: boolean;
  clarification_question: string | null;
  warnings: string[];
  response_type: ResponseType;
  conversation_status: "active" | "completed" | "archived";
  ai_model: string | null;
  provider: string | null;
  fallback_used: boolean;
  confidence: number | null;
  created_at: string;
}

export interface ConversationCreate {
  title?: string;
  business_profile_id?: string;
}

export interface ConversationResponse {
  id: string;
  user_id: string;
  business_profile_id: string | null;
  title: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface MessageResponse {
  id: string;
  conversation_id: string;
  role: "user" | "assistant";
  content: string;
  intent: string | null;
  message_metadata: Record<string, unknown> | null;
  created_at: string;
}

export interface ConversationMessagesResponse {
  items: MessageResponse[];
  total: number;
}

export interface ConversationStatusResponse {
  conversation_id: string;
  status: string;
  clarification_pending: boolean;
  clarification_question: string | null;
  business_profile_id: string | null;
  last_message_at: string | null;
}

// ============================================================================
// Eligibility
// ============================================================================

export interface EligibilityAssessRequest {
  business_profile_id: string;
  scheme_name: string;
  registration_type: string;
  business_attributes: Record<string, string>;
  missing_information?: string[];
  context?: Record<string, unknown>;
}

export interface ConditionResult {
  rule_id: string;
  description: string;
  field: string;
  operator: string;
  expected_value: unknown;
  actual_value: unknown;
  outcome: string;
  mandatory: boolean;
  source_reference: string | null;
  failure_message: string | null;
}

export type AssessmentStatus = 
  | "eligible" 
  | "ineligible" 
  | "needs_information" 
  | "potentially_eligible" 
  | "unverified";

export interface EligibilityAssessmentResponse {
  assessment_id: string;
  user_id: string;
  business_profile_id: string | null;
  rule_set_id: string;
  rule_set_version: string;
  scheme_name: string;
  registration_type: string;
  assessment_status: AssessmentStatus;
  result_data: Record<string, unknown>;
  missing_information: string[];
  condition_results: ConditionResult[];
  evidence_references: string[];
  warnings: string[];
  evaluated_at: string;
}

export interface EligibilityRuleSetResponse {
  rule_set_id: string;
  version: string;
  scheme_id: string;
  scheme_name: string;
  description: string;
  jurisdiction: string;
  issuing_authority: string;
  source_title: string | null;
  source_url: string | null;
  source_section: string | null;
  publication_date: string | null;
  effective_from: string | null;
  effective_until: string | null;
  approval_status: string;
  approved_at: string | null;
  approved_by: string | null;
  created_at: string;
  created_by: string;
  rule_count: number;
}

// ============================================================================
// Knowledge Search (Citations)
// ============================================================================

export interface KnowledgeSearchRequest {
  query: string;
  conversation_id?: string;
  filters?: Record<string, unknown>;
  limit?: number;
}

export interface RetrievalSourceResponse {
  document_id: string | null;
  source_title: string | null;
  issuing_authority: string | null;
  source_url: string | null;
  publication_date: string | null;
  relevant_excerpt: string | null;
  page_or_section: string | null;
  retrieval_score: number | null;
  document_version: string | null;
}

export interface KnowledgeSearchResponse {
  query: string;
  results: RetrievalSourceResponse[];
  total_count: number;
  provider_enabled: boolean;
}

// ============================================================================
// Roadmaps
// ============================================================================

export type TaskStatus = "pending" | "in_progress" | "completed" | "skipped" | "blocked";
export type TaskCategory = "registration" | "compliance" | "documentation" | "financial" | "operational" | "other";
export type TaskPriority = "low" | "medium" | "high" | "critical";
export type RoadmapStatus = "draft" | "active" | "completed" | "archived";

export interface RoadmapGenerateRequest {
  business_profile_id: string;
  workflow_execution_id?: string;
  service_type?: string;
  eligibility_assessment_id?: string;
  regenerate?: boolean;
}

export interface RoadmapRegenerateRequest {
  preserve_completed?: boolean;
  reason?: string;
}

export interface RoadmapTaskResponse {
  id: string;
  roadmap_id: string;
  title: string;
  description: string | null;
  category: TaskCategory;
  priority: TaskPriority;
  status: TaskStatus;
  sequence_number: number;
  dependencies: string[];
  evidence_references: string[];
  document_ids: string[];
  workflow_step_id: string | null;
  completion_criteria: string | null;
  due_date: string | null;
  official_portal_url: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface RoadmapResponse {
  id: string;
  user_id: string;
  business_profile_id: string;
  workflow_execution_id: string | null;
  service_type: string | null;
  eligibility_assessment_id: string | null;
  title: string;
  description: string | null;
  status: RoadmapStatus;
  version: number;
  total_tasks: number;
  completed_tasks: number;
  pending_tasks: number;
  blocked_tasks: number;
  progress_percentage: number;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}

export interface RoadmapListResponse {
  roadmaps: RoadmapResponse[];
  total_count: number;
}

export interface RoadmapProgress {
  roadmap_id: string;
  total_tasks: number;
  completed_tasks: number;
  pending_tasks: number;
  blocked_tasks: number;
  in_progress_tasks: number;
  progress_percentage: number;
  next_action: string | null;
  next_task_id: string | null;
  category_progress: Record<string, { total: number; completed: number; percentage: number }>;
}

export interface RoadmapDetailResponse {
  roadmap: RoadmapResponse;
  tasks: RoadmapTaskResponse[];
  progress: RoadmapProgress;
  dependency_graph: {
    task_ids: string[];
    edges: Array<{ from: string; to: string }>;
    blocked_task_ids: string[];
    ready_task_ids: string[];
    has_cycles: boolean;
    cycle_details: string[];
  };
}

export interface RoadmapTaskUpdate {
  title?: string;
  description?: string;
  category?: TaskCategory;
  priority?: TaskPriority;
  status?: TaskStatus;
  sequence_number?: number;
  due_date?: string | null;
  official_portal_url?: string | null;
  completion_criteria?: string | null;
}

// ============================================================================
// Workflows
// ============================================================================

export type WorkflowType =
  | "udyam_registration"
  | "gst_registration"
  | "msme_scheme_application"
  | "business_incorporation";

export type WorkflowStatus = "running" | "paused" | "completed" | "cancelled" | "awaiting_input";
export type StepStatus = "pending" | "running" | "completed" | "failed" | "skipped";

export interface WorkflowExecutionRequest {
  conversation_id?: string;
  service_type: WorkflowType;
  message: string;
  business_profile_id?: string;
}

export interface WorkflowStepResult {
  step_id: string;
  step_name: string;
  status: StepStatus;
  response: string;
  structured_data: Record<string, unknown>;
  missing_information: string[];
  clarification_question: string | null;
  warnings: string[];
  evidence_references: string[];
  next_step_id: string | null;
  is_final: boolean;
}

export interface WorkflowExecutionResponse {
  workflow_id: string;
  service_type: WorkflowType;
  status: WorkflowStatus;
  response: string;
  step_results: WorkflowStepResult[];
  structured_data: Record<string, unknown>;
  missing_information: string[];
  clarification_question: string | null;
  warnings: string[];
  evidence_references: string[];
  next_actions: string[];
  eligibility_assessment_id: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface ClarificationResponse {
  response: string;
}

export type ResumeWorkflowRequest = Record<string, unknown>;

export interface WorkflowServiceTypeInfo {
  service_type: WorkflowType;
  display_name: string;
  description: string;
}

export interface WorkflowServiceTypeResponse {
  service_types: WorkflowServiceTypeInfo[];
}

// ============================================================================
// AI / Intent
// ============================================================================

export interface AIGenerateRequest {
  prompt: string;
  temperature?: number;
  max_output_tokens?: number;
  system_instruction?: string;
}

export interface AIGenerateResponse {
  text: string;
  model: string;
}

export interface AIJSONRequest {
  prompt: string;
  temperature?: number;
  max_output_tokens?: number;
  system_instruction?: string;
}

export interface AIJSONResponse {
  data: Record<string, unknown>;
  model: string;
}

export interface AIStructuredRequest {
  prompt: string;
  response_schema: string;
  temperature?: number;
  max_output_tokens?: number;
  system_instruction?: string;
}

export interface AIStructuredResponse {
  data: Record<string, unknown>;
  model: string;
}

export interface IntentClassifyRequest {
  text: string;
  context?: Record<string, unknown>;
}

export interface IntentClassifyResponse {
  intent: string;
  confidence: number;
  entities: Record<string, unknown>;
}

export interface IntentExtractRequest {
  text: string;
  entity_types?: string[];
}

export interface IntentExtractResponse {
  entities: Record<string, unknown>;
}

export interface IntentAnalyzeRequest {
  text: string;
}

export interface IntentAnalyzeResponse {
  intent: string;
  confidence: number;
  entities: Record<string, unknown>;
  sentiment: "positive" | "negative" | "neutral";
  urgency: "low" | "medium" | "high";
}

export interface AIHealthResponse {
  enabled: boolean;
  model: string;
  available: boolean;
}

// ============================================================================
// Health
// ============================================================================

export interface HealthResponse {
  status: "healthy" | "unhealthy";
  version: string;
  timestamp: string;
}

export interface HealthDBResponse {
  database: "connected" | "disconnected";
  timestamp: string;
}

// ============================================================================
// Documents
// ============================================================================

export interface DocumentUploadResponse {
  document_id: string;
  filename: string;
  status: string;
  message: string;
}

export interface DocumentResponse {
  id: string;
  user_id: string;
  business_profile_id: string | null;
  original_filename: string;
  storage_key: string;
  content_type: string;
  file_size: number;
  processing_status: "pending" | "processing" | "completed" | "failed" | "error";
  document_type: string | null;
  extracted_data: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentListResponse {
  items: DocumentResponse[];
  total: number;
}

export interface MatchingDocument {
  name: string;
  category: string;
  mandatory: boolean;
  document_id?: string;
  document_type?: string;
  classification_confidence?: number;
  extracted_fields?: Record<string, unknown>;
  reason?: string;
  missing_fields?: string[];
}

export interface DocumentMatchingResponse {
  document_id: string;
  service: string;
  overall_status: string;
  checklist_coverage: number;
  available_documents: MatchingDocument[];
  missing_documents: MatchingDocument[];
  incomplete_extraction: MatchingDocument[];
  needs_review: MatchingDocument[];
  review_items: Record<string, unknown>[];
}

export interface DocumentDeleteResponse {
  message: string;
}

// ============================================================================
// Recommendations
// ============================================================================

export interface SchemeDetail {
  id: string;
  name: string;
  full_name: string;
  category: string;
  ministry: string;
  description: string;
  official_url: string;
}

export interface RecommendationDetail {
  scheme: SchemeDetail;
  eligibility_status: string;
  explanation: string;
  required_documents: string[];
  missing_information: string[];
  official_sources: Array<Record<string, string>>;
  matched_rules: string[];
  failed_rules: string[];
}

export interface RecommendationRequest {
  business_profile_id: string;
  service_filter?: string;
}

export interface RecommendationResponse {
  business_profile_id: string;
  total_schemes_evaluated: number;
  eligible_count: number;
  potentially_eligible_count: number;
  needs_info_count: number;
  ineligible_count: number;
  recommendations: RecommendationDetail[];
  missing_information: string[];
}

export interface RecommendationListResponse {
  items: RecommendationResponse[];
  total: number;
}