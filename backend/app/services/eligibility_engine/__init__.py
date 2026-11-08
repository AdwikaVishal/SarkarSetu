"""Eligibility engine package for SarkarSetu AI.

Provides deterministic, auditable eligibility evaluation against
versioned, approved government rules.

Components:
- EligibilityEngine - Core engine implementing EligibilityEvaluator protocol
- RuleRegistry - Stores and retrieves versioned rule sets
- RuleEvaluator - Deterministic condition evaluation
- RuleLoader - Loads validated rule definitions
- AssessmentService - Coordinates assessment lifecycle and persistence
"""

from app.services.eligibility_engine.assessment_service import (
    EligibilityAssessmentService,
)
from app.services.eligibility_engine.engine import EligibilityEngine
from app.services.eligibility_engine.rule_evaluator import RuleEvaluator
from app.services.eligibility_engine.rule_loader import RuleLoader
from app.services.eligibility_engine.rule_registry import RuleRegistry

__all__ = [
    "EligibilityEngine",
    "EligibilityAssessmentService",
    "RuleRegistry",
    "RuleEvaluator",
    "RuleLoader",
]
