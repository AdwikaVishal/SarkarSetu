# Shared TypeScript types for the SarkarSetu AI backend API.

Mirror of `backend/app/schemas/*`. Keep these in sync with the FastAPI
schemas. Location: `frontend/src/types/api.ts`.

export type UUID = string;

export interface UserResponse {
  id: UUID;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

export interface UserMeResponse extends UserResponse {}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: UserResponse;
}

export interface RefreshTokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface LogoutResponse {
  message: string;
}

export interface UserRegister {
  email: string;
  full_name?: string;
  password: string;
}

export interface UserLogin {
  email: string;
  password: string;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface BusinessProfileResponse {
  id: UUID;
  user_id: UUID;
  business_name: string;
  business_type: string;
  industry: string;
  state: string;
  district: string;
  annual_turnover: number | null;
  employee_count: number | null;
  sales_channels: string[];
  business_structure: string;
  business_stage: string;
  description: string | null;
  city: string | null;
  pincode: string | null;
  udyam_number: string | null;
  gstin: string | null;
  website: string | null;
  woman_owned: boolean;
  social_category: string | null;
  products_services: string[] | null;
  operating_mode: "online" | "offline" | "both" | null;
  date_of_establishment: string | null;
  is_deleted: boolean;
  deleted_at: string | null;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export interface BusinessProfileCreate {
  business_name: string;
  business_type: string;
  industry: string;
  state: string;
  district: string;
  annual_turnover?: number;
  employee_count?: number;
  sales_channels?: string[];
  business_structure: string;
  business_stage: string;
  description?: string;
  city?: string;
  pincode?: string;
  udyam_number?: string;
  gstin?: string;
  website?: string;
  woman_owned?: boolean;
  social_category?: string;
  products_services?: string[];
  operating_mode?: "online" | "offline" | "both";
  date_of_establishment?: string;
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
  business_structure?: string;
  business_stage?: string;
  description?: string;
  city?: string;
  pincode?: string;
  udyam_number?: string;
  gstin?: string;
  website?: string;
  woman_owned?: boolean;
  social_category?: string;
  products_services?: string[];
  operating_mode?: "online" | "offline" | "both";
  date_of_establishment?: string;
}

export interface ConversationResponse {
  id: UUID;
  user_id: UUID;
  title: string;
  status: string;
  business_profile_id: UUID | null;
  created_at: string;
  updated_at: string;
}

export interface ConversationCreate {
  title: string;
  business_profile_id?: UUID;
}

export interface ConversationUpdate {
  title?: string;
  status?: string;
}

export interface MessageResponse {
  id: UUID;
  conversation_id: UUID;
  role: string;
  content: string;
  intent: string | null;
  message_metadata: Record<string, unknown> | null;
  created_at: string;
}

export interface ChatMessageRequest {
  conversation_id: UUID | null;
  business_profile_id: UUID | null;
  message: string;
  idempotency_key?: string;
}

export interface ExtractedEntitySummary {
  entity_type: string;
  value: string;
  confidence: number;
  source: string;
  needs_clarification: boolean;
}

export interface IntentSummary {
  primary_intent: string;
  secondary_intents: string[];
  confidence: number;
  confidence_level: string;
  requires_clarification: boolean;
  clarification_question: string | null;
}

export enum ResponseType {
  GREETING = "greeting",
  GENERAL_GUIDANCE = "general_guidance",
  CLARIFICATION = "clarification",
  INTENT_UNCERTAIN = "intent_uncertain",
  WORKFLOW_NOT_AVAILABLE = "workflow_not_available",
  OUT_OF_SCOPE = "out_of_scope",
  ERROR = "error",
}

export interface ChatMessageResponse {
  conversation_id: UUID;
  user_message_id: UUID;
  assistant_message_id: UUID;
  assistant_response: string;
  intent: IntentSummary;
  extracted_entities: ExtractedEntitySummary[];
  clarification_required: boolean;
  clarification_question: string | null;
  warnings: string[];
  response_type: ResponseType;
  conversation_status: string;
  ai_model: string | null;
  created_at: string;
}

export interface ConversationStatusResponse {
  conversation_id: UUID;
  status: string;
  clarification_pending: boolean;
  clarification_question: string | null;
  business_profile_id: UUID | null;
  last_message_at: string | null;
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

export interface KnowledgeSearchRequest {
  query: string;
  conversation_id?: UUID;
  filters?: Record<string, unknown> | null;
  limit?: number;
}

export interface KnowledgeSearchResponse {
  query: string;
  results: RetrievalSourceResponse[];
  total_count: number;
  provider_enabled: boolean;
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

export interface EligibilityAssessmentResponse {
  assessment_id: UUID;
  user_id: UUID;
  business_profile_id: UUID | null;
  rule_set_id: string;
  rule_set_version: string | null;
  scheme_name: string | null;
  registration_type: string | null;
  assessment_status:
    | "eligible"
    | "ineligible"
    | "needs_information"
    | "potentially_eligible"
    | "unverified";
  result_data: Record<string, unknown>;
  missing_information: string[];
  condition_results: ConditionResult[];
  evidence_references: RetrievalSourceResponse[];
  warnings: string[];
  evaluated_at: string;
}

export interface EligibilityAssessmentRequest {
  user_id: UUID;
  business_profile_id: UUID | null;
  scheme_name: string | null;
  registration_type: string | null;
  business_attributes: Record<string, unknown>;
  missing_information: string[];
  context: Record<string, unknown>;
}

export interface RoadmapResponse {
  id: UUID;
  user_id: UUID;
  business_profile_id: UUID | null;
  workflow_execution_id: UUID | null;
  service_type: string;
  eligibility_assessment_id: UUID | null;
  title: string;
  description: string;
  status: "draft" | "active" | "completed" | "archived";
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

export interface RoadmapDetailResponse {
  roadmap: RoadmapResponse;
  tasks: RoadmapTaskResponse[];
  progress: {
    completed_tasks: number;
    total_tasks: number;
    progress_percentage: number;
  };
  dependency_graph: {
    task_ids: UUID[];
    edges: unknown[];
    blocked_task_ids: UUID[];
    ready_task_ids: UUID[];
    has_cycles: boolean;
    cycle_details: unknown[];
  };
}

export interface RoadmapTaskResponse {
  id: UUID;
  roadmap_id: UUID;
  title: string;
  description: string;
  category: string;
  priority: "low" | "medium" | "high" | "critical";
  status: "pending" | "in_progress" | "completed" | "blocked";
  sequence_number: number;
  dependencies: string[];
  evidence_references: unknown[];
  document_ids: UUID[];
  workflow_step_id: string | null;
  completion_criteria: string | null;
  due_date: string | null;
  official_portal_url: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface RoadmapGenerateRequest {
  business_profile_id: UUID;
  workflow_execution_id?: UUID;
  service_type: string;
  eligibility_assessment_id?: UUID;
  regenerate?: boolean;
}

export interface RoadmapTaskUpdate {
  title?: string;
  description?: string;
  sequence_number?: number;
  status?: "pending" | "in_progress" | "completed" | "blocked";
  priority?: "low" | "medium" | "high" | "critical";
  due_date?: string;
  official_portal_url?: string;
  required_documents?: string[];
  source_references?: string[];
  completed_at?: string;
}

export interface WorkflowExecutionResponse {
  workflow_id: UUID;
  service_type: string;
  status: string;
  response: string;
  step_results: Array<{
    step_id: string;
    step_name: string;
    status: string;
    response: string;
    structured_data: Record<string, unknown>;
    missing_information: string[];
    clarification_question: string | null;
    warnings: string[];
    evidence_references: RetrievalSourceResponse[];
    next_step_id: string | null;
    is_final: boolean;
  }>;
  structured_data: Record<string, unknown>;
  missing_information: string[];
  clarification_question: string | null;
  warnings: string[];
  evidence_references: RetrievalSourceResponse[];
  next_actions: string[];
  eligibility_assessment_id: UUID | null;
  completed_at: string | null;
  created_at: string;
}

export interface ClarificationResponse {
  response: string;
}
