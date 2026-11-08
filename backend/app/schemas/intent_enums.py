"""Intent enums for SarkarSetu AI.

Shared enum definitions used by both schemas and services.
"""

from enum import Enum


class Intent(str, Enum):
    """Supported intent categories for user messages."""

    # Government service discovery
    GOVERNMENT_SCHEME_DISCOVERY = "government_scheme_discovery"
    SUBSIDY_DISCOVERY = "subsidy_discovery"
    LOAN_DISCOVERY = "loan_discovery"
    REGISTRATION_DISCOVERY = "registration_discovery"

    # Registration workflows
    UDYAM_REGISTRATION = "udyam_registration"
    GST_REGISTRATION = "gst_registration"
    BUSINESS_REGISTRATION = "business_registration"

    # Eligibility and assessment
    SCHEME_ELIGIBILITY = "scheme_eligibility"
    UDYAM_ELIGIBILITY = "udyam_eligibility"
    GST_APPLICABILITY = "gst_applicability"

    # Documents and applications
    DOCUMENT_GUIDANCE = "document_guidance"
    DOCUMENT_VALIDATION = "document_validation"
    APPLICATION_GUIDANCE = "application_guidance"
    APPLICATION_STATUS = "application_status"

    # Business compliance
    COMPLIANCE_GUIDANCE = "compliance_guidance"
    TAX_GUIDANCE = "tax_guidance"
    DEADLINE_QUERY = "deadline_query"

    # Roadmap and action plans
    CREATE_ROADMAP = "create_roadmap"
    VIEW_ROADMAP = "view_roadmap"
    TASK_PROGRESS = "task_progress"

    # Business profile and documents
    BUSINESS_PROFILE_UPDATE = "business_profile_update"
    DOCUMENT_UPLOAD = "document_upload"

    # Conversation management
    GENERAL_QUESTION = "general_question"
    FOLLOW_UP = "follow_up"
    CLARIFICATION_RESPONSE = "clarification_response"
    GREETING = "greeting"
    OUT_OF_SCOPE = "out_of_scope"
    UNKNOWN = "unknown"


class ConfidenceLevel(str, Enum):
    """Confidence level categories for intent classification."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class UrgencyLevel(str, Enum):
    """Urgency levels for user requests."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class RiskFlag(str, Enum):
    """Risk flags that may be raised during intent detection."""

    HIGH_VALUE_TRANSACTION = "high_value_transaction"
    REGULATORY_RISK = "regulatory_risk"
    MISSING_CRITICAL_INFO = "missing_critical_info"
    AMBIGUOUS_REQUEST = "ambiguous_request"
    CROSS_SCHEME_CONFLICT = "cross_scheme_conflict"


class EntityType(str, Enum):
    """Entity types that can be extracted from user messages."""

    # Business entities
    BUSINESS_NAME = "business_name"
    BUSINESS_TYPE = "business_type"
    INDUSTRY = "industry"
    BUSINESS_STAGE = "business_stage"
    STATE = "state"
    DISTRICT = "district"
    CITY = "city"
    PIN_CODE = "pin_code"
    EMPLOYEE_COUNT = "employee_count"
    ANNUAL_TURNOVER = "annual_turnover"
    ESTABLISHMENT_DATE = "establishment_date"
    PRODUCTS_SERVICES = "products_services"
    OPERATING_MODE = "operating_mode"

    # Government service entities
    SCHEME_NAME = "scheme_name"
    REGISTRATION_TYPE = "registration_type"
    REGISTRATION_NUMBER = "registration_number"
    GOVERNMENT_DEPARTMENT = "government_department"
    APPLICATION_REFERENCE = "application_reference"

    # User intent entities
    REQUESTED_ACTION = "requested_action"
    REQUESTED_DEADLINE = "requested_deadline"
    REQUESTED_TIME_PERIOD = "requested_time_period"
    BUDGET = "budget"
    DOCUMENT_TYPES = "document_types"

    # Miscellaneous
    OTHER = "other"


class LanguageCode(str, Enum):
    """Supported language codes for multilingual support."""

    ENGLISH = "en"
    HINDI = "hi"
    KANNADA = "kn"
    HINGLISH = "en-hi"
    MIXED = "mixed"
    UNKNOWN = "unknown"


# Confidence thresholds for intent classification
CONFIDENCE_THRESHOLDS = {
    ConfidenceLevel.HIGH: 0.85,
    ConfidenceLevel.MEDIUM: 0.65,
    ConfidenceLevel.LOW: 0.0,
}


def get_confidence_level(score: float) -> ConfidenceLevel:
    """Determine the confidence level from a numeric score.

    Args:
        score: Confidence score between 0.0 and 1.0.

    Returns:
        The corresponding ConfidenceLevel enum value.
    """
    if score >= CONFIDENCE_THRESHOLDS[ConfidenceLevel.HIGH]:
        return ConfidenceLevel.HIGH
    elif score >= CONFIDENCE_THRESHOLDS[ConfidenceLevel.MEDIUM]:
        return ConfidenceLevel.MEDIUM
    else:
        return ConfidenceLevel.LOW


# All intent values as a set for validation
ALL_INTENT_VALUES = {intent.value for intent in Intent}

# All entity type values as a set for validation
ALL_ENTITY_TYPE_VALUES = {entity.value for entity in EntityType}
