"""Schemas package - exports all Pydantic schemas."""
from app.schemas.ai import (
    AIHealthResponse,
    AIJSONRequest,
    AIJSONResponse,
    AIRequest,
    AIResponse,
    AIStructuredRequest,
    AIStructuredResponse,
    AITestRequest,
    AITestResponse,
)
from app.schemas.auth import (
    LogoutResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    TokenResponse,
    UserLogin,
    UserMeResponse,
    UserRegister,
    UserResponse,
)
from app.schemas.business import (
    BusinessProfileBase,
    BusinessProfileCreate,
    BusinessProfileListResponse,
    BusinessProfileResponse,
    BusinessProfileUpdate,
    SetDefaultBusinessProfile,
)
from app.schemas.conversation import (
    ConversationBase,
    ConversationCreate,
    ConversationResponse,
    ConversationUpdate,
    MessageCreate,
    MessageResponse,
)
from app.schemas.document import (
    UploadedDocumentBase,
    UploadedDocumentCreate,
    UploadedDocumentResponse,
    UploadedDocumentUpdate,
)
from app.schemas.eligibility import (
    EligibilityResultBase,
    EligibilityResultCreate,
    EligibilityResultResponse,
    EligibilityResultUpdate,
)
from app.schemas.message import (
    MessageBase,
    MessageUpdate,
)
from app.schemas.orchestrator import (
    AssistantResponse,
    ChatMessageRequest,
    ChatMessageResponse,
    ConversationStatusResponse,
    ExtractedEntitySummary,
    IntentSummary,
    OrchestratorError,
    ResponseType,
)
from app.schemas.recommendation import (
    RecommendationBase,
    RecommendationCreate,
    RecommendationResponse,
    RecommendationUpdate,
)
from app.schemas.roadmap import (
    RoadmapBase,
    RoadmapCreate,
    RoadmapResponse,
    RoadmapUpdate,
)
from app.schemas.task import (
    RoadmapTaskBase,
    RoadmapTaskCreate,
    RoadmapTaskResponse,
    RoadmapTaskUpdate,
)
from app.schemas.user import (
    UserBase,
    UserCreate,
    UserInDB,
    UserUpdate,
)
from app.schemas.user import (
    UserResponse as UserSchemaResponse,
)

__all__ = [
    # Auth
    "UserRegister",
    "UserLogin",
    "TokenResponse",
    "RefreshTokenRequest",
    "RefreshTokenResponse",
    "UserResponse",
    "UserMeResponse",
    "LogoutResponse",
    # AI
    "AIRequest",
    "AIResponse",
    "AIJSONRequest",
    "AIJSONResponse",
    "AIStructuredRequest",
    "AIStructuredResponse",
    "AITestRequest",
    "AITestResponse",
    "AIHealthResponse",
    # User
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserSchemaResponse",
    "UserInDB",
    # BusinessProfile
    "BusinessProfileBase",
    "BusinessProfileCreate",
    "BusinessProfileUpdate",
    "BusinessProfileResponse",
    "BusinessProfileListResponse",
    "SetDefaultBusinessProfile",
    # Conversation
    "ConversationBase",
    "ConversationCreate",
    "ConversationUpdate",
    "ConversationResponse",
    # Message
    "MessageBase",
    "MessageCreate",
    "MessageUpdate",
    "MessageResponse",
    # Recommendation
    "RecommendationBase",
    "RecommendationCreate",
    "RecommendationUpdate",
    "RecommendationResponse",
    # EligibilityResult
    "EligibilityResultBase",
    "EligibilityResultCreate",
    "EligibilityResultUpdate",
    "EligibilityResultResponse",
    # UploadedDocument
    "UploadedDocumentBase",
    "UploadedDocumentCreate",
    "UploadedDocumentUpdate",
    "UploadedDocumentResponse",
    # Roadmap
    "RoadmapBase",
    "RoadmapCreate",
    "RoadmapUpdate",
    "RoadmapResponse",
    # RoadmapTask
    "RoadmapTaskBase",
    "RoadmapTaskCreate",
    "RoadmapTaskUpdate",
    "RoadmapTaskResponse",
    # Workflow
    "WorkflowStepResult",
    "WorkflowExecutionRequest",
    "WorkflowExecutionResponse",
    "WorkflowServiceTypeInfo",
    "WorkflowServiceTypeResponse",
    "WorkflowStatus",
    "ClarificationResponse",
    "ResumeWorkflowRequest",
    "WorkflowHistoryResponse",
    "WorkflowAction",
    # Orchestrator
    "AssistantResponse",
    "ChatMessageRequest",
    "ChatMessageResponse",
    "ConversationStatusResponse",
    "ExtractedEntitySummary",
    "IntentSummary",
    "OrchestratorError",
    "ResponseType",
]
