"""Intent taxonomy for SarkarSetu AI.

Defines the supported intent categories, entity types, confidence thresholds,
and confidence policies for intent detection and entity extraction.

All intent names and entity types are defined as enums in intent_enums.py so that
the orchestrator, frontend, and AI service all share the same vocabulary.
"""

from app.schemas.intent_enums import (
    ALL_ENTITY_TYPE_VALUES,
    ALL_INTENT_VALUES,
    ConfidenceLevel,
    EntityType,
    Intent,
    LanguageCode,
    RiskFlag,
    UrgencyLevel,
    get_confidence_level,
)

__all__ = [
    "Intent",
    "ConfidenceLevel",
    "UrgencyLevel",
    "RiskFlag",
    "EntityType",
    "LanguageCode",
    "get_confidence_level",
    "ALL_INTENT_VALUES",
    "ALL_ENTITY_TYPE_VALUES",
]
